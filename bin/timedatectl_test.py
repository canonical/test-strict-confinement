#!/usr/bin/env python3
"""
This Script is for test timedatectl command including
setting timezone, time and NTP
"""
import subprocess as sp
import argparse
import logging
import shlex
import re
import time
from typing import Dict


TIME_ZONE = "Time_zone"
NTP = "NTP"
LOCAL_TIME = "Local_time"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)


def timedatectl_parser() -> Dict[str, str]:
    """
    Parses from the output of timedatectl.
    Args:
    - timecmd (str, optional): The system command to run that outputs the
      time-related information. Defaults to 'timedatectl'.

    Returns:
    - Dict: The extracted information as a string based on the `parse` type.
      If the specified type is not found in the output, a RuntimeError is
      raised.

    Raises:
    - ValueError: If the `parse` argument is not one of the valid options.
    - RuntimeError: If the output of the command does not contain the expected
      information.

    Examples:
    >>> time_parser("timezone")
    'America/New_York'
    >>> time_parser("ntp")
    'enabled'
    """
    result = {
        TIME_ZONE: None,
        NTP: None,
        LOCAL_TIME: None,
    }
    output = run("timedatectl")
    timezone_search = re.search(r"Time zone:\s+(\S+)\s+\(.+\)", output)
    ntp_search = re.search(r"NTP service:\s+(\S+)", output)
    local_time_search = re.search(
        r"Local time: \S+ (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", output
    )
    if timezone_search:
        result[TIME_ZONE] = timezone_search.group(1)
    if ntp_search:
        result[NTP] = ntp_search.group(1)
    if local_time_search:
        result[LOCAL_TIME] = local_time_search.group(1)
    for key, value in result.items():
        if value is None:
            raise SystemExit("Not able to get time date information!")
    return result


def timedatectl_set(func: str, arg: str) -> None:
    """
    Execute timedatectl command with parameter.

    Parameters:
    - func (str): timedatectl parameter to run.
                  e.g. "set-time", "set-timezone", "set-ntp" ...etc
    - arg (str): The argument to run.
                  e.g. {True|False} for set-ntp
    Example:
    >>> time_set("set-ntp", "true")
    equal to command: timedatectl set-ntp true
    """
    cmd = 'timedatectl {} "{}"'.format(func, arg)
    run(cmd)


def run(cmd: str, timeout: int = 60) -> str:
    """
    Execute a shell command with a specified timeout.

    Parameters:
    - cmd (str): Command to be executed.
    - timeout (int, optional): Maximum time in seconds for the command to run.
      Defaults to 60 seconds.

    Returns:
    - str: Standard output from the executed command.

    Raises:
    - TimeoutExpired: If the command does not complete within the timeout.
    - CalledProcessError: If the command exits with a non-zero status.
    """
    try:
        process = sp.run(
            shlex.split(cmd),
            stdout=sp.PIPE,
            stderr=sp.PIPE,
            text=True,
            timeout=timeout,
        )
        process.check_returncode()  # Check for non-zero exit code
        return process.stdout.strip()
    except sp.TimeoutExpired:
        logging.error("Command '%s' timed out after %s seconds", cmd, timeout)
        raise SystemExit("Command timed out")
    except sp.CalledProcessError as e:
        logging.error(
            "Command '%s' failed with return code %d", cmd, e.returncode
        )
        logging.error("Error message: %s", e.stderr)
        raise SystemExit("Command failed with a non-zero exit code")
    except FileNotFoundError:
        logging.error("Command '%s' not found", cmd)
        raise SystemExit("Command not found")
    except Exception as e:
        logging.error("An unexpected error occurred: %s", e)
        raise SystemExit("An unexpected error occurred")


def toggle_ntp(status: bool) -> None:
    """
    Toggles the Network Time Protocol (NTP) service on or off based on the
    input parameter.

    This function attempts to enable or disable the NTP service on the system
    depending on the boolean value passed to the 'status' parameter.
    It logs the operation's success or failure and checks to confirm that the
    desired state is achieved.

    Args:
    - status (bool): If True, enable the NTP service; if False, disable it.
      The function sets the NTP service to 'active' if True is passed, and
       'inactive' if False is passed.

    Returns:
    - None: This function does not return any value. It logs the outcome of
      the operation instead.

    Raises:
    - SystemExit: If the command to toggle the NTP service fails for any
      reason, including execution errors from the underlying system command.

    Examples:
    >>> toggle_ntp(True)  # Attempts to enable the NTP service
    >>> toggle_ntp(False) # Attempts to disable the NTP service

    Notes:
    - The function uses the 'time_set' function to send the command to the
      system, which must be implemented to handle the 'set-ntp' command
      correctly.
    - It also uses the 'time_parser' function to verify the NTP state after
      attempting to toggle it.
      The 'time_parser' function should be capable of interpreting 'ntp'
      output from the system's status command to ensure correct verification.
    """
    expect_status = "active" if status else "inactive"
    logging.info("Attempting to toggle NTP service %s", expect_status)
    timedatectl_set("set-ntp", status)
    # Verify the state change
    if timedatectl_parser()[NTP] == expect_status:
        logging.info("Toggle NTP successed!")
    else:
        logging.error("Failed to toggle NTP service status.")
        raise SystemExit(1)


def set_timezone(timezone: str) -> None:
    """
    Test if timezone can be setup.
    """
    logging.info("Attempting to set timezone to %s", timezone)
    timedatectl_set("set-timezone", timezone)
    current_timezone = timedatectl_parser()[TIME_ZONE]
    logging.info("Current timezone is %s", current_timezone)
    if current_timezone != timezone:
        raise SystemExit("Timezone setup failed!")
    logging.info("Timezone setup succeed!")


def test_timezone(target_timezone):
    """
    This function intends to test if the system is able to set
    timezone and restore it.
    """
    # Giving default list for test timezone to prevent target_timezone
    # is the same as system timezone.
    timezone_list = ["UTC", "Asia/Taipei"]
    if target_timezone not in timezone_list:
        timezone_list.append(target_timezone)
    logging.info("Start to test timezone setting up")
    with TimeZoneRestore() as tzr:
        if tzr.restore_timezone in timezone_list:
            timezone_list.remove(tzr.restore_timezone)
        set_timezone(timezone_list[-1])


def test_ntp():
    mock_date = "2024-02-29 11:11:11"
    with NtpRestore():
        logging.info("Attempting to set date to a mockup date %s", mock_date)
        timedatectl_set("set-time", mock_date)
        current_date = timedatectl_parser()[LOCAL_TIME]
        logging.info("Current date is %s", current_date)
        # Check if current date has been set to mock_date
        if current_date != mock_date:
            logging.error("Set date failed!!")
            raise SystemExit(1)
        logging.info(
            "Attempting to toggle NTP to active and check if"
            " system time sync up with NTP."
        )
        toggle_ntp(True)
        logging.info("Waiting for 5 seconds to sync time from NTP server.")
        time.sleep(5)
        current_date = timedatectl_parser()[LOCAL_TIME]
        logging.info("Current date is %s", current_date)
        # Check if current date is not the same as mock_date
        if current_date != mock_date:
            logging.info("Date is sync up with NTP server!")
        else:
            logging.error("Date is not sync up with NTP server!")
            raise SystemExit(1)


class TimeZoneRestore:
    def __init__(self):
        self.restore_timezone = None

    def __enter__(self):
        self.restore_timezone = timedatectl_parser()[TIME_ZONE]
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        logging.info(
            "Restoring original timezone to %s", self.restore_timezone
        )
        set_timezone(self.restore_timezone)
        if exc_type:
            logging.error("An error occurred: %s", exc_value)
            return False


class NtpRestore:
    def __init__(self):
        self.restore_ntp = None

    def __enter__(self):
        self.restore_ntp = timedatectl_parser()[NTP]
        if self.restore_ntp == "active":
            toggle_ntp(False)

    def __exit__(self, exc_type, exc_value, traceback):
        logging.info("Restoring original NTP to %s", self.restore_ntp)
        if self.restore_ntp == "active":
            toggle_ntp(True)
        else:
            toggle_ntp(False)
        if exc_type:
            logging.error("An error occurred: %s", exc_value)
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Test system configuration tasks"
    )
    subparsers = parser.add_subparsers(
        dest="test", required=True, help="Test functions in timezone and ntp"
    )
    timezone_subparser = subparsers.add_parser(
        "timezone", help="Run timezone test"
    )
    timezone_subparser.add_argument(
        "-t",
        "--target",
        type=str,
        default="Asia/Taipei",
        help="Target timezone to test.",
    )
    subparsers.add_parser("ntp", help="Run NTP test")
    args = parser.parse_args()
    if args.test == "timezone":
        test_timezone(args.target)
    elif args.test == "ntp":
        test_ntp()


if __name__ == "__main__":
    main()
