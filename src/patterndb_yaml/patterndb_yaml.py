"""Core logic for processor."""

import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, BinaryIO, Callable, Optional, TextIO, Union, cast

import yaml

from .normalization_engine import NormalizationEngine

# Compile ANSI escape sequence regex once at module import time
ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def _match_pattern_components(
    line: str, pattern_components: list[dict[str, Any]], extract_fields: bool = False
) -> tuple[bool, dict[str, str]]:
    """
    Generic pattern matcher that walks through pattern components.

    Supports: alternatives, text, serialized, field (with parser).

    Args:
        line: Line to match against (ANSI codes will be stripped)
        pattern_components: List of component dicts from YAML pattern
        extract_fields: If True, extract and return field values

    Returns:
        Tuple of (matched: bool, fields: dict)
    """
    # Strip ANSI codes from line (use precompiled ANSI_RE)
    line_clean = ANSI_RE.sub("", line)

    pos = 0  # Current position in line_clean
    fields = {}  # Extracted field values

    for component in pattern_components:
        if pos > len(line_clean):
            return False, {}  # Ran past end of line

        if "alternatives" in component:
            # Try to match any alternative at current position
            matched = False
            for alt in component["alternatives"]:
                # Each alternative is a list of elements
                alt_text = _render_component_sequence(alt)
                if line_clean[pos:].startswith(alt_text):
                    pos += len(alt_text)
                    matched = True
                    break

            if not matched:
                return False, {}  # No alternative matched

        elif "field" in component:
            # Extract field value from current position
            field_name = component["field"]
            parser = component.get("parser")

            if parser == "NUMBER":
                # Match digits
                match = re.match(r"\d+", line_clean[pos:])
                if not match:
                    return False, {}
                if extract_fields:
                    fields[field_name] = match.group()
                pos += len(match.group())
            else:
                # Extract until end of line (ANYSTRING behavior)
                # TODO: Support delimiter inference for ESTRING behavior
                if extract_fields:
                    fields[field_name] = line_clean[pos:]
                pos = len(line_clean)

        elif "text" in component:
            # Fixed text must match exactly
            text = component["text"]
            if not line_clean[pos:].startswith(text):
                return False, {}
            pos += len(text)

        elif "serialized" in component:
            # Serialized characters must match exactly
            serialized_str = component["serialized"]
            if not line_clean[pos:].startswith(serialized_str):
                return False, {}
            pos += len(serialized_str)

    return True, fields


def _render_component_sequence(components: list[dict[str, Any]]) -> str:
    """
    Render a sequence of pattern components to their literal text.

    Args:
        components: List of component dicts (text, serialized, etc.)

    Returns:
        Concatenated text representation
    """
    result = []
    for comp in components:
        if "text" in comp:
            result.append(comp["text"])
        elif "serialized" in comp:
            result.append(comp["serialized"])
        # Fields and alternatives not supported in literal rendering
    return "".join(result)


def _load_sequence_config(rules_path: Path) -> tuple[dict[str, Any], set[str]]:
    """
    Load multi-line sequence configuration from normalization rules YAML.

    Finds rules with a 'sequence' field - these are leader patterns that
    start multi-line sequences.

    Args:
        rules_path: Path to normalization_rules.yaml

    Returns:
        Tuple of (sequence_configs dict, sequence_markers set)
        - sequence_configs: Dictionary mapping rule names to their sequence configurations
        - sequence_markers: Set of normalized output prefixes that identify sequence leaders
                           (extracted from the 'output' field, e.g., "[dialog-question:")
    """
    if not rules_path.exists():
        return {}, set()

    with open(rules_path) as f:
        data = yaml.safe_load(f)

    sequences = {}
    markers = set()

    for rule in data.get("rules", []):
        if "sequence" in rule:
            rule_name = rule["name"]
            sequences[rule_name] = rule

            output = rule.get("output", "")
            if "{" in output:
                # Extract marker from output field: "[rule-output:" portion
                # before first field placeholder
                # e.g., "[dialog-question:{content}]" -> "[dialog-question:"
                marker = output[: output.index("{")]
                markers.add(marker)
            else:
                # No field placeholder in the output
                # e.g., "[my-output]"
                markers.add(output)

    return sequences, markers


def _initialize_engine(
    rules_path: Path,
    explain: bool = False,
) -> tuple[NormalizationEngine, dict[str, Any], set[str]]:
    """
    Initialize normalization engine and load sequence configurations.

    Args:
        rules_path: Path to normalization_rules.yaml
        explain: If True, enable explain mode in the engine

    Returns:
        Tuple of (norm_engine, sequence_configs, sequence_markers)

    Raises:
        FileNotFoundError: If rules file does not exist
        RuntimeError: If normalization engine cannot be initialized
    """
    if not rules_path.exists():
        raise FileNotFoundError(f"Rules file not found: {rules_path}")

    try:
        norm_engine = NormalizationEngine(rules_path, explain=explain)

        # Provide a cached normalize callable to reduce repeated work on identical lines
        @lru_cache(maxsize=65536)
        def _normalize_cached(s: str) -> str:
            return norm_engine.normalize(s)

        # Attach for downstream use
        norm_engine.normalize_cached = _normalize_cached  # type: ignore[attr-defined]

        # Load sequence configurations
        sequence_configs, sequence_markers = _load_sequence_config(rules_path)

        return norm_engine, sequence_configs, sequence_markers

    except Exception as e:
        raise RuntimeError(f"Failed to initialize normalization engine: {e}") from e


class SequenceProcessor:
    """Handles multi-line sequence buffering and output."""

    def __init__(
        self,
        sequence_configs: dict[str, Any],
        sequence_markers: set[str],
        explain_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.sequence_configs = sequence_configs
        self.sequence_markers = sequence_markers
        self.current_sequence: Optional[str] = None  # Current sequence rule being buffered
        self.sequence_buffer: list[
            tuple[str, str]
        ] = []  # List of (raw_line, normalized_line) tuples
        self.explain_callback = explain_callback

    def _explain(self, message: str) -> None:
        """Output explanation message via callback if available."""
        if self.explain_callback:
            self.explain_callback(message)

    def flush_sequence(self, output: Union[TextIO, BinaryIO]) -> None:
        """Output buffered sequence and clear buffer."""
        if self.sequence_buffer:
            count = len(self.sequence_buffer)
            self._explain(f"Flushed sequence '{self.current_sequence}' ({count} lines buffered)")
            for _, norm_line in self.sequence_buffer:
                cast(TextIO, output).write(norm_line + "\n")
        self.sequence_buffer = []
        self.current_sequence = None

    def is_sequence_leader(self, normalized: str) -> Optional[str]:
        """Check if normalized line starts a sequence. Returns rule name if yes."""
        for marker in self.sequence_markers:
            if normalized.startswith(marker):
                # Extract rule name from marker (e.g., "[dialog-question:" -> "dialog_question")
                for rule_name in self.sequence_configs:
                    rule_output = str(self.sequence_configs[rule_name].get("output", ""))
                    if marker in rule_output:
                        return rule_name
        return None

    def is_sequence_follower(self, raw_line: str, rule_name: str) -> bool:
        """Check if raw line matches any follower pattern for the given sequence."""
        if rule_name not in self.sequence_configs:
            return False

        sequence_def = self.sequence_configs[rule_name].get("sequence", {})
        followers = sequence_def.get("followers", [])

        for follower_def in followers:
            follower_pattern = follower_def.get("pattern", [])
            matched, _ = _match_pattern_components(raw_line, follower_pattern)
            if matched:
                return True

        return False

    def process_line(self, raw_line: str, normalized: str, output: Union[TextIO, BinaryIO]) -> None:
        """
        Process and output a line (handling sequences).

        Args:
            raw_line: Raw input line
            normalized: Normalized version of the line
            output: Output stream to write to
        """
        # Check if we're currently buffering a sequence
        if self.current_sequence:
            # Check if this line is a follower
            if self.is_sequence_follower(raw_line, self.current_sequence):
                # Add to buffer and continue
                self.sequence_buffer.append((raw_line, normalized))
                buffer_count = len(self.sequence_buffer)
                self._explain(
                    f"Added follower to sequence '{self.current_sequence}' "
                    f"(buffer: {buffer_count} lines)"
                )
                return
            else:
                # Not a follower - flush the sequence first
                self._explain(f"Line is not a follower - ending sequence '{self.current_sequence}'")
                self.flush_sequence(output)

        # Check if this line starts a new sequence
        sequence_leader = self.is_sequence_leader(normalized)
        if sequence_leader:
            # Start buffering a new sequence
            self.current_sequence = sequence_leader
            self.sequence_buffer = [(raw_line, normalized)]
            self._explain(f"Started buffering sequence '{sequence_leader}' (leader line)")
        else:
            # Regular line - output immediately
            cast(TextIO, output).write(normalized + "\n")


class PatterndbYaml:
    """
    placeholder processor
    """

    def __init__(
        self,
        rules_path: Path,
        explain: bool = False,
    ):
        """
        Initialize processor.

        Args:
            rules_path: Path to normalization rules YAML file
            explain: If True, output explanations to stderr showing why lines were normalized
                    (default: False)
        """
        self.rules_path = rules_path
        self.explain = explain  # Show explanations to stderr

        # Initialize normalization engine and sequence processor (raises on failure)
        self.norm_engine, sequence_configs, sequence_markers = _initialize_engine(
            rules_path, explain=explain
        )
        # Pass explain callback to SequenceProcessor
        self.seq_processor = SequenceProcessor(
            sequence_configs,
            sequence_markers,
            explain_callback=self._print_explain if explain else None,
        )

        # Statistics
        self.lines_processed = 0
        self.lines_matched = 0

    def _print_explain(self, message: str) -> None:
        """Print explanation message to stderr if explain mode is enabled.

        Args:
            message: The explanation message to print
        """
        if self.explain:
            print(f"EXPLAIN: {message}", file=sys.stderr)

    def process(
        self,
        stream: Union[TextIO, BinaryIO],
        output: Union[TextIO, BinaryIO],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> None:
        """
        Process input stream and write to output.

        Args:
            stream: Input stream to read from
            output: Output stream to write to
            progress_callback: Optional callback for progress updates
        """
        # Process lines through normalization engine
        for line in stream:
            line = line.rstrip("\n") if isinstance(line, str) else line.decode("utf-8").rstrip("\n")
            self.lines_processed += 1

            # Update line number in normalization engine for explain output
            self.norm_engine.current_line_number = self.lines_processed

            # Normalize the line
            normalized = self.norm_engine.normalize_cached(line)  # type: ignore[attr-defined]
            if not normalized.startswith("^"):
                self.lines_matched += 1

            # Process the line (handles sequence buffering)
            self.seq_processor.process_line(line, normalized, output)

            if progress_callback:
                progress_callback(self.lines_processed, self.lines_processed - self.lines_matched)

        # Flush any remaining buffered sequence at end of input
        self.seq_processor.flush_sequence(output)

    def flush(self, output: Union[TextIO, BinaryIO]) -> None:
        """
        Flush any buffered output.

        Args:
            output: Output stream to flush to
        """
        # Flush any remaining buffered sequence
        self.seq_processor.flush_sequence(output)

    def get_stats(self) -> dict[str, Union[int, float]]:
        """
        Get normalization statistics.

        Returns:
            Dictionary with keys: lines_processed, lines_matched, match_rate
        """
        match_rate = self.lines_matched / self.lines_processed if self.lines_processed > 0 else 0.0
        return {
            "lines_processed": self.lines_processed,
            "lines_matched": self.lines_matched,
            "match_rate": match_rate,
        }
