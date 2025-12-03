#!/usr/bin/env python3
"""
Pattern matching using syslog-ng as a persistent process.

This module provides a minimal wrapper around syslog-ng for applying
patterns.xml to input lines. It handles only the syslog-ng process
management and pattern matching, without any application-specific logic.
"""

import atexit
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional


class PatternMatcher:
    """Wrapper for persistent syslog-ng process using named pipes."""

    def __init__(self, pdb_path: Path):
        """
        Initialize persistent syslog-ng process with FIFOs.

        Args:
            pdb_path: Path to patterndb XML file
        """
        self.pdb_path = pdb_path
        self.process: Optional[subprocess.Popen[str]] = None
        self.temp_dir: Optional[str] = None
        self.input_fifo: Optional[str] = None
        self.output_fifo: Optional[str] = None
        self.config_file: Optional[str] = None
        self.input_fd: int = -1
        self.output_fd: int = -1

        self._setup()
        atexit.register(self.close)

    def _setup(self) -> None:
        """Set up temporary directory, FIFOs, config, and start syslog-ng."""
        # Create temporary directory for our FIFOs and config
        self.temp_dir = tempfile.mkdtemp(prefix="syslog-ng-filter-")

        self.input_fifo = os.path.join(self.temp_dir, "input.fifo")
        self.output_fifo = os.path.join(self.temp_dir, "output.fifo")
        self.config_file = os.path.join(self.temp_dir, "syslog-ng.conf")

        # Create FIFOs
        os.mkfifo(self.input_fifo)
        os.mkfifo(self.output_fifo)

        # Write syslog-ng configuration
        config = f"""@version: 4.3

source s_pipe {{
    pipe("{self.input_fifo}" flags(no-parse));
}};

rewrite r_set_program {{
    set("claude" value("PROGRAM"));
}};

parser p_patterns {{
    db-parser(file("{self.pdb_path}"));
}};

destination d_pipe {{
    pipe("{self.output_fifo}"
         template("${{MESSAGE}}\\n")
         flush-lines(1)
    );
}};

log {{
    source(s_pipe);
    rewrite(r_set_program);
    parser(p_patterns);
    destination(d_pipe);
}};
"""
        with open(self.config_file, "w") as f:
            f.write(config)

        # Start syslog-ng process
        # Use temp_dir for persist file to avoid permission issues
        persist_file = os.path.join(self.temp_dir, "syslog-ng.persist")
        cmd = [
            "syslog-ng",
            "-f",
            self.config_file,
            "--foreground",
            "--stderr",
            "--no-caps",  # Disable capability management (not available in containers)
            "--persist-file",
            persist_file,
        ]
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Wait for syslog-ng to start up and open the FIFOs
        # Poll with short sleeps instead of fixed 0.5s wait
        import time

        max_wait = 0.5  # Maximum time to wait (seconds)
        poll_interval = 0.01  # Check every 10ms
        elapsed = 0.0

        while elapsed < max_wait:
            # Check if process is still running
            if self.process.poll() is not None:
                stderr_output = self.process.stderr.read() if self.process.stderr else "No stderr"
                raise RuntimeError(f"syslog-ng failed to start: {stderr_output}")

            # Try to open FIFOs (non-blocking for output)
            try:
                # IMPORTANT: Open output for reading FIRST (non-blocking), then input for writing
                # Otherwise we'll deadlock
                self.output_fd = os.open(self.output_fifo, os.O_RDONLY | os.O_NONBLOCK)
                self.input_fd = os.open(self.input_fifo, os.O_WRONLY)
                break  # Success!
            except (OSError, FileNotFoundError):
                # FIFOs not ready yet, wait a bit
                time.sleep(poll_interval)
                elapsed += poll_interval
        else:
            # Timeout
            raise RuntimeError(f"Timeout waiting for syslog-ng FIFOs (waited {max_wait}s)")

    def match(self, line: str) -> str:
        """
        Match a line against patterns using persistent syslog-ng process.

        Args:
            line: Line to match

        Returns:
            Transformed MESSAGE from syslog-ng, or original line if no match
        """
        try:
            # Write line to input FIFO (with newline)
            os.write(self.input_fd, (line + "\n").encode("utf-8"))

            # Read result from output FIFO with retry logic for non-blocking I/O
            import select

            max_retries = 10
            retry_delay = 0.01  # 10ms

            for _attempt in range(max_retries):
                # Check if data is available
                ready, _, _ = select.select([self.output_fd], [], [], retry_delay)
                if ready:
                    # Read up to 64KB (should be plenty for one line)
                    result = os.read(self.output_fd, 65536).decode("utf-8").rstrip("\n")
                    if result:
                        return result
                # Data not ready yet, try again

            # Timeout - no data received, return original line
            return line

        except Exception as e:
            print(f"Error in syslog-ng match: {e}", file=sys.stderr)
            return line

    def close(self) -> None:
        """Close the syslog-ng process and clean up FIFOs."""
        try:
            if self.input_fd >= 0:
                os.close(self.input_fd)
            if self.output_fd >= 0:
                os.close(self.output_fd)
        except Exception:
            pass

        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except Exception:
                self.process.kill()

        # Clean up temp directory
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil

            shutil.rmtree(self.temp_dir, ignore_errors=True)


def main() -> None:
    """Main entry point for pattern matching filter"""
    # Get the patterns.xml path relative to this module
    module_dir = Path(__file__).parent
    pdb_path = module_dir / "patterns.xml"

    if not pdb_path.exists():
        print(f"Error: patterns.xml not found at {pdb_path}", file=sys.stderr)
        sys.exit(1)

    # Initialize pattern matcher
    matcher = PatternMatcher(pdb_path)

    try:
        # Process stdin line by line
        for line in sys.stdin:
            line = line.rstrip("\n")
            result = matcher.match(line)
            try:
                print(result)
            except BrokenPipeError:
                # Output pipe closed (e.g., piped to head), exit gracefully
                sys.stderr.close()
                break
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        pass
    finally:
        matcher.close()


if __name__ == "__main__":
    main()
