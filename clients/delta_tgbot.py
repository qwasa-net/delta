"""
delta telegram demo bot
"""

import argparse
import concurrent.futures
import json
import logging
import os
import random
import sys
import time

import requests

from aiohttp import web
from delta import delta

TG_API_URL = "https://api.telegram.org/bot{token}/{cmd}"


def setup_logger(debug=False):
    """ setup debugger """
    logging.basicConfig(stream=sys.stderr,
                        level=logging.DEBUG if debug else logging.INFO,
                        format=("[%(asctime)-15s] %(levelname)s "
                                "[%(process)d#%(module)s.%(funcName)s]: %(message)s"))
    return logging.getLogger("delta")


class DeltaTG:
    """
    DeltaTG -- simple telegram bot interface
        + async webhook
        + sync parser (multiprocess via ProcessPoolExecutor queue)
    """

    # Note: one delta engine and one set of API keys
    # for all class instances -- in all subprocesses!
    engine = None
    token = None

    # templates for instant replies
    START_INPUT = "/start"
    START_REPLY = ["Hello, %(username)s!", "Привет, %(username)s!"]

    WORKER_SLEEP_TIME = 0

    def __init__(self, dicts, token, executor):
        self.counter = 0
        self.executor = executor
        self.init_delta(dicts)
        DeltaTG.token = token

    async def webhook(self, request):
        """
        handle incoming tg hook:
            - read the data
            - reply with instant text or call delta engine for help
        """

        self.counter += 1
        i = self.counter

        try:
            data = await request.json()
        except Exception as exc:
            logging.error("error: `%s`", exc)
            raise web.HTTPBadRequest()

        msg = data.get('message', {})
        chat_id = msg.get("chat", {}).get("id")
        msg_from = msg.get("from", {})
        from_id = msg_from.get("id")
        from_username = msg_from.get("username")
        from_name = ("%s %s" % (msg_from.get("first_name", ""), msg_from.get("last_name", "")))
        text = msg.get('text')

        logging.info("(%s) message from #%s (%s %s): `%s`",
                     i, from_id, from_username, from_name, text)

        if not chat_id or not from_id:
            raise web.HTTPBadRequest()

        # try quick reply
        reply = self.try_quick_reply(text, from_name, from_username, chat_id)

        # add a task for delta engine subprocess
        if not reply:
            self.executor.submit(DeltaTG.ask_delta, i, text, chat_id)

        return web.json_response(reply or {})

    def try_quick_reply(self, text, from_name, from_username, chat_id):
        """
        use instant reply templates for /start commands and empty texts
        """

        if (self.START_REPLY and (not text
                                  or (self.START_INPUT and text == self.START_INPUT))):
            reply_tmplt = random.choice(self.START_REPLY)
            reply = reply_tmplt % {'name': from_name, 'username': from_username}
            data = {"method": "sendMessage", "chat_id": chat_id, "text": reply[:4096]}
            logging.info("quick reply: `%s`", reply)
            return data

        return {}

    def init_delta(self, dicts):
        """" create delta instance and load dictionaries """

        logging.info("init delta (%s): %s", id(self), dicts)

        # note: static class attribute -- single instance for all
        DeltaTG.engine = delta.Delta()

        for dct in dicts:
            try:
                DeltaTG.engine.load_dictionary(dct)
            except Exception as exc:  # pylint: disable=broad-except
                logging.error("failed to load dictionary: %s", exc)

    @staticmethod
    def ask_delta(idx, text, chat_id):
        """ ask delta for answer """

        logging.info("(%s) %s> %.150s", idx, chat_id, text)

        if DeltaTG.WORKER_SLEEP_TIME:  # dev mode
            time.sleep(DeltaTG.WORKER_SLEEP_TIME)

        # call delta parser
        say = DeltaTG.engine.parse(text)

        logging.info("(%s) %s< %.150s", idx, chat_id, say)

        # post a reply to chat
        DeltaTG.send_tg_message(chat_id, say)

    @staticmethod
    def send_tg_message(chat_id, text):
        """ send a message via telegram API """

        data = {
            "chat_id": chat_id,
            "text": text[:4096],  # TG API limit
            "parse_mode": "Markdown"
        }

        headers = {
            "Content-Type": "application/json"
        }

        url = TG_API_URL.format(token=DeltaTG.token, cmd="sendMessage")

        try:
            rsp = requests.post(url=url, headers=headers, data=json.dumps(data))
            logging.info("message sent to=%s: [%s] %.80s", chat_id, rsp.status_code, rsp.text)
        except Exception as exc:  # pylint: disable=broad-except
            logging.error("failed (to=%s text=`%.40s`): %s", chat_id, text, exc)


def main():
    """
    main function
    - parses command line arguments
    - creates delta instanse
    - starts web server
    """

    parser = argparse.ArgumentParser(description='delta tg demo bot')
    parser.add_argument('--verbose', '-v', action='store_true', default=False)
    parser.add_argument('--debug', '-d', action='store_true', default=False)
    parser.add_argument('--api-token', type=str,
                        default=os.environ.get("DELTATG_API_TOKEN", ""),
                        help='Telegram HTTP API token ($DELTATG_API_TOKEN)')
    parser.add_argument('--max-workers', type=int, default=None, help="processes limit")
    parser.add_argument('--webhook-url', type=str,
                        default=os.environ.get("DELTATG_WEBHOOK_URL", "/"),
                        help="webhook path ($DELTATG_WEBHOOK_URL)")
    parser.add_argument('--workers-sleep-time', type=float, default=0.0)
    parser.add_argument('--port', '-P', type=int, default=8000)
    parser.add_argument('--host', '-H', type=str, default="127.0.0.1")
    parser.add_argument('dictionary', nargs='+', help='load XML dictionary')
    args = parser.parse_args()

    # set up debugging
    delta.logger = setup_logger(args.debug)
    if args.debug or args.verbose:
        delta.DEBUG = True

    delta.SHELL_ALLOWED = False
    DeltaTG.WORKER_SLEEP_TIME = args.workers_sleep_time

    logging.info("starting -- at %s:%s%s, with %s dicts, %s workers, using `%s…` token",
                 args.host, args.port, args.webhook_url,
                 len(args.dictionary), args.max_workers or 'few', args.api_token[:8])

    # create pool of workers
    executor = concurrent.futures.ProcessPoolExecutor(max_workers=args.max_workers)

    # create a request handler (webhook)
    handler = DeltaTG(args.dictionary, args.api_token, executor)

    # let the aiohttp magic begin!
    app = web.Application()
    app.add_routes([web.post(args.webhook_url, handler.webhook)])
    web.run_app(app, host=args.host, port=args.port, print=None)


if __name__ == "__main__":
    main()
