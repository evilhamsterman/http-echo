#!/usr/bin/env python3

# 2022, Georg Sauthoff
# 2023, Daniel Mills

import argparse
import http.server
import json
import sys
from http import HTTPStatus
from textwrap import dedent
from urllib.parse import parse_qs

try:
    from prettyprinter import cpprint as pprint, set_default_style
except ModuleNotFoundError:
    from pprint import pprint


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
            f"""\
            
            Recieved message from: {self.client_address[0]}
            Command: {self.command}
            Path: {self.path}
            """
        )
        return msg + str(self.headers).rstrip()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Display HTTP requests on STDOUT")
    p.add_argument("--address", help="bind address", default="localhost")
    p.add_argument("--port", type=int, help="bind port", default=8080)
    p.add_argument(
        "--style",
        help="set the output style for light or dark terminal",
        default="dark",
    )
    xs = p.parse_args()
    try:
        set_default_style(xs.style)
    except NameError:
        pass
    print(f"Listening on {xs.address}:{xs.port}, press CTRL+C to stop")
    with http.server.HTTPServer((xs.address, xs.port), Dumper) as s:
        try:
            s.serve_forever()
        except KeyboardInterrupt:
            sys.exit()
