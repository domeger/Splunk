#!/usr/bin/env python
"""
Calculate and display changes in files of backup data for a single device on a
Code42 installation.
"""

# pylint: disable=import-error
import os
import sys
import argparse
import datetime
import logging
from dateutil import parser as date_parser

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))
import c42api
import argutil

LOG = c42api.get_logger(__name__)
XTERM_COLOR_END = '\033[0m'


def _byte_format(num):
    """
    Format a byte number into a human readable string (in English).

    :param num (int): A number (in bytes) to format.

    :return string: Formatted string in English localization.
    """
    for unit in ['bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB']:
        if num < 1024:
            return "%d %s" % (num, unit)
        num /= 1024.0
    return "%.1f %s" % (num, 'YB')


def _custom_output(out, events, allow_color=True):
    """
    Write custom formatted output where each line contains statically organized
    information about a file version using a variety of separators for visual
    display, interpreted primarily by humans.

    :param out (File):             The File/STDIO stream to write output.
    :param events (iterable[obj]): A list of events to iteratively write out.
    :param allow_color (bool):     Whether XTERM colors should be allowed when
                                       available.
    """

    if os.name == 'nt':
        # We currently forbid Windows from writing in color (no ANSI support).
        allow_color = False
    if out not in [sys.stdout, sys.stderr]:
        # Writing to a file (non-STDIO stream) should not be in color.
        allow_color = False

    color_start = '\033[1m'
    for event in events:
        shape = '?'
        if event['eventType'] == 'BACKUP_FILE_ACTIVITY':
            shape = '*'
            color_start = '\033[94m'
        elif event['eventType'] == 'BACKUP_FILE_DELETE':
            shape = '-'
            color_start = '\033[91m'

        if allow_color:
            out.write(color_start)

        out.write(shape)
        if out is not sys.stdout:
            # Write the deviceGuid if we are writing our custom format to disk.
            out.write(" %s" % event['deviceGuid'])
        out.write(" %s" % event['files'][0]['fullPath'])
        if event['files'][0]['MD5Hash']:
            out.write(" (%s)" % event['files'][0]['MD5Hash'])

        date = datetime.datetime.fromtimestamp(event['timestamp'] / 1000.0)
        out.write(" %s" % str(date))

        if event['files'][0]['length'] > 0:
            out.write(" %s" % _byte_format(event['files'][0]['length']))

        if allow_color:
            out.write(XTERM_COLOR_END)
        out.write("\n")


def _outline(args):
    """
    Log an outline of work that will be performed by this script for user
    confirmation.

    :param args (argparse.Namespace): Prepared arguments that will be used for
                                          parameters.
    """
    if args.output:
        LOG.info("Resolving Backup Selection Delta to " + args.output)
    else:
        LOG.info("Resolving Backup Selection Delta")
    LOG.info("Device:\t\t" + args.device)
    LOG.info("Base date:\t\t" + args.date1.isoformat())
    LOG.info("Second date:\t\t" + args.date2.isoformat())
    if ((args.hostname.startswith('https:') and args.port == 443) or
            (args.hostname.startswith('http:') and args.port == 80) or
            args.port <= 0):
        # Don't display the port if it's the default port for that protocol (443 or 80)
        LOG.info('API URL:\t\t' + args.hostname)
    else:
        LOG.info('API URL:\t\t' + args.hostname + ':' + str(args.port))
    LOG.info('Console User:\t\t' + args.username)


def _run():
    """Initializes the state for the script based on command line input."""
    arg_parser = argparse.ArgumentParser()
    args = _setup_args(arg_parser)
    if not args.device:
        raise ValueError("Device is required.")
    if args.format != 'custom' and not args.output:
        # Writing non-custom output to STDOUT, so boost the log message level.
        c42api.set_log_level(logging.ERROR)
    _outline(args)
    server = argutil.server_from_args(args)

    devices = c42api.devices(server, args.device)
    if len(devices) != 1:
        raise ValueError("*** THIS SCRIPT ONLY SUPPORTS A SINGLE DEVICE ***")

    events = c42api.calculate_delta(server, devices[0], args.date1, args.date2)
    with c42api.common.smart_open(args.output, overwrite=True) as out:
        if args.format == 'custom':
            _custom_output(out, events, allow_color=args.color)
        elif args.format == 'json':
            c42api.write_json(out, events)
        elif args.format == 'csv':
            c42api.write_csv(out, events, header=args.header)


@argutil.output_options('custom', 'csv', 'json')
@argutil.logging_options
@argutil.server_options
@argutil.devices_options
def _setup_args(arg_parser):
    """Setup args"""
    arg_parser.add_argument('date1', type=date_parser.parse,
                            help='Date for the base during delta calculation (2015-06-24).')
    arg_parser.add_argument('date2', type=date_parser.parse,
                            help='Date for the opposing delta calculation (2015-06-24).')
    arg_parser.add_argument('--no-folders', default=True, dest='folders', action='store_false',
                            help='Skips all events related to folder changes from output results.')
    arg_parser.add_argument('--no-color', default=True, dest='color', action='store_false',
                            help='''Prevent XTERM colors for custom output even when
                            available (does not apply on Windows).''')
    return arg_parser.parse_args()

if __name__ == '__main__':
    _run()
