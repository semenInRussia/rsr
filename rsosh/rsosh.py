"""Parse a list of Russian school Olympiad from rsr-olymp.ru."""

import copy
from html.parser import HTMLParser
from http.client import HTTPResponse, HTTPSConnection
from urllib.parse import urlparse

from attr import dataclass


@dataclass
class Olymp:
    """A representation of a school Olympiad."""

    number: int
    name: str
    url: str
    lesson: str
    level: int

    def __str__(self) -> str:
        return f"{self.number}: {self.name}: {self.lesson} (#{self.level})"


def _remove_extra_whitespaces(s):
    return " ".join(s.split())


@dataclass
class _ParsingOlymp:
    """A class to store parsed parts of Olymp."""

    number: int | None
    name: str | None
    url: str | None
    lessons: list[str] | None
    levels: list[int] | None

    def is_parsed(self) -> bool:
        """Return True, if this Olympiad in parsing process already parsed."""
        # return true if all values aren't None
        return all(self.__dict__.values())


def empty_olymp() -> _ParsingOlymp:
    """Return an _ParsingOlymp instance with empty values."""
    return _ParsingOlymp(None, None, None, None, None)


class Parser(HTMLParser):
    """A class to parse a web-page with RSR Olympiads table."""

    # the result fields
    _is_parsed_olymps_fresh: bool = False
    _olymps: list[_ParsingOlymp] = []
    _parsed_olymps: list[Olymp] | None = None

    _current_olymp = empty_olymp()

    # state flags to check the current event, yes it's an anti-pattern
    # but anyway
    _in_table = False
    _in_thead = False
    _is_parse_olymp = False

    @property
    def parsed_olymps(self) -> list[Olymp]:
        """Return already parsed Olympiads."""
        if self._is_parsed_olymps_fresh:
            return self._parsed_olymps or []

        self._is_parsed_olymps_fresh = True
        olymps = []

        # NOTE: that one Olymp - one lesson, we can found some olymps
        # with the same name, number but with different lessons.
        #
        # so, ITMO: Physics, ITMO: ICT, ITMO: Math are 3 different olympiads
        for o in self._olymps:
            if not o.is_parsed():
                continue

            for i in range(len(o.levels)):  # type: ignore
                olymps.append(
                    Olymp(
                        number=o.number,  # type: ignore
                        name=o.name,  # type: ignore
                        level=o.levels[i],  # type: ignore
                        url=o.url,  # type: ignore
                        lesson=o.lessons[i * 2],  # type: ignore
                    )
                )

        self._parsed_olymps = olymps
        return olymps

    def handle_starttag(  # noqa
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attrs_dict = dict(attrs)

        if tag == "table" and not self._in_table:
            self._in_table = attrs_dict.get("class") == "mainTableInfo"
            return

        if not self._in_table:
            return

        # ignore any thing inside </thead> tag
        if self._in_thead:
            return

        if tag == "thead":
            self._in_thead = True
            return

        # any olympiad info is located inside </tr> tag
        if tag == "tr":
            self._is_parse_olymp = True
            self._current_olymp = empty_olymp()
            return

        # inside </a> tag should be located the URL to an olympiad
        if tag == "a" and self._is_parse_olymp:
            self._current_olymp.url = attrs_dict.get("href")
            return

    def handle_data(self, data: str) -> None:  # noqa
        # handle tag content only if we parse an Olympiad
        if not self._is_parse_olymp or not self._in_table:
            return

        # ignore empty strings
        if not data.strip("\n\t "):
            return

        # Sometimes, after </tr> can be other <tr> with some
        # additional lessons of this olympiad.
        #
        # Handle this case
        if self._current_olymp.number is None and not data.isdigit():
            self._current_olymp = self._olymps[-1]
            self._olymps.pop()

        # if olympiad's number haven't parsed yet, then we get a
        # number of current olympiad, almost whole logic of this
        # function is within it
        if self._current_olymp.number is None:
            self._current_olymp.number = int(data)
            return

        if self._current_olymp.url is None:
            # olymp URL located inside a.href and handled in other
            # place
            return

        if self._current_olymp.name is None:
            self._current_olymp.name = _remove_extra_whitespaces(data)
            return

        # after name can be lessons or level of this olympiad.  If a
        # string is digits, then it's a level
        if self._current_olymp.levels is None:
            self._current_olymp.levels = []

        if data.isdigit():
            self._current_olymp.levels.append(int(data))
            return

        if self._current_olymp.lessons is None:
            self._current_olymp.lessons = []

        self._current_olymp.lessons.append(_remove_extra_whitespaces(data))

    def handle_endtag(self, tag: str) -> None:  # noqa
        if tag == "table":
            self._in_table = False

        if tag == "thead":
            self._in_thead = False
            return

        if tag == "tr" and self._is_parse_olymp:
            self._is_parse_olymp = False
            self._save_current_olymp()
            return

    def _save_current_olymp(self) -> None:
        ol = copy.deepcopy(self._current_olymp)
        self._olymps.append(ol)
        self._is_parsed_olymps_fresh = False


RSR_URL = "https://rsr-olymp.ru"
CHUNK_SIZE = 1024 * 1024 * 1024


def parse_from_web(url=RSR_URL) -> list[Olymp]:
    """Parse Olympiads from web-page over the http(s) ."""
    resp = _do_http_request(url)
    p = Parser()

    chunk = resp.read(CHUNK_SIZE)
    while chunk:
        p.feed(chunk.decode("utf-8"))
        chunk = resp.read(CHUNK_SIZE)

    return p.parsed_olymps


def _do_http_request(url) -> HTTPResponse:
    u = urlparse(url)
    return _http_request_to_host(u.hostname, u.path)


def _http_request_to_host(host, uri="/") -> HTTPResponse:
    c = HTTPSConnection(host)
    c.request("GET", uri)
    resp = c.getresponse()
    return resp


def _main():
    """Just use API that defined above at the file."""
    parsed_olymps = parse_from_web()

    for olymp in parsed_olymps:
        if olymp.lesson != "информатика":
            continue
        print(olymp.name, f"({olymp.level})")
        print(olymp.url)
        print("---")


if __name__ == "__main__":
    _main()
