from .bisector import *
import argparse
import os
import subprocess as sp
import shlex
import json
import logging
import sys

logger = logging.getLogger(__name__)
log_format = '%(asctime)s | %(levelname)s | %(message)s'

def load_session(sfile):
    logger.info(f"Loading session from {sfile}")
    with open(sfile) as f:
        data = json.load(f)
    logger.debug(f"Session data: {data}")
    return Bisector.from_json(data)

def save_session(b, sfile):
    logger.info(f"Saving session to {sfile}")
    data = b.to_json()
    logger.debug(f"Session data: {data}")
    with open(sfile, 'w') as f:
        json.dump(data, f, indent=4)

def print_current(b):
    print(f"[+] Current option [@index: {b.idx}]: {b.current}  ")

def create_new_bisector(options_file):
    if options_file:
        with open(options_file) as f:
            content = f.read()
    elif not sys.stdin.isatty():
        logger.info(f"No file provided, using stdin")
        content = sys.stdin.read()
    else:
        logger.error(f"No file provided with `-f`, and didn't receive any input from stdin. Exiting.")
        sys.exit(1)

    options = [line.strip() for line in content.split('\n') if line.strip()]
    return Bisector(options)



def handle_start(args):
    b = create_new_bisector(args.file)
    logger.info(f"Starting new session with {len(b.options)} options, session file: {args.session}")
    print_current(b)
    save_session(b, args.session)

def handle_run(args):
    if args.existing:
        b = load_session(args.session)
    else:
        b = create_new_bisector(args.file)

    base_cmd = args.cmd
    if not base_cmd:
        logger.error("No command provided to run, exiting.")
        sys.exit(1)

    while not b.is_done():
        logger.debug(f"Checking option [@index: {b.idx}]: {b.current}")
        cmd = shlex.join(base_cmd + [b.current])

        try:
            logger.debug(f"Running command: {cmd}")
            sp.run(cmd, shell=True, check=True)
            status = Status.GOOD

        except sp.CalledProcessError as e:
            logger.debug(f"Command failed with return code {e.returncode}")
            if e.returncode == 125:
                status = Status.SKIP
            else:
                status = Status.BAD

        logger.info(f"Setting status to {status} for option [@index: {b.idx}]: {b.current}")
        b.set_status(status)

    result, value = b.get_result()
    print(f"[+] Finished session, result: {result}, value: {value} [@index: {b.idx}]")

    if args.existing:
        save_session(b, args.session)

def handle_set_status(sfile, cmd):
    s = Status[cmd.upper()]

    b = load_session(sfile)

    if b.is_done():
        logger.warn("Session is already done finished, doing nothing. Reset with 'start' command.")
        return

    b.set_status(s)

    if b.is_done():
        result, value = b.get_result()
        print(f"[+] Finished session, result: {result}, value: {value} [@index: {b.idx}]")
    else:
        logger.info(f"Updated session with {s}")
        print_current(b)

    save_session(b, sfile)


def main():
    level = os.environ.get('LOG', 'WARN').upper()
    logging.basicConfig(format=log_format, level=level)

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--session', help='Session file to track state', type=str, default='bisect_state.json')

    subparsers = parser.add_subparsers(dest='command', help='sub-command help', required=True)

    start_parser = subparsers.add_parser('start', help='Start a new bisect session')
    start_parser.add_argument('-f', '--file', help='File containing the list of options', default=None)

    _good_parser = subparsers.add_parser('good', help='Mark the current option as good')
    _bad_parser = subparsers.add_parser('bad', help='Mark the current option as bad')
    _skip_parser = subparsers.add_parser('skip', help='Skip the current option')

    run_parser = subparsers.add_parser('run', help='Automatically run the bisect session until completion')
    run_parser.add_argument('-e', '--existing', help='Use an existing session file instead of starting a new one', action='store_true')
    run_parser.add_argument('-f', '--file', help='File containing the list of options', default=None)
    run_parser.add_argument('cmd', nargs=argparse.REMAINDER)

    args = parser.parse_args()

    if args.command == 'start':
        handle_start(args)

    elif args.command == 'run':
        handle_run(args)

    elif args.command in ('good', 'bad', 'skip'):
        handle_set_status(args.session, args.command)


if __name__ == '__main__':
    main()