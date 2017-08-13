import sys


def init(level='DEBUG'):
    """Enable Readable Logging"""
    import coloredlogs

    coloredlogs.install(
        level=level,
        level_styles={'info': {'color': 'green', 'bold': True},
                      'debug': {'color': 'magenta'},
                      'warning': {'color': 'yellow'},
                      'error': {'color': 'red'},
                      'critical': {'color': 'red', 'bold': True}
                      },
        field_styles={'programname': {'color': 'cyan'},
                      'name': {'color': 'blue'}
                      # 'levelname':    {'bold': True}
                      },
        # In more complex applications, add process and [%(name)-22s]
        fmt='%(asctime)s  [%(levelname)-5s] %(message)s')


def traced(log_attr=None):
    """
    Print Function and Method Entry w/ Parameters and Exit w/ Return Values

    Use this function as a decorator for automatic tracing, based on log level.

    Inspiration
    - Parameters (w/ defaults):
        https://stackoverflow.com/a/39643469/4560540
    - Return values:
        https://stackoverflow.com/a/32238541/4560540
    - Distinguish function and method
        https://stackoverflow.com/a/19319626/4560540
    - Alternative:
        http://pythonhosted.org/Autologging/intro.html

    """
    import functools
    import logging
    import pprint
    import inspect

    def real_decorator(decorated_function):

        @functools.wraps(decorated_function)
        def with_logging(*args, **kwargs):

            is_method = inspect.getfullargspec(decorated_function).args[0] == 'self'
            arg_index = 1 if is_method else 0

            # TODO: Catch kwargs

            if log_attr:
                logging.info("{func.__doc__} {arg}".format(
                    func=decorated_function,
                    # Searches for object variable or dict item
                    arg=getattr(args[arg_index], log_attr,
                                args[arg_index].get(log_attr)
                                if getattr(args[arg_index], 'get', False)
                                else "")
                    if len(args) > arg_index else ""
                ))
                logging.debug("{func.__name__}({args})".format(
                    func=decorated_function,
                    args=getattr(args[arg_index], log_attr,
                                 args[arg_index].get(log_attr)
                                 if getattr(args[arg_index], 'get', False)
                                 else "")
                    if len(args) > arg_index else ""))
            else:
                logging.info("{func.__doc__} {arg}".format(
                    func=decorated_function,
                    arg=args[arg_index] if len(args) > arg_index else ""))
                logging.debug("{func.__name__}{args}".format(
                    func=decorated_function,
                    args="".join(pprint.pformat(args[arg_index:], compact=True, width=240, depth=1))))

            wrapped_function = decorated_function(*args, **kwargs)
            if wrapped_function:
                logging.debug(pprint.pformat(wrapped_function, compact=True, width=120, depth=3))
            return wrapped_function

        return with_logging

    return real_decorator


from contextlib import contextmanager


@contextmanager
def ignored(*exceptions):
    """Use to Ignore Specific Exceptions


    """
    import logging
    import pprint
    try:
        yield
    except exceptions:
        logging.warning(pprint.pformat(exceptions[0]))
        pass


def handle_exception(*exc_info):
    """
    A Global Exception Handler

    Use with sys.excepthook = handle_exception,
    to catch all otherwise uncaught exceptions
    that terminate the program.

    https://stackoverflow.com/a/34106632/4560540

    """
    import logging
    import traceback

    logging.critical("".join(traceback.format_exception(*exc_info)))


sys.excepthook = handle_exception

import atexit


def exit_handler():
    import logging
    logging.info("Exit")


atexit.register(exit_handler)
