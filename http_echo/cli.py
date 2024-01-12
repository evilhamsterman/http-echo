#!/usr/bin/env python3

# 2022, Georg Sauthoff
# 2023, Daniel Mills

import http.server
import json
import signal
import sys
from enum import StrEnum
from http import HTTPStatus
from textwrap import dedent
from typing import Annotated, Iterable, Mapping
from urllib.parse import parse_qs

import pygments.styles
from rich import print
from rich.columns import Columns
from rich.panel import Panel
from rich.pretty import Pretty
from rich.syntax import Syntax
from rich.text import Text
from typer import Exit, Option, Typer

from http_echo import __version__

app = Typer()

STYLES = StrEnum(
    "SYTLES", [(s[1].replace("-", "_"), s[1]) for s in pygments.styles.STYLES.values()]
)


class Dumper(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        """Print a GET request."""
        print(self.__format_req_data())
        self.send_response(HTTPStatus.OK)
        self.end_headers()

    def do_DELETE(self):
        """Delete is just redirected to GET"""
        return self.do_GET()

    def do_POST(self):
        """Print a POST request.

        Use syntax highlighting if the request is a structured type like JSON,
        form data, or XML.
        """
        n = int(self.headers.get("content-length", 0))
        body = self.rfile.read(n)
        req_panel = self.__format_req_data()

        if self.headers.get("content-type") == "application/json":
            try:
                data = body.decode()
                body_panel = self.__format_json_data(
                    data,
                    title="JSON",
                )
            except json.decoder.JSONDecodeError:
                body_panel = Panel(
                    f"[bold red]{body}[/bold red]",
                    title="Invalid JSON",
                    style="bold red",
                )
        elif self.headers.get("content-type") == "application/x-www-form-urlencoded":
            try:
                data = parse_qs(body.decode(), strict_parsing=True)
                body_panel = self.__format_json_data(
                    data,
                    title="Form",
                )
            except ValueError:
                body_panel = Panel(
                    f"[bold red]{body}[bold red]",
                    title="Invalid Form",
                    style="bold red",
                )
        else:
            body_panel = Panel(Pretty(body), title="Unknown body format")
        print(
            Panel(
                Columns([req_panel, body_panel], expand=False),
                title="Request",
                expand=False,
                title_align="left",
            )
        )
        self.send_response(HTTPStatus.OK)
        self.end_headers()

    def do_PUT(self):
        return self.do_POST()

    def log_message(self, format, *args):
        pass

    def __format_req_data(self) -> Panel:
        msg = dedent(
            f"""
            [white]Recieved message from: {self.client_address[0]}
            Command: {self.command}
            Path: {self.path}[/white]
            """
        )
        return Panel(msg, title="Request info", width=40, style="bold green")

    def __format_json_data(self, data: str | Iterable | Mapping, title: str) -> Syntax:
        if isinstance(data, str):
            try:
                json.loads(data)  # validate JSON
                s = Syntax(data, lexer="json", indent_guides=True, line_numbers=True)
            except json.decoder.JSONDecodeError:
                print("Invalid JSON")
                raise
        else:
            s = Syntax(
                json.dumps(data, indent=4),
                lexer="json",
                indent_guides=True,
                line_numbers=True,
            )
        return Panel(s, title=title, width=100)


def terminate(sig, frame):
    raise KeyboardInterrupt


def version_callback(value: bool):
    """Print the version of the program and exit"""
    if value:
        print(Text(f"http-echo {__version__}"))
        raise Exit()


def list_styles_callback(value: bool):
    """Print available styles and exit"""
    if value:
        from pygments.styles import STYLE_MAP

        print("Available styles:")
        for s in STYLE_MAP:
            print(s)
        raise Exit()


@app.command()
def main(
    address: Annotated[str, Option("-a", "--address")] = "localhost",
    port: Annotated[int, Option("-p", "--port")] = 8080,
    style: Annotated[
        STYLES,
        Option("-s", "--style", show_choices=STYLES),
    ] = STYLES.github_dark,
    list_styles: Annotated[
        bool, Option("--list-styles", callback=list_styles_callback, is_eager=True)
    ] = False,
    version: Annotated[
        bool, Option("--version", callback=version_callback, is_eager=True)
    ] = None,
):
    """Display HTTP requests on STDOUT with fancy formatting"""
    print(f"Listening on {address}:{port}, press CTRL+C to stop")
    signal.signal(signal.SIGTERM, terminate)
    with http.server.HTTPServer((address, port), Dumper) as s:
        try:
            s.serve_forever()
        except KeyboardInterrupt:
            sys.exit()
