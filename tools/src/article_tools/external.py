"""Check that the external URLs in the link blocks still answer."""

from __future__ import annotations

import dataclasses
import ssl
import urllib.error
import urllib.request
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .rules import definitions

if TYPE_CHECKING:
    from .model import Article, Finding

DEAD = "dead-link"
UNREACHABLE = "unreachable-link"
DEAD_STATUSES = frozenset({404, 410})
HTTP_ERROR = 400
USER_AGENT = "article-tools link check"
SCHEMES = ("http://", "https://")


@dataclass(frozen=True)
class Probe:
    """What a URL answered: a status, or why there was no answer."""

    status: int | None = None
    error: str = ""
    note: str = ""


Fetch = Callable[[str, float], Probe]


def unverified() -> ssl.SSLContext:
    """Return a TLS context that does not check certificates."""
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


def request(url: str, timeout: float, method: str, *, verify: bool = True) -> Probe:
    """Ask a URL once with one method.

    When the certificate cannot be verified, ask again without checking it and
    say so. Only a status code is read, and nothing identifying is sent.
    """
    if not url.lower().startswith(SCHEMES):
        return Probe(error=f"not an http or https URL: {url}")
    asked = urllib.request.Request(  # noqa: S310
        url,
        method=method,
        headers={"User-Agent": USER_AGENT},
    )
    try:
        context = None if verify else unverified()
        with urllib.request.urlopen(  # noqa: S310
            asked, timeout=timeout, context=context
        ) as response:
            return Probe(status=response.status)
    except urllib.error.HTTPError as error:
        return Probe(status=error.code)
    except urllib.error.URLError as error:
        if verify and isinstance(error.reason, ssl.SSLCertVerificationError):
            retry = request(url, timeout, method, verify=False)
            return dataclasses.replace(retry, note="certificate not verified")
        return Probe(error=str(error.reason))
    except (OSError, ValueError) as error:
        return Probe(error=str(error))


def probe(url: str, timeout: float) -> Probe:
    """Ask with HEAD, and again with GET when the server rejects HEAD."""
    first = request(url, timeout, "HEAD")
    if first.status is not None and first.status >= HTTP_ERROR:
        return request(url, timeout, "GET")
    return first


def collect(articles: list[Article]) -> dict[str, list[tuple[Article, int, str]]]:
    """Gather each external URL with every place it is used."""
    urls: dict[str, list[tuple[Article, int, str]]] = {}
    for article in articles:
        for reference, (number, target) in definitions(article).items():
            url = target.split()[0]
            if url.lower().startswith(SCHEMES):
                urls.setdefault(url, []).append((article, number, reference))
    return urls


def verdict(answer: Probe) -> tuple[str, str] | None:
    """Return (rule, detail) for a bad answer, or nothing for a good one."""
    noted = f" ({answer.note})" if answer.note else ""
    if answer.status is None:
        return UNREACHABLE, f"no answer: {answer.error}{noted}"
    if answer.status in DEAD_STATUSES:
        return DEAD, f"HTTP {answer.status}{noted}"
    if answer.status >= HTTP_ERROR:
        return (
            UNREACHABLE,
            f"HTTP {answer.status}{noted}, the site may refuse automated checks",
        )
    return None


def check_external(
    articles: list[Article],
    *,
    timeout: float = 10.0,
    workers: int = 8,
    fetch: Fetch = probe,
) -> list[Finding]:
    """Check every external URL once, and report each place a bad one is used."""
    urls = collect(articles)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        answers = dict(
            zip(urls, pool.map(lambda url: fetch(url, timeout), urls), strict=True)
        )
    findings: list[Finding] = []
    for url, places in urls.items():
        bad = verdict(answers[url])
        if bad:
            rule, detail = bad
            findings += [
                article.finding(rule, number, f"[{reference}] {url}: {detail}")
                for article, number, reference in places
            ]
    return sorted(findings, key=lambda finding: (finding.article, finding.line))
