#!/usr/bin/env python3
"""Check the built site's links, anchors, references, feeds, and metadata offline."""
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
CONFIG = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
BASE = CONFIG.get("base_path", "").rstrip("/")
ORIGIN = CONFIG["url"].rstrip("/")


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.ids, self.links, self.images, self.duplicates = set(), [], [], []
        self.h1 = 0
        self.locale, self.canonical = None, None
        self.alternates, self.language_links = {}, []
        self.structured, self.citation = [], ""
        self._capture = None
        self._buffer = ""
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "script" and a.get("type") == "application/ld+json":
            self._capture, self._buffer = "schema", ""
        if tag == "code" and a.get("id") == "article-bibtex":
            self._capture, self._buffer = "citation", ""
        if tag == "html":
            self.locale = a.get("lang")
        if tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href")
        if tag == "link" and a.get("rel") == "alternate" and "hreflang" in a:
            self.alternates[a["hreflang"]] = a.get("href")
        if tag == "a" and "hreflang" in a:
            self.language_links.append(a)
        if "id" in a:
            if a["id"] in self.ids:
                self.duplicates.append(a["id"])
            self.ids.add(a["id"])
        if tag == "h1":
            self.h1 += 1
        for key in ("href", "src"):
            if key in a:
                self.links.append(a[key])
        if tag == "img":
            self.images.append(a)

    def handle_data(self, data):
        if self._capture:
            self._buffer += data

    def handle_endtag(self, tag):
        if tag == "script" and self._capture == "schema":
            self.structured.append(json.loads(self._buffer))
            self._capture = None
        elif tag == "code" and self._capture == "citation":
            self.citation = self._buffer
            self._capture = None


def main():
    errors = []
    pages = {p: Page(p.read_text(encoding="utf-8")) for p in DIST.rglob("*.html")}
    assert pages, "Build the website first"
    for file, page in pages.items():
        relative = file.relative_to(DIST).as_posix()
        lang = "en" if relative.startswith("en/") else "zh-CN"
        common = relative.removeprefix("en/") if lang == "en" else relative
        common = common.removesuffix("index.html")
        expected = {"zh-CN": ORIGIN + BASE + "/" + common, "en": ORIGIN + BASE + "/en/" + common}
        if page.locale != lang or page.canonical != expected[lang]:
            errors.append(f"{file}: incorrect language or canonical URL")
        if page.alternates != {**expected, "x-default": expected["zh-CN"]}:
            errors.append(f"{file}: incorrect translation alternates")
        switches = {a.get("hreflang"): a.get("href") for a in page.language_links}
        if switches != {key: urlsplit(value).path for key, value in expected.items()}:
            errors.append(f"{file}: language switch does not point to the same page")
        current = [a.get("hreflang") for a in page.language_links if a.get("aria-current") == "page"]
        if current != [lang]:
            errors.append(f"{file}: language switch active state is incorrect")
        if page.h1 != 1:
            errors.append(f"{file}: expected one h1; got {page.h1}")
        if page.duplicates:
            errors.append(f"{file}: duplicate IDs {page.duplicates}")
        for image in page.images:
            if "alt" not in image:
                errors.append(f"{file}: image has no alt text")
        for link in page.links:
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc:
                if parsed.scheme not in ("http", "https", "mailto", "tel"):
                    errors.append(f"{file}: unexpected URL scheme {link}")
                continue
            raw_path = unquote(parsed.path)
            if raw_path.startswith("/"):
                if BASE and not raw_path.startswith(BASE + "/"):
                    errors.append(f"{file}: URL does not respect base_path: {link}")
                raw_path = raw_path[len(BASE):].lstrip("/")
                target = DIST / raw_path
            else:
                target = file.parent / raw_path if raw_path else file
            if target.is_dir():
                target /= "index.html"
            target = target.resolve()
            if not target.is_file():
                errors.append(f"{file}: broken local URL {link}")
                continue
            if parsed.fragment and target.suffix == ".html":
                target_page = pages.get(target)
                if target_page is None or unquote(parsed.fragment) not in target_page.ids:
                    errors.append(f"{file}: missing anchor {link}")
    for file in list(DIST.rglob("*.xml")) + list((DIST / "assets").glob("*.svg")):
        ET.parse(file)
    for lang, feed_path in (("zh-CN", "feed.xml"), ("en", "en/feed.xml")):
        channel = ET.parse(DIST / feed_path).getroot().find("channel")
        if channel.findtext("language") != lang:
            errors.append(f"{feed_path}: wrong RSS language")
        for item in channel.findall("item"):
            local_url = urlsplit(item.findtext("link")).path.removeprefix(BASE + "/")
            if not (DIST / local_url / "index.html").is_file():
                errors.append(f"{feed_path}: missing article {local_url}")
    for file in (ROOT / "content" / "posts").rglob("*.md"):
        source = file.read_text(encoding="utf-8")
        definitions = re.findall(r"^\[\^([^\]]+)\]:", source, re.M)
        uses = re.findall(r"\[\^([^\]]+)\](?!:)", source)
        if len(definitions) != len(set(definitions)):
            errors.append(f"{file}: duplicate footnote definitions")
        for missing in set(uses) - set(definitions):
            errors.append(f"{file}: undefined footnote {missing}")
        meta = json.loads(file.with_suffix(".json").read_text(encoding="utf-8"))
        lang = "en" if file.parent.name == "en" else "zh-CN"
        prefix = "en/" if lang == "en" else ""
        article_page = pages[DIST / prefix / "insights" / meta["slug"] / "index.html"]
        expected_authors = [{"@type": author["type"], "name": author["name"]} for author in meta["authors"]]
        if len(article_page.structured) != 1 or article_page.structured[0].get("author") != expected_authors:
            errors.append(f"{file}: incorrect structured author metadata")
        citation_file = DIST / "downloads" / (meta["slug"] + (".cite.en.bib" if lang == "en" else ".cite.bib"))
        citation = citation_file.read_text(encoding="utf-8")
        if citation != article_page.citation:
            errors.append(f"{file}: displayed and downloaded article citations differ")
        expected_bib_author = " and ".join(author["bibtex"] for author in meta["authors"])
        if f"author = {{{expected_bib_author}}}" not in citation or f"date = {{{meta['date']}}}" not in citation:
            errors.append(f"{file}: incorrect article citation author or publication date")
        if not citation.startswith("@misc{" + meta["citation_key"] + ",") or article_page.canonical not in citation:
            errors.append(f"{file}: article citation must use its key and canonical URL")
        refs = json.loads((ROOT / "content" / "references" / (meta["slug"] + ".json")).read_text(encoding="utf-8"))
        ids = [ref["id"] for ref in refs]
        if len(ids) != len(set(ids)):
            errors.append(f"{file}: duplicate reference IDs")
        for ref in refs:
            if not all(ref.get(key) for key in ("id", "title", "url", "organization", "accessed")):
                errors.append(f"Incomplete reference: {ref}")
            if not ref["url"].startswith("https://"):
                errors.append(f"Reference must use HTTPS: {ref['url']}")
        for missing in set(definitions) - set(ids):
            errors.append(f"{file}: footnote {missing} has no structured reference")
        if file.parent.name == "en":
            original = file.parent.parent / file.name
            original_source = original.read_text(encoding="utf-8")
            original_definitions = re.findall(r"^\[\^([^\]]+)\]:", original_source, re.M)
            if definitions != original_definitions:
                errors.append(f"{file}: translated footnotes differ from the Chinese version")
            external_links = re.findall(r"\]\((https?://[^)]+)\)", source)
            original_links = re.findall(r"\]\((https?://[^)]+)\)", original_source)
            if external_links != original_links:
                errors.append(f"{file}: translated source links differ from the Chinese version")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"PASS: {len(pages)} bilingual HTML pages; language switches, metadata, RSS, links, figures and references")


if __name__ == "__main__":
    main()
