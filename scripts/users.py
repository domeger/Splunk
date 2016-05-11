#!/usr/bin/env python
#
# Copyright (c) 2015 - 2016 Code42 Software, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
A script for fetching and printing every user on a Code42 installation in
either csv or json format.
"""

# pylint: disable=import-error
import os
import sys
import logging
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))
import c42api
import argutil


def _run():
    """Initializes the state for the script based on command line input."""
    arg_parser = argparse.ArgumentParser()
    args = _setup_args(arg_parser)
    if args.logfile:
        c42api.set_log_file(args.logfile)

    if args.output or args.logfile:
        c42api.set_log_level(logging.DEBUG)
    else:
        c42api.set_log_level(logging.ERROR)
    server = argutil.server_from_args(args)
    is_json = args.format == 'json'
    with c42api.common.smart_open(args.output, overwrite=True) as out:
        if is_json:
            c42api.write_json(out, c42api.fetch_users(server))
        else:
            c42api.write_csv(out, c42api.fetch_users(server), args.header, shallow=True)


@argutil.output_options('json', 'csv')
@argutil.logging_options
@argutil.server_options
def _setup_args(arg_parser):
    """
    Add all available arguments to an argparse.ArgumentParser object for the
    users script.

    The decorators outside the function take care of most of the work. See
    their definitions in arg_decorators.py for more info.

    :param arg_parser: An argparse.ArgumentParser object to add args to.
    :return:           The argparse.ArgumentParser object with arguments
                       added to it.
    """
    return arg_parser.parse_args()


if __name__ == '__main__':
    _run()
