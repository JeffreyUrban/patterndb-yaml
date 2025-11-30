"""Comprehensive tests for pattern_filter module using mocks."""

import subprocess
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from patterndb_yaml.pattern_filter import PatternMatcher, main


@pytest.fixture
def mock_pdb_file():
    """Create a temporary patterndb file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
        f.write(
            """<?xml version="1.0"?>
            <patterndb version="6" pub_date="2025-01-01">
              <ruleset name="test" id="test">
                <pattern>test</pattern>
                <rules>
                  <rule provider="test" id="test" class="test">
                    <patterns>
                      <pattern>test</pattern>
                    </patterns>
                  </rule>
                </rules>
              </ruleset>
            </patterndb>"""
        )
        pdb_path = Path(f.name)
    yield pdb_path
    pdb_path.unlink()


@pytest.mark.unit
class TestPatternMatcherInit:
    """Tests for PatternMatcher initialization."""

    @patch("builtins.open", create=True)
    @patch("atexit.register")
    @patch("time.sleep")
    @patch("os.open")
    @patch("subprocess.Popen")
    @patch("os.mkfifo")
    @patch("tempfile.mkdtemp")
    def test_successful_initialization(
        self,
        mock_mkdtemp,
        mock_mkfifo,
        mock_popen,
        mock_os_open,
        mock_sleep,
        mock_atexit,
        mock_file_open,
        mock_pdb_file,
    ):
        """Test successful PatternMatcher initialization."""
        # Setup mocks
        mock_mkdtemp.return_value = "/tmp/test-dir"
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process is running
        mock_popen.return_value = mock_process
        mock_os_open.side_effect = [100, 101]  # output_fd, input_fd

        # Create matcher
        matcher = PatternMatcher(mock_pdb_file)

        # Verify setup was called correctly
        assert matcher.temp_dir == "/tmp/test-dir"
        assert matcher.input_fifo == "/tmp/test-dir/input.fifo"
        assert matcher.output_fifo == "/tmp/test-dir/output.fifo"
        assert matcher.output_fd == 100
        assert matcher.input_fd == 101

        # Verify FIFOs were created
        assert mock_mkfifo.call_count == 2

        # Verify syslog-ng was started
        mock_popen.assert_called_once()

        # Cleanup
        with patch("os.close"), patch("shutil.rmtree"):
            matcher.close()

    @patch("builtins.open", create=True)
    @patch("atexit.register")
    @patch("time.sleep")
    @patch("subprocess.Popen")
    @patch("os.mkfifo")
    @patch("tempfile.mkdtemp")
    def test_syslogng_fails_to_start(
        self,
        mock_mkdtemp,
        mock_mkfifo,
        mock_popen,
        mock_sleep,
        mock_atexit,
        mock_file_open,
        mock_pdb_file,
    ):
        """Test handling when syslog-ng fails to start."""
        mock_mkdtemp.return_value = "/tmp/test-dir"

        # Mock process that exits immediately
        mock_process = Mock()
        mock_process.poll.return_value = 1  # Process exited
        mock_process.stderr = StringIO("Configuration error")
        mock_popen.return_value = mock_process

        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="syslog-ng failed to start"):
            PatternMatcher(mock_pdb_file)


@pytest.mark.unit
class TestPatternMatcherMatch:
    """Tests for PatternMatcher.match method."""

    @patch("builtins.open", create=True)
    @patch("select.select")
    @patch("os.read")
    @patch("os.write")
    @patch("atexit.register")
    @patch("time.sleep")
    @patch("os.open")
    @patch("subprocess.Popen")
    @patch("os.mkfifo")
    @patch("tempfile.mkdtemp")
    def test_successful_match(
        self,
        mock_mkdtemp,
        mock_mkfifo,
        mock_popen,
        mock_os_open,
        mock_sleep,
        mock_atexit,
        mock_os_write,
        mock_os_read,
        mock_select,
        mock_file_open,
        mock_pdb_file,
    ):
        """Test successful line matching."""
        # Setup mocks for initialization
        mock_mkdtemp.return_value = "/tmp/test-dir"
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process
        mock_os_open.side_effect = [100, 101]  # output_fd, input_fd

        matcher = PatternMatcher(mock_pdb_file)

        # Setup mocks for match
        mock_select.return_value = ([100], [], [])  # Data ready on first try
        mock_os_read.return_value = b"normalized output\n"

        result = matcher.match("test input line")

        # Verify line was written to input
        mock_os_write.assert_called_once_with(101, b"test input line\n")

        # Verify output was read
        mock_os_read.assert_called_once_with(100, 65536)

        assert result == "normalized output"

        with patch("os.close"), patch("shutil.rmtree"):
            matcher.close()

    @patch("builtins.open", create=True)
    @patch("select.select")
    @patch("os.read")
    @patch("os.write")
    @patch("atexit.register")
    @patch("time.sleep")
    @patch("os.open")
    @patch("subprocess.Popen")
    @patch("os.mkfifo")
    @patch("tempfile.mkdtemp")
    def test_match_timeout(
        self,
        mock_mkdtemp,
        mock_mkfifo,
        mock_popen,
        mock_os_open,
        mock_sleep,
        mock_atexit,
        mock_os_write,
        mock_os_read,
        mock_select,
        mock_file_open,
        mock_pdb_file,
    ):
        """Test match timeout (no data received after max retries)."""
        # Setup mocks for initialization
        mock_mkdtemp.return_value = "/tmp/test-dir"
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process
        mock_os_open.side_effect = [100, 101]

        matcher = PatternMatcher(mock_pdb_file)

        # Simulate data never becoming ready
        mock_select.return_value = ([], [], [])

        result = matcher.match("test input")

        # Should return original line on timeout
        assert result == "test input"
        assert mock_select.call_count == 10  # max_retries

        with patch("os.close"), patch("shutil.rmtree"):
            matcher.close()

    @patch("builtins.open", create=True)
    @patch("os.write")
    @patch("atexit.register")
    @patch("time.sleep")
    @patch("os.open")
    @patch("subprocess.Popen")
    @patch("os.mkfifo")
    @patch("tempfile.mkdtemp")
    def test_match_exception_handling(
        self,
        mock_mkdtemp,
        mock_mkfifo,
        mock_popen,
        mock_os_open,
        mock_sleep,
        mock_atexit,
        mock_os_write,
        mock_file_open,
        mock_pdb_file,
    ):
        """Test match handles exceptions gracefully."""
        # Setup mocks for initialization
        mock_mkdtemp.return_value = "/tmp/test-dir"
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process
        mock_os_open.side_effect = [100, 101]

        matcher = PatternMatcher(mock_pdb_file)

        # Simulate write error
        mock_os_write.side_effect = OSError("Broken pipe")

        result = matcher.match("test input")

        # Should return original line on error
        assert result == "test input"

        with patch("os.close"), patch("shutil.rmtree"):
            matcher.close()


@pytest.mark.unit
class TestPatternMatcherClose:
    """Tests for PatternMatcher.close method."""

    @patch("builtins.open", create=True)
    @patch("os.path.exists", return_value=True)
    @patch("os.close")
    @patch("atexit.register")
    @patch("time.sleep")
    @patch("os.open")
    @patch("subprocess.Popen")
    @patch("os.mkfifo")
    @patch("tempfile.mkdtemp")
    def test_normal_close(
        self,
        mock_mkdtemp,
        mock_mkfifo,
        mock_popen,
        mock_os_open,
        mock_sleep,
        mock_atexit,
        mock_os_close,
        mock_exists,
        mock_file_open,
        mock_pdb_file,
    ):
        """Test normal close operation."""
        # Setup mocks for initialization
        mock_mkdtemp.return_value = "/tmp/test-dir"
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_process.wait.return_value = None
        mock_popen.return_value = mock_process
        mock_os_open.side_effect = [100, 101]

        matcher = PatternMatcher(mock_pdb_file)

        # Mock shutil.rmtree for close()
        with patch("shutil.rmtree") as mock_rmtree:
            matcher.close()

            # Verify temp directory was cleaned up
            mock_rmtree.assert_called_once_with("/tmp/test-dir", ignore_errors=True)

        # Verify file descriptors were closed
        assert mock_os_close.call_count == 2

        # Verify process was terminated
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once_with(timeout=2)

    @patch("builtins.open", create=True)
    @patch("shutil.rmtree")
    @patch("os.close")
    @patch("atexit.register")
    @patch("time.sleep")
    @patch("os.open")
    @patch("subprocess.Popen")
    @patch("os.mkfifo")
    @patch("tempfile.mkdtemp")
    def test_close_with_fd_errors(
        self,
        mock_mkdtemp,
        mock_mkfifo,
        mock_popen,
        mock_os_open,
        mock_sleep,
        mock_atexit,
        mock_os_close,
        mock_rmtree,
        mock_file_open,
        mock_pdb_file,
    ):
        """Test close handles file descriptor close errors."""
        # Setup mocks for initialization
        mock_mkdtemp.return_value = "/tmp/test-dir"
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process
        mock_os_open.side_effect = [100, 101]

        matcher = PatternMatcher(mock_pdb_file)

        # Simulate close error
        mock_os_close.side_effect = OSError("Bad file descriptor")

        # Should not raise
        matcher.close()

        # Process should still be terminated
        mock_process.terminate.assert_called_once()

    @patch("builtins.open", create=True)
    @patch("shutil.rmtree")
    @patch("os.close")
    @patch("atexit.register")
    @patch("time.sleep")
    @patch("os.open")
    @patch("subprocess.Popen")
    @patch("os.mkfifo")
    @patch("tempfile.mkdtemp")
    def test_close_with_process_timeout(
        self,
        mock_mkdtemp,
        mock_mkfifo,
        mock_popen,
        mock_os_open,
        mock_sleep,
        mock_atexit,
        mock_os_close,
        mock_rmtree,
        mock_file_open,
        mock_pdb_file,
    ):
        """Test close kills process if terminate times out."""
        # Setup mocks for initialization
        mock_mkdtemp.return_value = "/tmp/test-dir"
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_process.wait.side_effect = subprocess.TimeoutExpired("syslog-ng", 2)
        mock_popen.return_value = mock_process
        mock_os_open.side_effect = [100, 101]

        matcher = PatternMatcher(mock_pdb_file)
        matcher.close()

        # Process should be killed after timeout
        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()


@pytest.mark.unit
class TestMainFunction:
    """Tests for main() function."""

    @patch("builtins.print")
    @patch("sys.stdin")
    @patch("patterndb_yaml.pattern_filter.PatternMatcher")
    @patch("pathlib.Path.exists", return_value=True)
    def test_main_processes_stdin(self, mock_exists, mock_matcher_class, mock_stdin, mock_print):
        """Test main() processes stdin line by line."""
        # Setup stdin with explicit iteration
        mock_stdin.__iter__.return_value = iter(["line 1\n", "line 2\n", "line 3\n"])

        # Setup matcher mock
        mock_matcher = Mock()
        mock_matcher.match.side_effect = lambda line: f"[normalized:{line}]"
        mock_matcher_class.return_value = mock_matcher

        # Run main
        main()

        # Verify matcher was created
        mock_matcher_class.assert_called_once()

        # Verify lines were matched
        assert mock_matcher.match.call_count == 3
        mock_matcher.match.assert_any_call("line 1")
        mock_matcher.match.assert_any_call("line 2")
        mock_matcher.match.assert_any_call("line 3")

        # Verify matcher was closed
        mock_matcher.close.assert_called_once()

        # Verify output
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("[normalized:line 1]" in str(call) for call in print_calls)

    @patch("sys.stdin")
    @patch("patterndb_yaml.pattern_filter.PatternMatcher")
    @patch("pathlib.Path.exists", return_value=True)
    def test_main_handles_keyboard_interrupt(self, mock_exists, mock_matcher_class, mock_stdin):
        """Test main() handles KeyboardInterrupt gracefully."""
        # Setup stdin with explicit iteration
        mock_stdin.__iter__.return_value = iter(["line 1\n", "line 2\n"])

        mock_matcher = Mock()
        mock_matcher.match.side_effect = KeyboardInterrupt()
        mock_matcher_class.return_value = mock_matcher

        # Should not raise
        main()

        # Matcher should be closed
        mock_matcher.close.assert_called_once()

    @patch("builtins.print", side_effect=[None, BrokenPipeError()])
    @patch("patterndb_yaml.pattern_filter.PatternMatcher")
    @patch("sys.stdin", new_callable=StringIO)
    @patch("sys.stderr.close")
    @patch("pathlib.Path.exists", return_value=True)
    def test_main_handles_broken_pipe(
        self, mock_exists, mock_stderr_close, mock_stdin, mock_matcher_class, mock_print
    ):
        """Test main() handles BrokenPipeError gracefully."""
        mock_stdin.write("line 1\nline 2\n")
        mock_stdin.seek(0)

        mock_matcher = Mock()
        mock_matcher.match.return_value = "output"
        mock_matcher_class.return_value = mock_matcher

        # Should not raise
        main()

        # stderr.close should be called
        mock_stderr_close.assert_called_once()

    @patch("builtins.print")
    @patch("pathlib.Path.exists", return_value=False)
    def test_main_missing_patterns_xml(self, mock_exists, mock_print):
        """Test main() exits if patterns.xml not found."""
        # sys.exit() should raise SystemExit
        with pytest.raises(SystemExit) as exc_info:
            main()

        # Should exit with code 1
        assert exc_info.value.code == 1

        # Should print error message
        error_calls = [call for call in mock_print.call_args_list if "Error:" in str(call)]
        assert len(error_calls) > 0
