"""Sequence processing for multi-line pattern matching.

This module handles buffering and normalization of multi-line sequences,
where a leader line is followed by multiple follower lines that should be
grouped and output together.
"""

from typing import Any, BinaryIO, Callable, Optional, TextIO, Union, cast

from .pattern_matching import match_pattern_components


class SequenceProcessor:
    """Handles multi-line sequence buffering and output."""

    def __init__(
        self,
        sequence_configs: dict[str, Any],
        sequence_markers: set[str],
        explain_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        """
        Initialize sequence processor.

        Args:
            sequence_configs: Dictionary of sequence rule configurations
            sequence_markers: Set of output markers that identify sequence leaders
            explain_callback: Optional callback for explanation messages
        """
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
            matched, _ = match_pattern_components(raw_line, follower_pattern)
            if matched:
                return True

        return False

    def normalize_follower(self, raw_line: str, rule_name: str) -> str:
        """
        Normalize a follower line according to its pattern and output template.

        Args:
            raw_line: Raw follower line to normalize
            rule_name: Name of the sequence rule this follower belongs to

        Returns:
            Normalized follower line, or raw line if no pattern matches
        """
        if rule_name not in self.sequence_configs:
            return raw_line

        sequence_def = self.sequence_configs[rule_name].get("sequence", {})
        followers = sequence_def.get("followers", [])

        # Try each follower pattern
        for follower_def in followers:
            follower_pattern = follower_def.get("pattern", [])
            matched, fields = match_pattern_components(
                raw_line, follower_pattern, extract_fields=True
            )

            if matched:
                # Get output template for this follower
                output_template = follower_def.get("output", "")

                if not output_template:
                    # No output template - return raw line
                    return raw_line

                # Format output using extracted fields
                try:
                    formatted_output: str = output_template.format(**fields)
                    self._explain(f"Normalized follower using pattern: {formatted_output}")
                    return formatted_output
                except KeyError as e:
                    # Template references missing field
                    self._explain(f"Follower template error - missing field {e}")
                    return raw_line

        # No pattern matched
        return raw_line

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
                # Normalize the follower according to its pattern
                normalized_follower = self.normalize_follower(raw_line, self.current_sequence)
                # Add to buffer and continue
                self.sequence_buffer.append((raw_line, normalized_follower))
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
