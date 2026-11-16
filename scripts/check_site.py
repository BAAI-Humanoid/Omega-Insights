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
BASE = json.loads((ROOT / "site.json").read_text(encoding="utf-8")).get("base_path", "").rstrip("/")


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.ids, self.links, self.images, self.duplicates = set(), [], [], []
        self.h1 = 0
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
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


def main():
    errors = []
    pages = {p: Page(p.read_text(encoding="utf-8")) for p in DIST.rglob("*.html")}
    assert pages, "Build the website first"
    for file, page in pages.items():
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
    for file in list(DIST.glob("*.xml")) + list((DIST / "assets").glob("*.svg")):
        ET.parse(file)
    for file in (ROOT / "content" / "posts").glob("*.md"):
        source = file.read_text(encoding="utf-8")
        definitions = re.findall(r"^\[\^([^\]]+)\]:", source, re.M)
        uses = re.findall(r"\[\^([^\]]+)\](?!:)", source)
        if len(definitions) != len(set(definitions)):
            errors.append(f"{file}: duplicate footnote definitions")
        for missing in set(uses) - set(definitions):
            errors.append(f"{file}: undefined footnote {missing}")
        meta = json.loads(file.with_suffix(".json").read_text(encoding="utf-8"))
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
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"PASS: {len(pages)} HTML pages; internal links, anchors, images, XML, footnotes and references")


if __name__ == "__main__":
    main()
