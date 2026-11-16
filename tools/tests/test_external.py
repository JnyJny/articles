"""Test the external URL check: the probe itself, and what it makes of answers."""

import socket
import ssl
import threading
import urllib.error
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Self

import pytest

from article_tools.external import (
    DEAD,
    UNREACHABLE,
    Probe,
    check_external,
    collect,
    probe,
    request,
    verdict,
)
from article_tools.model import find_articles

from .conftest import META, MakeRepo

STATUS = {"/ok": 200, "/gone": 410, "/missing": 404, "/boom": 500}


class Handler(BaseHTTPRequestHandler):
    """A tiny web server with a few pages, and one that dislikes HEAD."""

    def respond(self, *, head: bool) -> None:
        """Send the status for the path."""
        code = STATUS.get(self.path, 404)
        if self.path == "/nohead":
            code = 405 if head else 200
        self.send_response(code)
        self.end_headers()

    def do_HEAD(self) -> None:
        """Answer HEAD."""
        self.respond(head=True)

    def do_GET(self) -> None:
        """Answer GET."""
        self.respond(head=False)

    def log_message(self, *args: object) -> None:
        """Keep the test output quiet."""


@pytest.fixture(scope="module")
def server() -> Iterator[str]:
    """Serve on a free local port for the module, and return its base URL."""
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    httpd.server_close()


@pytest.mark.parametrize(
    ("path", "status"),
    [("/ok", 200), ("/gone", 410), ("/missing", 404), ("/boom", 500), ("/nohead", 200)],
)
def test_probe_reads_the_status(server: str, path: str, status: int) -> None:
    """The probe reports the status, falling back to GET when HEAD is refused."""
    assert probe(server + path, 2).status == status


def test_probe_connection_refused() -> None:
    """A port nobody listens on gives an error and no status."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    answer = probe(f"http://127.0.0.1:{port}/", 2)
    assert answer.status is None
    assert answer.error


@pytest.mark.parametrize("url", ["ftp://example.org/x", "file:///etc/passwd"])
def test_request_refuses_other_schemes(url: str) -> None:
    """Only http and https are ever fetched."""
    answer = request(url, 1, "HEAD")
    assert answer.status is None
    assert "not an http or https URL" in answer.error


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        (Probe(status=200), None),
        (Probe(status=301), None),
        (Probe(status=404), DEAD),
        (Probe(status=410), DEAD),
        (Probe(status=403), UNREACHABLE),
        (Probe(status=429), UNREACHABLE),
        (Probe(status=500), UNREACHABLE),
        (Probe(error="timed out"), UNREACHABLE),
    ],
)
def test_verdict(answer: Probe, expected: str | None) -> None:
    """Only a 404 or 410 is dead. Other trouble is unreachable. Good answers pass."""
    result = verdict(answer)
    assert (result[0] if result else None) == expected


def make_articles(repo: MakeRepo) -> list:
    """Two articles that share a URL, plus links that are not fetched."""
    first = (
        META
        + "# A\n\nsee [a][a] [b][b] [c][c]\n\n<!-- Links -->\n"
        + '[a]: http://x.test/ok\n[b]: http://x.test/gone "Title"\n'
        + "[c]: ../b/article.md\n[d]: mailto:me@x.test\n"
    )
    second = (
        META
        + "# B\n\n<!-- Links -->\n[e]: http://x.test/gone\n[f]: http://x.test/flaky\n"
    )
    root = repo({"c/a/article.md": first, "c/b/article.md": second})
    return find_articles(root, include_stubs=True)


def test_collect_gathers_http_urls_with_their_places(repo: MakeRepo) -> None:
    """Each URL is listed once with every place that uses it."""
    urls = collect(make_articles(repo))
    assert sorted(urls) == [
        "http://x.test/flaky",
        "http://x.test/gone",
        "http://x.test/ok",
    ]
    assert len(urls["http://x.test/gone"]) == 2


def test_check_external_reports_each_place_and_fetches_once(repo: MakeRepo) -> None:
    """A dead URL is reported where it is used, and each URL is fetched only once."""
    calls: list[str] = []
    answers = {
        "http://x.test/ok": Probe(status=200),
        "http://x.test/gone": Probe(status=404),
        "http://x.test/flaky": Probe(error="timed out"),
    }

    def fetch(url: str, _timeout: float) -> Probe:
        calls.append(url)
        return answers[url]

    findings = check_external(make_articles(repo), fetch=fetch)
    assert sorted(calls) == sorted(answers)
    assert [(f.article, f.rule) for f in findings] == [
        ("c/a", DEAD),
        ("c/b", DEAD),
        ("c/b", UNREACHABLE),
    ]
    assert "HTTP 404" in findings[0].message
    assert "timed out" in findings[2].message


class FakeResponse:
    """The part of an HTTP response the probe reads."""

    def __init__(self, status: int) -> None:
        """Remember the status."""
        self.status = status

    def __enter__(self) -> Self:
        """Enter the response context."""
        return self

    def __exit__(self, *args: object) -> None:
        """Leave the response context."""


def test_a_bad_certificate_is_retried_unverified_and_noted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A certificate failure falls back to an unverified ask, and says so."""
    contexts: list[object] = []

    def fake_urlopen(_request: object, timeout: float, context: object) -> FakeResponse:
        contexts.append(context)
        if context is None:
            reason = ssl.SSLCertVerificationError(
                "unable to get local issuer certificate"
            )
            raise urllib.error.URLError(reason)
        assert timeout == 2
        return FakeResponse(404)

    monkeypatch.setattr("article_tools.external.urllib.request.urlopen", fake_urlopen)
    answer = request("https://old.test/page", 2, "HEAD")
    assert answer == Probe(status=404, note="certificate not verified")
    assert contexts[0] is None
    assert isinstance(contexts[1], ssl.SSLContext)
    assert contexts[1].verify_mode == ssl.CERT_NONE
    assert verdict(answer) == (DEAD, "HTTP 404 (certificate not verified)")


def test_other_network_errors_are_not_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    """A refused connection is reported as it is, with one attempt."""
    calls: list[object] = []

    def fake_urlopen(_request: object, **kwargs: object) -> FakeResponse:
        calls.append(kwargs["timeout"])
        message = "connection refused"
        raise urllib.error.URLError(message)

    monkeypatch.setattr("article_tools.external.urllib.request.urlopen", fake_urlopen)
    assert request("https://x.test/", 2, "HEAD") == Probe(error="connection refused")
    assert len(calls) == 1


def test_an_os_error_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    """A socket-level error is an answer of no answer."""

    def fake_urlopen(_request: object, **_kwargs: object) -> FakeResponse:
        message = "boom"
        raise TimeoutError(message)

    monkeypatch.setattr("article_tools.external.urllib.request.urlopen", fake_urlopen)
    assert request("https://x.test/", 2, "HEAD") == Probe(error="boom")
