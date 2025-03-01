"""
delta demo -- command line client and tiny server
"""

import argparse
import logging
import re
import select
import socket
import sys

from delta import delta

SERVER_READ_TIMEOUT = 5
SERVER_INPUT_MAXSIZE = 1024 * 1


def set_debugger(debug=False):
    """setup debugger"""
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG if debug else logging.INFO,
        format="%(levelname)s %(module)s: %(message)s",
    )
    return logging.getLogger("delta")


def init_delta(dicts):
    """ " create delta instance and load dictionaries"""

    engine = delta.Delta()
    for dct in dicts:
        try:
            engine.load_dictionary(dct)
        except Exception as exc:  # pylint: disable=broad-except
            logging.error("failed to load dictionary: %s", exc)

    return engine


def say_to_me(engine, inline, print_in_out=True):
    """say one line"""

    say = engine.parse(inline)

    if print_in_out:
        output = f"> {inline}\n< {say}\n"
        print(output)
    else:
        print(say)


def talk_to_me(engine):
    """read lines from input and then say something back"""

    while True:

        try:
            inline = input("> ")
            inline = re.sub(r"[ \r\t\n]+", " ", inline).strip()
        except (EOFError, KeyboardInterrupt) as _:
            print()
            break

        if inline:
            say = engine.parse(inline)
            print(say, "\n")


def run_server(engine, server_params, limit=10**10):
    """
    launch simple iterative TCP server (one client connection at a time)
    and talk with someone from outside
    """

    # create socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # we need this for fast server restarting
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # bind socket to address and port
    logging.info("server is listening at: %s", server_params)
    server.bind((server_params[0], int(server_params[1])))
    server.listen(5)

    try:
        while limit > 0:
            handle_client(server, engine)
            limit -= 1
    except KeyboardInterrupt:
        logging.info("exiting by request")
    except Exception as exc:  # pylint: disable=broad-except
        logging.error("something bad happened: %s", exc)

    # close listening socket
    server.close()


def handle_client(server, engine):
    """wait for client, read input, process, reply and then exit"""

    # wait here for the client (blocking call)
    client, client_address = server.accept()
    logging.info("server got new connection: %s", client_address)

    # block again until data is posted or timeout occured
    selset = select.select([client], [], [], SERVER_READ_TIMEOUT)

    if len(selset[0]) == 0:  # nothing to read
        logging.error("socket reading timeout (%ss)", SERVER_READ_TIMEOUT)

    else:  # got something to read -- read and process

        data = client.recv(SERVER_INPUT_MAXSIZE)

        inline = data.decode("utf-8", errors="ignore")
        inline = re.sub(r"[ \r\t\n]+", " ", inline).strip()
        logging.info("> %s", inline)

        if inline:
            say = engine.parse(inline)
            client.sendall(bytes(say + "\r\n", encoding="utf-8", errors="ignore"))
            logging.info("< %s", say)

    client.close()


def main():
    """
    main function
    - parses command line arguments
    - creates delta instanse
    - starts dialog
    """

    parser = argparse.ArgumentParser(description="delta commandline interface")
    parser.add_argument("--verbose", "-v", action="store_true", default=False, help="show some stats")
    parser.add_argument("--debug", "-d", action="store_true", default=False, help="print debug info")
    parser.add_argument(
        "--allow-shell", action="store_true", default=False, help="allow delta to run SHELL and EVAL"
    )
    parser.add_argument("--say", "-s", nargs=1, metavar="YOUSAY", help="use this phrase from command line")
    parser.add_argument(
        "--tcpserver", "-t", nargs=2, metavar=("HOST", "PORT"), help="start simple TCP server"
    )
    parser.add_argument("--tcpserver-limit", type=int, default=10**10)
    parser.add_argument("dictionary", nargs="+", help="load XML dictionary")
    args = parser.parse_args()

    # set up debugging
    delta.logger = set_debugger(args.debug)
    if args.debug or args.verbose:
        delta.DEBUG = True

    delta.SHELL_ALLOWED = bool(args.allow_shell)

    # create engine and load dictionaries
    delta_engine = init_delta(args.dictionary)

    if args.tcpserver:
        # start simple TCP server
        run_server(delta_engine, args.tcpserver, args.tcpserver_limit)
    elif args.say:
        # one timer from commandline
        say_to_me(delta_engine, args.say[0], print_in_out=(args.debug or args.verbose))
    else:
        # start dialog from console
        talk_to_me(delta_engine)


if __name__ == "__main__":
    main()
