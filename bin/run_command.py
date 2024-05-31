#!/usr/bin/env python3
"""
This script is for testing sepcific functions in SNAP strict confinenemt mode.
And it requires interface to be connected before testing.
"""
import subprocess as sp
import argparse
import logging
from inspect import getmembers, isfunction
import shlex


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)


class RunnableFunction:

    @staticmethod
    def warm_boot(args):
        cmd = 'dbus-send --system --dest=org.freedesktop.login1 --print-reply \
        /org/freedesktop/login1 org.freedesktop.login1.Manager.Reboot \
        boolean:true'
        run(cmd, args.timeout)

    @staticmethod
    def cold_boot(args):
        cmd = 'dbus-send --system --dest=org.freedesktop.login1 --print-reply \
        /org/freedesktop/login1 org.freedesktop.login1.Manager.PowerOff \
        boolean:true'
        run(cmd, args.timeout)


def run(cmd, timeout):
    logging.info(cmd)
    process = sp.run(shlex.split(cmd),
                     stdout=sp.PIPE,
                     stderr=sp.PIPE,
                     text=True,
                     timeout=timeout)
    if process.returncode != 0:
        logging.error("Return message: {}".format(process.stderr.strip()))
        raise SystemExit("Command run failed")
    else:
        return process.stdout.strip()


def main():
    func_mapping = {}
    for key, func in getmembers(RunnableFunction, isfunction):
        func_mapping[key] = func
    parser = argparse.ArgumentParser(
        description='This script is for calling subprocess for testing.')
    parser.add_argument('function',
                        help='The name of test function.',
                        choices=func_mapping)
    parser.add_argument("-a", "--argument", required=False,
                        help="The argument for the function")
    parser.add_argument("-t", "--timeout", required=False,
                        type=int,
                        default=60,
                        help="Subprocess timeout period.")
    args = parser.parse_args()

    args.timeout = 60 if not args.timeout else args.timeout
    func_mapping[args.function](args)


if __name__ == "__main__":
    main()
