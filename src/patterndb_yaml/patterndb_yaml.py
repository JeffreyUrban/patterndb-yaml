"""Core logic for processor."""

import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, BinaryIO, Callable, Optional, TextIO, Union

import yaml

from .normalization_engine import NormalizationEngine
from .sequence_processor import SequenceProcessor


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


class PatterndbYaml:
    """
    Log normalization processor using YAML-defined pattern rules.

    Transforms heterogeneous log formats into normalized output for comparison.
    Processes input streams line-by-line with constant memory usage.
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

    @property
    def sequence_configs(self) -> dict[str, Any]:
        """Get sequence configurations for multi-line sequences."""
        return self.seq_processor.sequence_configs

    @property
    def sequence_markers(self) -> set[str]:
        """Get sequence markers for fast leader detection."""
        return self.seq_processor.sequence_markers

    def _print_explain(self, message: str) -> None:
        """Print explanation message to stderr if explain mode is enabled.

        Args:
            message: The explanation message to print
        """
        if self.explain:
            print(f"EXPLAIN: {message}", file=sys.stderr)

    def normalize_lines(self, lines: list[str]) -> list[str]:
        """
        Batch normalize lines with sequence support, no StringIO overhead.

        Processes a list of lines directly, avoiding newline addition/removal overhead.
        Supports multi-line sequences. Use this method when you have lines already
        loaded in memory. For streaming large files, use process() instead.

        Args:
            lines: List of input lines (without trailing newlines)

        Returns:
            List of normalized output lines (without trailing newlines)

        Example:
            ```python
            from pathlib import Path
            processor = PatterndbYaml(rules_path=Path("examples/rules.yaml"))
            lines = ["ERROR: Connection failed", "INFO: Retrying"]
            normalized = processor.normalize_lines(lines)
            # Returns: ['[ERROR:Connection failed]', '[INFO:Retrying]']
            ```
        """
        result: list[str] = []

        for line in lines:
            # Normalize the line
            normalized = self.norm_engine.normalize_cached(line)  # type: ignore[attr-defined]

            # Handle sequences (replicate process_line logic but with list output)
            if self.seq_processor.current_sequence:
                if self.seq_processor.is_sequence_follower(
                    line, self.seq_processor.current_sequence
                ):
                    normalized_follower = self.seq_processor.normalize_follower(
                        line, self.seq_processor.current_sequence
                    )
                    self.seq_processor.sequence_buffer.append((line, normalized_follower))
                    continue
                else:
                    # Flush buffered sequence to result list
                    result.extend(norm_line for _, norm_line in self.seq_processor.sequence_buffer)
                    self.seq_processor.sequence_buffer = []
                    self.seq_processor.current_sequence = None

            # Check if starting new sequence
            sequence_leader = self.seq_processor.is_sequence_leader(normalized)
            if sequence_leader:
                self.seq_processor.current_sequence = sequence_leader
                self.seq_processor.sequence_buffer = [(line, normalized)]
            else:
                result.append(normalized)

        # Flush any remaining sequence
        result.extend(norm_line for _, norm_line in self.seq_processor.sequence_buffer)
        self.seq_processor.sequence_buffer = []
        self.seq_processor.current_sequence = None

        return result

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
