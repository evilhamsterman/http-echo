#!/usr/bin/env python3

# 2022, Georg Sauthoff
# 2023, Daniel Mills

import argparse
import http.server
import json
import signal
import sys
from http import HTTPStatus
from textwrap import dedent
from typing import Any
from urllib.parse import parse_qs


class Dumper(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        print(self.__print_req())
        self.send_response(HTTPStatus.OK)
        self.end_headers()

    def do_DELETE(self):
        return self.do_GET()

    def do_POST(self):
        n = int(self.headers.get("content-length", 0))
        body = self.rfile.read(n)
        print(self.__print_req())
        if self.headers.get("content-type") == "application/json":
            print("JSON data:")
            try:
                pprint(json.loads(body))
            except json.decoder.JSONDecodeError:
                print(f"Invalid JSON\n{body}")
        elif self.headers.get("content-type") == "application/x-www-form-urlencoded":
            print("Form data:")
            try:
                pprint(parse_qs(body.decode(), strict_parsing=True))
            except ValueError:
                print(f"Invalid form data\n{body}")
        else:
            print(body)
        self.send_response(HTTPStatus.OK)
        self.end_headers()

    def do_PUT(self):
        return self.do_POST()

    def log_message(self, format, *args):
        pass

    def __print_req(self):
        msg = dedent(
            f"""\n
            Recieved message from: {self.client_address[0]}
            Command: {self.command}
            Path: {self.path}
            """
        )
        return msg + str(self.headers).rstrip()


def terminate(sig, frame):
    raise KeyboardInterrupt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Display HTTP requests on STDOUT")
    p.add_argument(
        "-a", "--address", help="bind address (default: localhost)", default="localhost"
    )
    p.add_argument(
        "-p", "--port", type=int, help="bind port (default: 8080)", default=8080
    )
    p.add_argument(
        "-s",
        "--style",
        help="set the style of the formatting (default: github-dark)",
        default="github-dark",
    )
    p.add_argument(
        "--list-styles", action="store_true", help="List available styles and exit"
    )
    xs = p.parse_args()

    try:
        from pygments import highlight
        from pygments.formatters import Terminal256Formatter
        from pygments.lexers import PythonLexer
        from pprint import pformat

        if xs.list_styles:
            from pygments.styles import STYLE_MAP

            print("Available styles:")
            for s in STYLE_MAP:
                print(s)
            sys.exit()

        def pprint(obj: Any) -> None:
            print(
                highlight(
                    pformat(obj), PythonLexer(), Terminal256Formatter(style=xs.style)
                )
            )

    except ModuleNotFoundError:
        if xs.list_styles:
            print("Styles not supported install pygments https://pygments.org")
            sys.exit()
        from pprint import pprint
    print(f"Listening on {xs.address}:{xs.port}, press CTRL+C to stop")
    signal.signal(signal.SIGTERM, terminate)
    with http.server.HTTPServer((xs.address, xs.port), Dumper) as s:
        try:
            s.serve_forever()
        except KeyboardInterrupt:
            sys.exit()
