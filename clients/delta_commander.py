"""
delta demo -- command line client
"""
import argparse
import logging
import sys

from delta import delta


def set_debugger(debug=False):
    """ setup debugger """
    logging.basicConfig(stream=sys.stderr,
                        level=logging.DEBUG if debug else logging.INFO,
                        format="%(levelname)s %(module)s: %(message)s")
    return logging.getLogger("delta")


def init_delta(dicts):
    """" creates delta instance and loads dictionaries """

    engine = delta.Delta()
    for dct in dicts:
        try:
            engine.load_dictionary(dct)
        except Exception as exc:  # pylint: disable=broad-except
            logging.error("failed to load dictionary: %s", exc)

    return engine


def say_to_me(engine, inline, print_in_out=True):
    """ say one line """

    say = engine.parse(inline)

    if print_in_out:
        output = "> {}\n< {}\n".format(inline, say)
        print(output)
    else:
        print(say)


def talk_to_me(engine):
    """ read lines from input and then say something """

    while True:

        try:
            inline = input("> ")
        except (EOFError, KeyboardInterrupt) as _:
            print()
            break

        if inline:
            say = engine.parse(inline)
            print(say, "\n")


def main():
    """
    main function
    - parses command line arguments
    - creates delta instanse
    - starts dialog
    """

    parser = argparse.ArgumentParser(description='delta commandline interface')
    parser.add_argument('--verbose', '-v', action='store_true', default=False,
                        help="show some stats")
    parser.add_argument('--debug', '-d', action='store_true', default=False,
                        help="print debug info")
    parser.add_argument('--allow-shell', action='store_true', default=False,
                        help="allow delta to run SHELL and EVAL")
    parser.add_argument('--say', '-s', nargs='?',
                        help='use this phrase from command line')
    parser.add_argument('dictionary', nargs='+',
                        help='load XML dictionary')
    args = parser.parse_args()

    # set up debugging
    delta.logger = set_debugger(args.debug)
    if args.debug or args.verbose:
        delta.DEBUG = True

    delta.SHELL_ALLOWED = bool(args.allow_shell)

    # create engine and load dictionaries
    delta_engine = init_delta(args.dictionary)

    if args.say:  # one timer
        say_to_me(delta_engine, args.say, print_in_out=(args.debug or args.verbose))
    else:  # start dialog
        talk_to_me(delta_engine)


if __name__ == "__main__":
    main()
