#!/usr/bin/env python3
"""Build paired Chinese/English research pages from Markdown and shared references."""
import datetime as dt
import html
import json
import re
import shutil
import unicodedata
from pathlib import Path
import xml.etree.ElementTree as ET

import markdown

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist"
CONFIG = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
BASE = CONFIG.get("base_path", "").rstrip("/")
ORIGIN = CONFIG["url"].rstrip("/")
LANGUAGES = ("zh-CN", "en")
UI = {lang: json.loads((ROOT / "content" / "ui" / f"{lang}.json").read_text(encoding="utf-8")) for lang in LANGUAGES}
e = html.escape


def route(lang, value=""):
    return ("en/" if lang == "en" else "") + value.lstrip("/")


def path(value=""):
    return f"{BASE}/{value.lstrip('/')}"


def absolute(value=""):
    return ORIGIN + path(value)


def write(name, text):
    dest = OUT / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")


def slugify(value, separator):
    value = unicodedata.normalize("NFKC", value).lower()
    value = re.sub(r"[^\w\s-]", "", value)
    return re.sub(r"[-\s]+", separator, value).strip(separator) or "section"


def shell(title, description, body, lang, relative="", page_class="", structured=None):
    ui = UI[lang]
    canonical = absolute(route(lang, relative))
    schema = ""
    if structured:
        schema = '<script type="application/ld+json">' + json.dumps(structured, ensure_ascii=False).replace("<", "\\u003c") + "</script>"
    alternates = '\n'.join(f'<link rel="alternate" hreflang="{other}" href="{absolute(route(other, relative))}">' for other in LANGUAGES)
    alternates += f'\n<link rel="alternate" hreflang="x-default" href="{absolute(relative)}">'
    switch = ""
    for other, label in (("zh-CN", "中文"), ("en", "EN")):
        current = ' aria-current="page"' if other == lang else ""
        switch += f'<a href="{path(route(other, relative))}" lang="{other}" hreflang="{other}" aria-label="{UI[other]["language_name"]}"{current}>{label}</a>'
    return f'''<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(description)}">
<meta name="theme-color" content="#154c44"><link rel="canonical" href="{e(canonical)}">
{alternates}
<meta property="og:type" content="{'article' if structured else 'website'}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{e(canonical)}"><meta property="og:locale" content="{ui['og_locale']}">
<link rel="icon" href="{path('assets/favicon.svg')}" type="image/svg+xml">
<link rel="stylesheet" href="{path('assets/style.css')}">
<link rel="alternate" type="application/rss+xml" title="{e(CONFIG['name'])} · {ui['language_name']}" href="{path(route(lang, 'feed.xml'))}">
{schema}
<script defer src="{path('assets/site.js')}"></script>
</head>
<body class="{page_class}">
<a class="skip-link" href="#main">{ui['skip']}</a>
<header class="site-header"><div class="header-inner">
<a class="brand" href="{path(route(lang))}"><img class="brand-mark" src="{path('assets/favicon.svg')}" alt="" width="34" height="34"><span class="brand-text">Omega <span>Insights</span></span></a>
<div class="header-controls"><nav class="nav" aria-label="{ui['nav']['label']}"><a href="{path(route(lang, '#articles'))}">{ui['nav']['articles']}</a><a href="{path(route(lang, 'about/'))}">{ui['nav']['about']}</a><a href="{CONFIG['organization_url']}">GitHub <span aria-hidden="true">↗</span></a></nav><nav class="language-switch" aria-label="{ui['language_label']}">{switch}</nav></div>
</div></header>
{body}
<footer class="site-footer"><div class="footer-inner"><div><strong>Omega Insights</strong><p>Thinking through intelligence. Grounded in the physical world.</p></div><nav aria-label="{ui['footer']['label']}"><a href="{path(route(lang, 'feed.xml'))}">{ui['footer']['rss']}</a><a href="{CONFIG['repository_url']}">{ui['footer']['source']}</a><a href="{path(route(lang, 'about/'))}">{ui['footer']['about']}</a></nav><small>© {dt.date.today().year} BAAI-Humanoid · {ui['footer']['copyright']}</small></div></footer>
</body></html>'''


def tags(values):
    return '<div class="post-tags">' + ''.join(f'<span class="tag">{e(value)}</span>' for value in values) + '</div>'


def bibliography(items):
    # Organization authors are deliberately braced to preserve their names in BibTeX.
    result = []
    for item in items:
        def clean(value):
            return str(value).replace("\\", "\\textbackslash{}").replace("{", "\\{").replace("}", "\\}").replace("&", "\\&").replace("%", "\\%")
        key = re.sub(r"[^a-zA-Z0-9_-]", "", item["id"])
        fields = {
            "title": clean(item["title"]),
            "author": " and ".join(clean(a) for a in item["authors"]) if item.get("authors") else "{" + clean(item.get("organization", "")) + "}",
            "howpublished": "\\url{" + item["url"] + "}",
            "url": item["url"],
            "note": "Accessed " + item.get("accessed", "2026-11-16"),
        }
        if item.get("published"):
            fields["year"] = item["published"][:4]
        for field in ("journal", "booktitle", "volume", "pages", "series", "publisher", "eprint", "archivePrefix", "doi"):
            if item.get(field):
                fields[field] = clean(item[field])
        kind = item.get("type", "misc")
        if kind not in ("misc", "inproceedings", "article"):
            raise ValueError(f"Unsupported reference type: {kind}")
        result.append("@" + kind + "{" + key + ",\n" + ",\n".join(f"  {k} = {{{v}}}" for k, v in fields.items()) + "\n}")
    return "\n\n".join(result) + "\n"


def article_bibtex(meta, lang):
    """Cite this post as a web publication, separately from its source bibliography."""
    escape_map = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "_": r"\_", "#": r"\#", "$": r"\$", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    clean = lambda text: "".join(escape_map.get(char, char) for char in text)
    url = absolute(route(lang, f"insights/{meta['slug']}/"))
    # Author metadata supplies BibTeX name syntax (family, given) or protected names.
    authors = " and ".join(author["bibtex"] for author in meta["authors"])
    fields = {
        "author": authors,
        "title": "{" + clean(meta["title"]) + "}",
        "year": meta["date"][:4],
        "date": meta["date"],
        "howpublished": clean(CONFIG["name"]),
        "url": url,
        "note": UI[lang]["citation"]["language_note"],
    }
    return "@misc{" + meta["citation_key"] + ",\n" + ",\n".join(f"  {key} = {{{value}}}" for key, value in fields.items()) + "\n}\n"


def citation_section(meta, lang, bibtex, download):
    ui = UI[lang]["citation"]
    names = UI[lang]["article"]["authors_separator"].join(author["name"] for author in meta["authors"])
    url = absolute(route(lang, f"insights/{meta['slug']}/"))
    return f'''<section id="cite" class="article-citation" aria-labelledby="citation-heading">
<h2 id="citation-heading">{ui['title']}</h2><p>{ui['intro']}</p>
<p class="citation-text">{e(names)} ({meta['date']}). {e(meta['title'])} <em>{e(CONFIG['name'])}</em>. <a href="{url}">{url}</a></p>
<pre><code id="article-bibtex" class="language-bibtex">{e(bibtex)}</code></pre>
<div class="citation-controls"><button class="button" type="button" data-copy-citation data-copied="{e(ui['copied'])}" data-success="{e(ui['success'])}" data-failure="{e(ui['failure'])}" hidden>{ui['copy']}</button><a class="button" download href="{path(download)}">{ui['download']}</a><span class="copy-status" role="status" aria-live="polite"></span></div>
</section>'''


def load_posts():
    pairs = []
    source_dir = ROOT / "content" / "posts"
    source_files = sorted(source_dir.glob("*.json"))
    if not source_files:
        raise ValueError("No posts found")
    if {p.name for p in source_files} != {p.name for p in (source_dir / "en").glob("*.json")}:
        raise ValueError("Every post needs matching Chinese and English metadata in content/posts/ and content/posts/en/.")
    for file in source_files:
        pair = {}
        for lang in LANGUAGES:
            localized_file = source_dir / ("en" if lang == "en" else "") / file.name
            meta = json.loads(localized_file.read_text(encoding="utf-8"))
            slug = meta["slug"]
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) or slug != file.stem:
                raise ValueError(f"Slug must match the filename: {localized_file}")
            if not re.fullmatch(r"[A-Za-z0-9_-]+", meta.get("citation_key", "")):
                raise ValueError(f"A stable citation_key is required: {localized_file}")
            if not meta.get("authors") or any(not all(author.get(key) for key in ("id", "name", "type", "bibtex")) or author["type"] not in ("Person", "Organization") for author in meta["authors"]):
                raise ValueError(f"Authors need id, localized name, type and BibTeX name: {localized_file}")
            source = localized_file.with_suffix(".md").read_text(encoding="utf-8")
            pair[lang] = (meta, source)
        for field in ("slug", "date"):
            if pair["zh-CN"][0].get(field) != pair["en"][0].get(field):
                raise ValueError(f"Translation metadata differs in {field}: {file.name}")
        author_ids = {lang: [(author["id"], author["type"]) for author in pair[lang][0]["authors"]] for lang in LANGUAGES}
        if author_ids["zh-CN"] != author_ids["en"]:
            raise ValueError(f"Translations must refer to the same authors: {file.name}")
        if pair["zh-CN"][0]["citation_key"] == pair["en"][0]["citation_key"]:
            raise ValueError(f"Use distinct citation keys for the two language editions: {file.name}")
        refs = json.loads((ROOT / "content" / "references" / file.name).read_text(encoding="utf-8"))
        pairs.append((pair, refs))
    return pairs


def build_article(meta, source, refs, lang):
    ui = UI[lang]["article"]
    category = meta.get("category", ui["category"])
    eyebrow = ui["eyebrow"].format(category=category)
    source = source.replace("{{BASE}}", BASE)
    renderer = markdown.Markdown(extensions=["extra", "toc", "sane_lists"], extension_configs={"toc": {"slugify": slugify, "toc_depth": "2-2", "permalink": False}})
    content = renderer.convert(source)
    content = content.replace("<table>", f'<div class="table-scroll" role="region" aria-label="{ui["table"]}" tabindex="0"><table>').replace("</table>", "</table></div>")
    tokens = re.findall(r"[\u4e00-\u9fff]|\b[a-zA-Z]+\b", source)
    minutes = meta.get("reading_minutes") or max(1, round(len(tokens) / (220 if lang == "en" else 330)))
    meta["reading_minutes"] = minutes
    relative = f"insights/{meta['slug']}/"
    reference_base = f"downloads/{meta['slug']}"
    markdown_file = reference_base + (".en.md" if lang == "en" else ".md")
    authors = ui["authors_separator"].join(author["name"] for author in meta["authors"])
    bibtex = article_bibtex(meta, lang)
    citation_file = reference_base + (".cite.en.bib" if lang == "en" else ".cite.bib")
    write(citation_file, bibtex)
    write(markdown_file, "# " + meta["title"] + "\n\n" + meta["subtitle"] + "\n\n" + authors + " · " + meta["date"] + "\n\n" + source + "\n\n## " + UI[lang]["citation"]["title"] + "\n\n```bibtex\n" + bibtex + "```\n")
    cite = citation_section(meta, lang, bibtex, citation_file)
    toc = renderer.toc.replace('class="toc"', 'class="toc-list"')
    article = f'''<main id="main">
<header class="article-header container"><a class="eyebrow text-link" href="{path(route(lang, '#articles'))}">{e(eyebrow)}</a><h1 class="article-title">{e(meta['title'])}</h1><p class="article-deck">{e(meta['subtitle'])}</p><div class="article-meta"><span>{e(authors)}</span><time datetime="{meta['date']}">{meta['date']}</time><span>{ui['minutes'].format(minutes=minutes)}</span><span>{ui['references'].format(count=len(refs))}</span></div>{tags(meta['tags'])}</header>
<div class="article-layout container"><aside class="toc"><details class="toc-inner" open><summary>{ui['toc']}</summary>{toc}<a class="text-link" href="#cite">{UI[lang]['citation']['title']}</a><a class="text-link toc-top" href="#main">{ui['top']}</a></details></aside><div><article class="article-body prose">{content}</article>{cite}<section class="article-actions" aria-label="{ui['files']}"><h2>{ui['continue']}</h2><p>{ui['continue_text']}</p><div><a class="button" download href="{path(markdown_file)}">{ui['markdown']}</a><a class="button" download href="{path(reference_base + '.bib')}">{ui['bibtex']}</a><a class="button" download href="{path(reference_base + '-references.json')}">{ui['json']}</a><button class="button" data-print hidden type="button">{ui['print']}</button><a class="text-link" href="{CONFIG['repository_url']}/issues/new">{ui['correction']}</a></div></section></div></div>
</main>'''
    schema = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": meta["title"], "description": meta["summary"], "inLanguage": lang, "datePublished": meta["date"], "dateModified": meta.get("updated", meta["date"]), "author": [{"@type": author["type"], "name": author["name"]} for author in meta["authors"]], "publisher": {"@type": "Organization", "name": "BAAI-Humanoid", "url": CONFIG["organization_url"]}, "mainEntityOfPage": absolute(route(lang, relative)), "citation": [ref["url"] for ref in refs]}
    schema["articleSection"] = category
    write(route(lang, relative) + "index.html", shell(meta["title"] + " · " + CONFIG["name"], meta["summary"], article, lang, relative, "article-page", schema))


def build_home(posts, lang):
    ui = UI[lang]["home"]
    previews = ""
    for i, post in enumerate(posts, 1):
        href = path(route(lang, 'insights/' + post['slug'] + '/'))
        category = post.get("category", UI[lang]["article"]["category"])
        previews += f'''<article class="featured-post"><div class="post-number">{i:02d}</div><div class="post-preview"><div class="hero-meta"><time datetime="{post['date']}">{post['date']}</time><span>{e(ui['preview'].format(category=category, minutes=post['reading_minutes']))}</span></div><h3 class="post-title"><a href="{href}">{e(post['title'])}</a></h3><p class="post-excerpt">{e(post['summary'])}</p>{tags(post['tags'])}<a class="read-link" href="{href}">{ui['read']} <span aria-hidden="true">↗</span></a></div></article>'''
    topics = ''.join(f'<span>{e(topic)}</span>' for topic in ui['topics'])
    cards = ''.join(f'<div><span class="eyebrow">{card["label"]}</span><h2>{e(card["title"])}</h2><p>{e(card["text"])}</p></div>' for card in ui['cards'])
    count_label = ui['count'].format(count=len(posts))
    if lang == "en":
        count_label = f"{len(posts):02d} " + ("article" if len(posts) == 1 else "articles")
    body = f'''<main id="main" class="container"><section class="hero"><p class="eyebrow">OMEGA INSIGHTS</p><h1 class="hero-title">{e(ui['title'][0])}<br><span>{e(ui['title'][1])}</span></h1><p class="hero-deck">{e(ui['deck'])}</p><div class="hero-meta">{topics}</div></section><section id="articles" aria-labelledby="articles-title"><div class="section-heading"><h2 id="articles-title">{ui['section']}</h2><span>{count_label}</span></div>{previews}</section><section class="research-strip" aria-label="{ui['focus']}">{cards}</section></main>'''
    write(route(lang, "index.html"), shell(CONFIG['name'], UI[lang]['description'], body, lang))


def build_about(lang):
    ui = UI[lang]['about']
    sections = ""
    for section in ui['sections']:
        paragraphs = ''.join('<p>' + paragraph.format(organization_url=e(CONFIG['organization_url']), issues_url=e(CONFIG['repository_url'] + '/issues/new')) + '</p>' for paragraph in section['paragraphs'])
        sections += f'<section><h2>{e(section["title"])}</h2>{paragraphs}</section>'
    body = f'''<main id="main" class="container"><header class="article-header"><p class="eyebrow">{ui['eyebrow']}</p><h1 class="article-title">{e(ui['title'][0])}<br>{e(ui['title'][1])}</h1><p class="article-deck">{e(ui['deck'])}</p></header><div class="prose about-grid">{sections}</div></main>'''
    write(route(lang, "about/index.html"), shell(UI[lang]['nav']['about'] + ' · ' + CONFIG['name'], UI[lang]['description'], body, lang, 'about/'))


def build_feed(posts, lang):
    creator_ns = 'http://purl.org/dc/elements/1.1/'
    ET.register_namespace('dc', creator_ns)
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    for key, value in {'title': CONFIG['name'] + ' · ' + UI[lang]['language_name'], 'link': absolute(route(lang)), 'description': UI[lang]['description'], 'language': lang}.items():
        ET.SubElement(channel, key).text = value
    for post in posts:
        item = ET.SubElement(channel, 'item')
        url = absolute(route(lang, f"insights/{post['slug']}/"))
        values = {'title': post['title'], 'link': url, 'guid': url, 'description': post['summary'], 'pubDate': dt.datetime.strptime(post['date'], '%Y-%m-%d').strftime('%a, %d %b %Y 00:00:00 +0800')}
        for key, value in values.items():
            ET.SubElement(item, key).text = value
        for author in post['authors']:
            ET.SubElement(item, '{' + creator_ns + '}creator').text = author['name']
    write(route(lang, 'feed.xml'), ET.tostring(rss, encoding='unicode', xml_declaration=True))


def main():
    pairs = load_posts()
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / 'assets', OUT / 'assets')
    posts = {lang: [] for lang in LANGUAGES}
    for pair, refs in pairs:
        slug = pair['zh-CN'][0]['slug']
        write(f'downloads/{slug}.bib', bibliography(refs))
        write(f'downloads/{slug}-references.json', json.dumps(refs, ensure_ascii=False, indent=2) + '\n')
        for lang, (meta, source) in pair.items():
            build_article(meta, source, refs, lang)
            posts[lang].append(meta)
    for lang in LANGUAGES:
        posts[lang].sort(key=lambda post: (post['date'], post['slug']), reverse=True)
        build_home(posts[lang], lang)
        build_about(lang)
        build_feed(posts[lang], lang)
        ui = UI[lang]['error']
        body = f'<main id="main" class="container error-page"><p class="eyebrow">404</p><h1>{e(ui["heading"])}</h1><p>{e(ui["text"])}</p><a class="button" href="{path(route(lang))}">{ui["back"]}</a></main>'
        write(route(lang, '404.html'), shell(ui['title'] + ' · ' + CONFIG['name'], ui['text'], body, lang, '404.html'))
    xhtml = 'http://www.w3.org/1999/xhtml'
    ET.register_namespace('xhtml', xhtml)
    sitemap = ET.Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    relatives = ['', 'about/'] + [f"insights/{post['slug']}/" for post in posts['zh-CN']]
    for lang in LANGUAGES:
        for relative in relatives:
            url = ET.SubElement(sitemap, 'url')
            ET.SubElement(url, 'loc').text = absolute(route(lang, relative))
            for other in LANGUAGES:
                ET.SubElement(url, '{' + xhtml + '}link', rel='alternate', hreflang=other, href=absolute(route(other, relative)))
    write('sitemap.xml', ET.tostring(sitemap, encoding='unicode', xml_declaration=True))
    write('robots.txt', 'User-agent: *\nAllow: /\nSitemap: ' + absolute('sitemap.xml') + '\n')
    write('.nojekyll', '')
    print(f'Built {len(pairs)} bilingual post(s) into {OUT}')


if __name__ == '__main__':
    main()
