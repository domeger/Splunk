"""Decorators to add commonly used args to an argument parser"""

# pylint: disable=import-error
import getpass

import c42api


# decorator
def output_options(*args):
    """
    The decorator that adds format options.

    The args are the possible format options that will be added to the help
    parameter for the format arg. The first one in
    """
    default = args[0]
    display_args = ["'" + arg + "'" for arg in args]
    display_args[-1] = 'and ' + display_args[-1]
    joiner = ', ' if len(display_args) > 2 else ' '
    phrase = joiner.join(display_args)

    def real_decorator(func):
        """The decorator that will be applied to the function"""
        def wrapper_func(arg_parser):
            """The wrapper function the csv and json decorator returns"""
            arg_parser.add_argument("-f", "--output-format", dest="format", type=lambda s: s.lower(), default=default,
                                    help="An optional output format. Supports {}. Defaults to '{}'.".
                                    format(phrase, default))
            arg_parser.add_argument("-o", "--output", dest="output", default=None,
                                    help="An optional output file. Defaults writing to STDOUT.")
            if 'csv' in args:
                arg_parser.add_argument("-H", "--header", dest="header", action="store_true",
                                        help="Include header when outputting to a CSV document.")
            return func(arg_parser)

        return wrapper_func

    return real_decorator


# decorator
def server_options(func):
    """The decorator that adds server options"""
    def wrapper_func(arg_parser):
        """The wrapper function the server decorator returns"""
        arg_parser.add_argument('-s', dest='hostname',
                                help='Code42 Console URL (without port)')
        arg_parser.add_argument('-u', dest='username', default='admin',
                                help='Code42 Console Username')
        arg_parser.add_argument('-port', dest='port', type=int, default=4285,
                                help='Code42 Console Port')
        arg_parser.add_argument('--no-verify', dest='verify_ssl', action='store_false',
                                default=True, help='Disable SSL certificate verification when making HTTPS requests.')
        arg_parser.add_argument('-p', dest='password', default='',
                                help='Code42 Console password (replaces prompt)')
        return func(arg_parser)
    return wrapper_func


def server_from_args(args):
    """
    Initialize c42api.common.Server object from arguments object.

    :param args: The script arguments to interpret.

    :return Server: Server object corresponding to the args.

    :raise ValueError: Server hostname not specified in args.
    """
    if not args.hostname:
        raise ValueError("Server hostname is required.")

    password = args.password
    if not password:
        password = getpass.getpass("Code42 Console Password [" + args.username + "]: ")

    server = c42api.Server(args.hostname, port=args.port, username=args.username, password=password,
                           verify_ssl=args.verify_ssl)

    return server


# decorator
def logging_options(func):
    """The decorator that adds logging options"""
    def wrapper_func(arg_parser):
        """The wrapper function the logging decorator returns"""
        arg_parser.add_argument('-log', dest='logfile', default=None,
                                help='Logfile to print informational output messages (instead of STDOUT)')
        return func(arg_parser)
    return wrapper_func


# decorator
def devices_options(func):
    """The decorator that adds device options"""
    def wrapper_func(arg_parser):
        """The wrapper function the date range decorator returns"""
        arg_parser.add_argument('-d', '--device', dest='device',
                                help='Devices to use for query')
        return func(arg_parser)
    return wrapper_func
