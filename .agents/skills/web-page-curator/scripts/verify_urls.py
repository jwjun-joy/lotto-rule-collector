#!/usr/bin/env python3
"""Helper script to verify candidate URLs and check for required keywords in page content."""

import argparse
from html.parser import HTMLParser
import json
import re
import sys
import urllib.error
import urllib.request


class PageContentParser(HTMLParser):
    """Extracts page title, meta description, and visible text from HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.ignore_tags = {"script", "style", "noscript", "svg"}
        self.ignore_depth = 0
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self.meta_description = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_lower = tag.lower()
        if tag_lower in self.ignore_tags:
            self.ignore_depth += 1
        elif tag_lower == "title":
            self.in_title = True
        elif tag_lower == "meta":
            attr_dict = {k.lower(): (v or "") for k, v in attrs}
            name = attr_dict.get("name", "").lower()
            prop = attr_dict.get("property", "").lower()
            if name == "description" or prop == "og:description":
                if not self.meta_description and attr_dict.get("content"):
                    self.meta_description = attr_dict["content"].strip()

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        if tag_lower in self.ignore_tags and self.ignore_depth > 0:
            self.ignore_depth -= 1
        elif tag_lower == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        elif self.ignore_depth == 0:
            stripped = data.strip()
            if stripped:
                self.text_parts.append(stripped)

    @property
    def title(self) -> str:
        return re.sub(r"\s+", " ", "".join(self.title_parts)).strip()

    @property
    def text(self) -> str:
        return " ".join(self.text_parts)


def verify_url(url: str, keywords: list[str], timeout: int = 10) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; WebPageCuratorVerifier/1.0)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    req = urllib.request.Request(url, headers=headers)
    result = {
        "input_url": url,
        "final_url": url,
        "status": None,
        "accessible": False,
        "title": "",
        "meta_description": "",
        "matched_keywords": [],
        "missing_keywords": [],
        "text_length": 0,
        "snippet": "",
        "error": None,
    }

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result["status"] = resp.status
            result["final_url"] = resp.geturl()
            result["accessible"] = 200 <= resp.status < 400

            raw_bytes = resp.read(512 * 1024)  # Read up to 512KB
            charset = resp.headers.get_content_charset() or "utf-8"
            try:
                html_text = raw_bytes.decode(charset, errors="replace")
            except LookupError:
                html_text = raw_bytes.decode("utf-8", errors="replace")

            parser = PageContentParser()
            parser.feed(html_text)

            result["title"] = parser.title
            result["meta_description"] = parser.meta_description
            body_text = parser.text
            result["text_length"] = len(body_text)
            result["snippet"] = body_text[:300]

            body_lower = (parser.title + " " + parser.meta_description + " " + body_text).lower()
            for kw in keywords:
                if kw.lower() in body_lower:
                    result["matched_keywords"].append(kw)
                else:
                    result["missing_keywords"].append(kw)

    except urllib.error.HTTPError as e:
        result["status"] = e.code
        result["error"] = f"HTTP {e.code}: {e.reason}"
    except Exception as e:  # pylint: disable=broad-except
        result["error"] = str(e)

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify URLs and check if required keywords exist in the page content."
    )
    parser.add_argument("--urls", nargs="+", required=True, help="List of URLs to verify")
    parser.add_argument("--keywords", nargs="*", default=[], help="Keywords to check in page content")
    parser.add_argument("--timeout", type=int, default=10, help="HTTP request timeout in seconds")
    args = parser.parse_args()

    results = [verify_url(url, args.keywords, timeout=args.timeout) for url in args.urls]
    json.dump(results, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
