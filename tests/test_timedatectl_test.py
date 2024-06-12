import unittest
from unittest.mock import patch, MagicMock
from timedatectl_test import (
    timedatectl_parser,
    timedatectl_set,
    toggle_ntp,
    set_timezone,
    run,
    TIME_ZONE,
    NTP,
    LOCAL_TIME,
)


class TestTimeDateCtl(unittest.TestCase):
    @patch("timedatectl_test.run")
    def test_timedatectl_parser(self, mock_run):
        mock_run.return_value = """
            Local time: 二 2024-06-11 11:28:42 CST
            Universal time: 二 2024-06-11 03:28:42 UTC
            RTC time: 二 2024-06-11 03:28:42
            Time zone: Asia/Taipei (CST, +0800)
            System clock synchronized: yes
            NTP service: active
            RTC in local TZ: no
        """
        expected = {
            TIME_ZONE: "Asia/Taipei",
            NTP: "active",
            LOCAL_TIME: "2024-06-11",
        }
        result = timedatectl_parser()
        self.assertEqual(result, expected)

    @patch("timedatectl_test.run")
    def test_timedatectl_set(self, mock_run):
        timedatectl_set("set-timezone", "UTC")
        mock_run.assert_called_with("timedatectl set-timezone UTC")

    @patch("timedatectl_test.timedatectl_set")
    @patch("timedatectl_test.timedatectl_parser")
    def test_toggle_ntp_enable_success(
        self, mock_timedatectl_parser, mock_timedatectl_set
    ):
        mock_timedatectl_parser.return_value = {"NTP": "active"}

        # Call the function with status True to enable NTP
        toggle_ntp(True)

        # Check if the timedatectl_set function was called with the
        # correct parameters
        mock_timedatectl_set.assert_called_with("set-ntp", True)

        # Check if the parser was called to verify the state
        mock_timedatectl_parser.assert_called_once()

    @patch("timedatectl_test.timedatectl_set")
    @patch("timedatectl_test.timedatectl_parser")
    def test_toggle_ntp_disable_success(
        self, mock_timedatectl_parser, mock_timedatectl_set
    ):
        mock_timedatectl_parser.return_value = {"NTP": "inactive"}

        # Call the function with status False to disable NTP
        toggle_ntp(False)

        # Check if the timedatectl_set function was called with the
        # correct parameters
        mock_timedatectl_set.assert_called_with("set-ntp", False)

        # Check if the parser was called to verify the state
        mock_timedatectl_parser.assert_called_once()

    @patch("timedatectl_test.timedatectl_set")
    @patch("timedatectl_test.timedatectl_parser")
    def test_toggle_ntp_enable_failure(
        self, mock_timedatectl_parser, mock_timedatectl_set
    ):
        mock_timedatectl_parser.return_value = {"NTP": "inactive"}

        with self.assertRaises(SystemExit):
            toggle_ntp(True)

        # Check if the timedatectl_set function was called with the
        # correct parameters
        mock_timedatectl_set.assert_called_with("set-ntp", True)

        # Check if the parser was called to verify the state
        mock_timedatectl_parser.assert_called_once()

    @patch("timedatectl_test.timedatectl_set")
    @patch("timedatectl_test.timedatectl_parser")
    def test_toggle_ntp_disable_failure(
        self, mock_timedatectl_parser, mock_timedatectl_set
    ):
        mock_timedatectl_parser.return_value = {"NTP": "active"}

        with self.assertRaises(SystemExit):
            toggle_ntp(False)

        # Check if the timedatectl_set function was called with the
        # correct parameters
        mock_timedatectl_set.assert_called_with("set-ntp", False)

        # Check if the parser was called to verify the state
        mock_timedatectl_parser.assert_called_once()

    @patch("timedatectl_test.timedatectl_set", side_effect=SystemError)
    def test_toggle_ntp_set_command_failure(self, mock_timedatectl_set):
        with self.assertRaises(SystemExit):
            toggle_ntp(True)

        # Check if the timedatectl_set function was called and
        # raised SystemError
        mock_timedatectl_set.assert_called_with("set-ntp", True)

    @patch("timedatectl_test.timedatectl_set")
    @patch("timedatectl_test.timedatectl_parser")
    def test_set_timezone_success(
        self, mock_timedatectl_parser, mock_timedatectl_set
    ):
        # Mock the return value of timedatectl_parser to match the
        # desired timezone
        mock_timedatectl_parser.return_value = {
            "Time_zone": "America/New_York"
        }
        mock_timedatectl_set.retrun_value = True
        # Call the function with the desired timezone
        set_timezone("America/New_York")

        # Check if the timedatectl_set function was called with the
        # correct parameters
        mock_timedatectl_set.assert_called_with(
            "set-timezone", "America/New_York"
        )

        # Check if the parser was called to verify the state
        mock_timedatectl_parser.assert_called_once()

    @patch("timedatectl_test.timedatectl_set")
    @patch("timedatectl_test.timedatectl_parser")
    def test_set_timezone_failure(
        self, mock_timedatectl_parser, mock_timedatectl_set
    ):
        # Mock the return value of timedatectl_parser to not match the
        # desired timezone
        mock_timedatectl_parser.return_value = {
            "Time_zone": "America/Los_Angeles"
        }

        with self.assertRaises(SystemExit):
            set_timezone("America/New_York")

        # Check if the timedatectl_set function was called with the
        # correct parameters
        mock_timedatectl_set.assert_called_with(
            "set-timezone", "America/New_York"
        )

        # Check if the parser was called to verify the state
        mock_timedatectl_parser.assert_called_once()

    @patch(
        "timedatectl_test.timedatectl_set",
        side_effect=SystemError("Failed to set timezone"),
    )
    def test_set_timezone_command_failure(self, mock_timedatectl_set):
        with self.assertRaises(SystemExit):
            set_timezone("America/New_York")

        # Check if the timedatectl_set function was called and
        # raised SystemError
        mock_timedatectl_set.assert_called_with(
            "set-timezone", "America/New_York"
        )

    @patch("timedatectl_test.shlex.split")
    @patch("timedatectl_test.sp.run")
    def test_run_success(self, mock_run, mock_split):
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "success"
        mock_run.return_value = mock_process
        result = run("timedatectl status")
        self.assertEqual(result, "success")

    @patch("timedatectl_test.shlex.split")
    @patch("timedatectl_test.sp.run")
    def test_run_failure(self, mock_run, mock_split):
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stderr = "error"
        mock_run.return_value = mock_process
        with self.assertRaises(SystemError):
            run("timedatectl status")


if __name__ == "__main__":
    unittest.main()
