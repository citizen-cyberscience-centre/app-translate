import argparse
import logging
import os
import sys


# http://code.activestate.com/recipes/52308/
# http://github.com/dsc/bunch
class Bunch:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)


def default_parser(doc):

    parser = argparse.ArgumentParser(
        description=doc,
        #epilog=epilog,
        # RawDescriptionHelpFormatter preserves epilog line breaks but
        # does not show default values. Discussed at
        # http://goo.gl/490yc
        # http://bugs.python.org/issue12806
        formatter_class=argparse.RawDescriptionHelpFormatter,
        #formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        #usage=usage,
        )

    # Application options.
    logargs = parser.add_argument_group('Application')
    logargs.add_argument('--explore',
                         help="Explore data in stragic spots.",
                         action="store_true")
    logargs.add_argument('--numcores',
                         help="Number of cores in multicore sow/reap run.",
                         action="store",
                         type=int,
                         default=1)
    logargs.add_argument('--corenum',
                         help="Core number in multicore run.",
                         action="store",
                         type=int,
                         default=-1)

    # Boilerplate logging options.
    logargs = parser.add_argument_group('Logging')
    logargs.add_argument('--nolog',
                         help="Disable console (and all) logging.",
                         action="store_true")
    logargs.add_argument('--loglevel',
                         help="Console log level (DEBUG, WARNING, etc.).",
                         action="store",
                         default='INFO')
    logargs.add_argument('--flog',
                         help="Enable file logging.",
                         action="store_true")
    logargs.add_argument('--floglevel',
                         help="File log level (DEBUG, WARNING, etc.).",
                         action="store",
                         default='INFO')
    logargs.add_argument('--quiet',
                         help="Disable all logging (same as --nolog).",
                         action="store_true")
    logargs.add_argument('--verbose',
                         help="Same as '--loglevel DEBUG'.",
                         action="store_true")
    parser.add_argument('--colorlog',
                        help="Use crazy logging ColorFormatter.",
                        action="store_true")

    parser.add_argument('--qc',
                        help="Quiet and colorlog.",
                        action="store_true")
    parser.add_argument('--vc',
                        help="Verbose and colorlog.",
                        action="store_true")


    # Boilerplate useful options.
    logargs = parser.add_argument_group('Misc.')
    logargs.add_argument('--doit',
                         help="Do it!",
                         action="store_true")
    logargs.add_argument('--test',
                         help="Enable testing.",
                         action="store_true")
    logargs.add_argument('--offline',
                         help="Enable offline features.",
                         action="store_true")


    # Example of choices, int.
    # parser.add_argument('--shuffle', '-s', 
    #                     help="Run analysis on shuffled data.",
    #                     action="store",
    #                     type=int,
    #                     choices=(0, 1, 2, 3, 4),
    #                     default=0)

    return parser


def set_logging(logger=None, args=None):
    """Set handlers and formatters for root logger defined at top of this file.

    Logger handlers, formatters and filters should be set here at this
    application (executable script) level.

    Libraries, etc. that are imported and that make use of logging
    should have at the least a NullHandler set up like so:

    import logging
    logger = logging.getLogger(__name__)
    # Needed if module imported from elsewhere before root logger set up.
    logger.addHandler(logging.NullHandler())

    That way, they simply pass logging messages to the root logger
    defined here and it is the responsibility of this root logger to
    decide what and how to send where.

    Logging option combinations:

    bin/play.py --colorlog --loglevel ERROR --floglevel DEBUG
    bin/play.py --nolog
    bin/play.py --nolog
    """

    if logger is None:
        logger = logging.getLogger(__name__)

    if args is None:
        args = Bunch(quiet=False,
                     verbose=False,
                     nolog=False,
                     flog=False,
                     colorlog=False,
                     loglevel = 'INFO')

    if isinstance(args, logging.Logger):
        # Backwards compatibility.
        logger, args = args, logger

    if args.qc:
        args.quiet = args.colorlog = True
    elif args.vc:
        args.verbose = args.colorlog = True

    if args.quiet:
        #args.nolog = True
        args.nolog = False
        args.loglevel = 'CRITICAL'  # Want to see something.
    elif args.verbose:
        # Note that quiet trumps verbose.
        args.nolog = False
        args.loglevel = 'DEBUG'

    # Turn off all logging.
    if args.nolog:
        logger.disabled = True
        return

    # Let logger take everything but handlers can filter with
    # --loglevel and --floglevel.
    logger.setLevel(logging.DEBUG)

    # How log messages are displayed in different handlers.
    fmt = "%(levelname)s: %(funcName)s-%(lineno)d %(message)s"

    # Set up a file logger first so as not to give it ColorFormatter.
    if args.flog:

        # Override default --log for file logger.
        numeric_level = getattr(logging, args.floglevel.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid flog level: %s' % args.floglevel)

        fh = logging.FileHandler('%s.log' % sys.argv[0], mode='w')  # or 'a'
        file_formatter = logging.Formatter("%(asctime)s " + fmt)
        fh.setLevel(level=numeric_level)
        fh.setFormatter(file_formatter)
        logger.addHandler(fh)

    # Default console handler.
    numeric_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % args.loglevel)

    ch = logging.StreamHandler()
    console_formatter = logging.Formatter(fmt)
    ch.setLevel(level=numeric_level)
    if args.colorlog:
        try:
            # Ryan special sauce hack. Write me if you want it.
            from erpy.erpy_logging import ColorFormatter
            console_formatter = ColorFormatter()
        except:  # ImportError:
            pass
    ch.setFormatter(console_formatter)
    logger.addHandler(ch)

    logger.debug("%d handler(s)." % len(logger.handlers))
    assert len(logger.handlers) > 0
