import unittest
from unittest.mock import patch, MagicMock
import subprocess as sp
import timedatectl_test  # assuming your script is named timedatectl_test.py


class TestTimedatectlFunctions(unittest.TestCase):
    def setUp(self):
        self.mock_output_initial = """
            Local time: Tue 2024-06-17 12:34:56 UTC
            Universal time: Tue 2024-06-17 12:34:56 UTC
            RTC time: Tue 2024-06-17 12:34:56
            Time zone: America/New_York (EDT, -0400)
            System clock synchronized: yes
            NTP service: active
        """
        self.mock_output_mismatch = """
            Local time:
            Time zone:
            NTP service:
        """
        self.mock_output_toggled = """
            Local time: Tue 2024-06-17 12:34:56 UTC
            Universal time: Tue 2024-06-17 12:34:56 UTC
            RTC time: Tue 2024-06-17 12:34:56
            Time zone: America/New_York (EDT, -0400)
            System clock synchronized: yes
            NTP service: inactive
        """
        self.mock_timezone = "Asia/Taipei"
        self.mock_ntp_status = "active"

    @patch("timedatectl_test.run")
    def test_timedatectl_parser_success(self, mock_run):
        mock_run.return_value = self.mock_output_initial
        result = timedatectl_test.timedatectl_parser()
        self.assertEqual(
            result[timedatectl_test.TIME_ZONE], "America/New_York"
        )
        self.assertEqual(result[timedatectl_test.NTP], "active")
        self.assertEqual(
            result[timedatectl_test.LOCAL_TIME], "2024-06-17 12:34:56"
        )

    @patch("timedatectl_test.run")
    def test_timedatectl_parser_fail(self, mock_run):
        mock_run.return_value = self.mock_output_mismatch

        with self.assertRaises(SystemError) as cm:
            timedatectl_test.timedatectl_parser()

        self.assertEqual(str(cm.exception),
                         "Not able to get time date information!")

    @patch("timedatectl_test.run")
    def test_timedatectl_set(self, mock_run):
        timedatectl_test.timedatectl_set("set-timezone", self.mock_timezone)
        mock_run.assert_called_with('timedatectl set-timezone "Asia/Taipei"')

    @patch("timedatectl_test.sp.run")
    def test_run_success(self, mock_run):
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "command output"
        mock_run.return_value = mock_process

        result = timedatectl_test.run("echo 'hello'")
        self.assertEqual(result, "command output")
        mock_run.assert_called_once_with(
            ["echo", "hello"],
            stdout=sp.PIPE,
            stderr=sp.PIPE,
            text=True,
            timeout=60,
        )

    @patch("timedatectl_test.sp.run")
    def test_run_timeout(self, mock_run):
        mock_run.side_effect = sp.TimeoutExpired(
            cmd="echo 'hello'", timeout=60
        )

        with self.assertRaises(SystemExit) as cm:
            timedatectl_test.run("echo 'hello'")
        self.assertEqual(cm.exception.code, "Command timed out")
        mock_run.assert_called_once_with(
            ["echo", "hello"],
            stdout=sp.PIPE,
            stderr=sp.PIPE,
            text=True,
            timeout=60,
        )

    @patch("timedatectl_test.sp.run")
    def test_run_called_process_error(self, mock_run):
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stderr = "error message"
        mock_run.side_effect = sp.CalledProcessError(
            returncode=1, cmd="echo 'hello'", stderr="error message"
        )

        with self.assertRaises(SystemExit) as cm:
            timedatectl_test.run("echo 'hello'")
        self.assertEqual(
            cm.exception.code, "Command failed with a non-zero exit code"
        )
        mock_run.assert_called_once_with(
            ["echo", "hello"],
            stdout=sp.PIPE,
            stderr=sp.PIPE,
            text=True,
            timeout=60,
        )

    @patch("timedatectl_test.sp.run")
    def test_run_file_not_found_error(self, mock_run):
        mock_run.side_effect = FileNotFoundError()

        with self.assertRaises(SystemExit) as cm:
            timedatectl_test.run("nonexistent-command")
        self.assertEqual(cm.exception.code, "Command not found")
        mock_run.assert_called_once_with(
            ["nonexistent-command"],
            stdout=sp.PIPE,
            stderr=sp.PIPE,
            text=True,
            timeout=60,
        )

    @patch("timedatectl_test.sp.run")
    def test_run_unexpected_error(self, mock_run):
        mock_run.side_effect = Exception("Unexpected error")

        with self.assertRaises(SystemExit) as cm:
            timedatectl_test.run("echo 'hello'")
        self.assertEqual(cm.exception.code, "An unexpected error occurred")
        mock_run.assert_called_once_with(
            ["echo", "hello"],
            stdout=sp.PIPE,
            stderr=sp.PIPE,
            text=True,
            timeout=60,
        )

    @patch("timedatectl_test.timedatectl_set")
    @patch("timedatectl_test.timedatectl_parser")
    def test_set_timezone_success(
        self, mock_timedatectl_parser, mock_timedatectl_set
    ):
        mock_timedatectl_parser.return_value = {
            timedatectl_test.TIME_ZONE: "Asia/Taipei"
        }

        # Call the function to be tested
        timedatectl_test.set_timezone("Asia/Taipei")

        # Assertions to ensure the correct behavior
        mock_timedatectl_set.assert_called_with("set-timezone", "Asia/Taipei")
        mock_timedatectl_parser.assert_called_once()

    @patch("timedatectl_test.timedatectl_set")
    @patch("timedatectl_test.timedatectl_parser")
    def test_set_timezone_fail(
        self, mock_timedatectl_parser, mock_timedatectl_set
    ):
        mock_timedatectl_parser.return_value = {
            timedatectl_test.TIME_ZONE: "America/New_York"
        }

        # Ensure the function handles exceptions correctly
        with self.assertRaises(SystemError):
            timedatectl_test.set_timezone("Asia/Taipei")

        # Assertions to ensure the correct behavior
        mock_timedatectl_set.assert_called_with("set-timezone", "Asia/Taipei")
        mock_timedatectl_parser.assert_called_once()

    @patch("timedatectl_test.run")
    def test_toggle_ntp(self, mock_run):
        mock_run.side_effect = [
            self.mock_output_initial,
            self.mock_output_toggled,
            self.mock_output_toggled,
        ]
        timedatectl_test.toggle_ntp(False)
        self.assertEqual(
            timedatectl_test.timedatectl_parser()[timedatectl_test.NTP],
            "inactive",
        )

    @patch("timedatectl_test.run")
    def test_toggle_ntp_enable(self, mock_run):
        mock_run.side_effect = [
            self.mock_output_toggled,
            self.mock_output_initial,
            self.mock_output_initial,
        ]
        timedatectl_test.toggle_ntp(True)
        self.assertEqual(
            timedatectl_test.timedatectl_parser()[timedatectl_test.NTP],
            "active",
        )

    @patch("timedatectl_test.time.sleep", return_value=None)
    @patch("timedatectl_test.toggle_ntp")
    @patch("timedatectl_test.timedatectl_parser")
    @patch("timedatectl_test.timedatectl_set")
    @patch("timedatectl_test.NtpRestore")
    def test_test_ntp_success(
        self,
        mock_ntprestore,
        mock_timedatectl_set,
        mock_timedatectl_parser,
        mock_toggle_ntp,
        mock_sleep,
    ):
        mock_ntprestore.return_value.__enter__.return_value = None
        mock_ntprestore.return_value.__exit__.return_value = None

        mock_timedatectl_parser.side_effect = [
            {timedatectl_test.LOCAL_TIME: "2024-02-29 11:11:11"},
            {timedatectl_test.LOCAL_TIME: "2024-06-17 12:34:56"},
        ]

        timedatectl_test.test_ntp()

        mock_timedatectl_set.assert_called_with(
            "set-time", "2024-02-29 11:11:11"
        )
        mock_toggle_ntp.assert_called_with(True)
        self.assertTrue(mock_sleep.called)
        self.assertEqual(mock_timedatectl_parser.call_count, 2)

    @patch("timedatectl_test.timedatectl_parser")
    @patch("timedatectl_test.timedatectl_set")
    @patch("timedatectl_test.NtpRestore")
    def test_test_ntp_fail_set_time(
        self,
        mock_ntprestore,
        mock_timedatectl_set,
        mock_timedatectl_parser,
    ):
        mock_ntprestore.return_value.__enter__.return_value = None
        mock_ntprestore.return_value.__exit__.return_value = None

        mock_timedatectl_parser.return_value = {
            timedatectl_test.LOCAL_TIME: "2024-06-17 12:34:56"
        }

        with self.assertRaises(SystemExit):
            timedatectl_test.test_ntp()

        mock_timedatectl_set.assert_called_with(
            "set-time", "2024-02-29 11:11:11"
        )
        self.assertEqual(mock_timedatectl_parser.call_count, 1)

    @patch("timedatectl_test.time.sleep", return_value=None)
    @patch("timedatectl_test.toggle_ntp")
    @patch("timedatectl_test.timedatectl_parser")
    @patch("timedatectl_test.timedatectl_set")
    @patch("timedatectl_test.NtpRestore")
    def test_test_ntp_fail_ntp_sync(
        self,
        mock_ntprestore,
        mock_timedatectl_set,
        mock_timedatectl_parser,
        mock_toggle_ntp,
        mock_sleep,
    ):
        mock_ntprestore.return_value.__enter__.return_value = None
        mock_ntprestore.return_value.__exit__.return_value = None

        mock_timedatectl_parser.side_effect = [
            {timedatectl_test.LOCAL_TIME: "2024-02-29 11:11:11"},
            {timedatectl_test.LOCAL_TIME: "2024-02-29 11:11:11"},
        ]

        with self.assertRaises(SystemExit):
            timedatectl_test.test_ntp()

        mock_timedatectl_set.assert_called_with(
            "set-time", "2024-02-29 11:11:11"
        )
        mock_toggle_ntp.assert_called_with(True)
        self.assertTrue(mock_sleep.called)
        self.assertEqual(mock_timedatectl_parser.call_count, 2)

    @patch("timedatectl_test.set_timezone")
    @patch("timedatectl_test.TimeZoneRestore")
    def test_test_timezone_success_target_timezone(
        self, mock_timezonerestore, mock_set_timezone
    ):
        # Mock the TimeZoneRestore class
        mock_restore = MagicMock()
        mock_restore.restore_timezone = "America/New_York"
        mock_timezonerestore.return_value.__enter__.return_value = mock_restore

        # Call the function to be tested
        timedatectl_test.test_timezone("Asia/Taipei")

        # Assertions to ensure the correct behavior
        mock_set_timezone.assert_any_call("Asia/Taipei")

    @patch("timedatectl_test.set_timezone")
    @patch("timedatectl_test.TimeZoneRestore")
    def test_test_timezone_success_default_timezone(
        self, mock_timezonerestore, mock_set_timezone
    ):
        # Mock the TimeZoneRestore class
        mock_restore = MagicMock()
        mock_restore.restore_timezone = "Asia/Taipei"
        mock_timezonerestore.return_value.__enter__.return_value = mock_restore

        # Call the function to be tested
        timedatectl_test.test_timezone("Asia/Taipei")

        # Assertions to ensure the correct behavior
        mock_set_timezone.assert_any_call("UTC")

    @patch("timedatectl_test.timedatectl_parser")
    @patch("timedatectl_test.set_timezone")
    def test_timezone_restore_success(
        self, mock_set_timezone, mock_timedatectl_parser
    ):
        mock_timedatectl_parser.return_value = {
            timedatectl_test.TIME_ZONE: "America/New_York"
        }

        with timedatectl_test.TimeZoneRestore():
            pass

        mock_set_timezone.assert_called_once_with("America/New_York")

    @patch("timedatectl_test.timedatectl_parser")
    @patch("timedatectl_test.set_timezone")
    def test_timezone_restore_on_exception(
        self, mock_set_timezone, mock_timedatectl_parser
    ):
        # Mock the parser return value to simulate the timezone
        mock_timedatectl_parser.return_value = {
            timedatectl_test.TIME_ZONE: "America/New_York"
        }

        with self.assertLogs("", level="ERROR") as cm:
            try:
                with timedatectl_test.TimeZoneRestore():
                    raise ValueError("Test exception")
            except ValueError:
                pass

        # Check that the log contains the expected error message
        self.assertTrue(
            any(
                "An error occurred: Test exception" in message
                for message in cm.output
            )
        )

        # Check that set_timezone was called to restore the original timezone
        mock_set_timezone.assert_called_once_with("America/New_York")

    @patch("timedatectl_test.timedatectl_parser")
    @patch("timedatectl_test.toggle_ntp")
    def test_ntp_restore_active(
        self, mock_toggle_ntp, mock_timedatectl_parser
    ):
        mock_timedatectl_parser.return_value = {timedatectl_test.NTP: "active"}

        with timedatectl_test.NtpRestore():
            mock_toggle_ntp.assert_called_with(False)

        mock_toggle_ntp.assert_any_call(True)

    @patch("timedatectl_test.timedatectl_parser")
    @patch("timedatectl_test.toggle_ntp")
    def test_ntp_restore_inactive(
        self, mock_toggle_ntp, mock_timedatectl_parser
    ):
        mock_timedatectl_parser.return_value = {
            timedatectl_test.NTP: "inactive"
        }

        with timedatectl_test.NtpRestore():
            mock_toggle_ntp.assert_not_called()

        mock_toggle_ntp.assert_any_call(False)

    @patch("timedatectl_test.timedatectl_parser")
    @patch("timedatectl_test.toggle_ntp")
    def test_ntp_restore_with_exception(
        self, mock_toggle_ntp, mock_timedatectl_parser
    ):
        # Mock the parser return value to simulate the timezone
        mock_timedatectl_parser.return_value = {timedatectl_test.NTP: "active"}

        # Mock the logging raise a ERROR level log.
        with self.assertLogs("", level="ERROR") as cm:
            try:
                with timedatectl_test.NtpRestore():
                    raise ValueError("Test exception")
            except ValueError:
                pass
        # Check that the log contains the expected error message
        self.assertTrue(
            any(
                "An error occurred: Test exception" in message
                for message in cm.output
            )
        )

        # Check that set_timezone was called to restore the original timezone
        mock_toggle_ntp.assert_any_call(True)


if __name__ == "__main__":
    unittest.main()
