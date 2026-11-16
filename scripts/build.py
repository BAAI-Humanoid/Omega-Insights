#!/usr/bin/env python3
"""Build a small, file-based research blog. Only dependency: Python-Markdown."""
import datetime as dt
import html
import json
import re
import shutil
import unicodedata
from pathlib import Path
from urllib.parse import quote
import xml.etree.ElementTree as ET

import markdown

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist"
CONFIG = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
BASE = CONFIG.get("base_path", "").rstrip("/")
ORIGIN = CONFIG["url"].rstrip("/")
e = html.escape


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


def shell(title, description, body, canonical, page_class="", structured=None):
    schema = ""
    if structured:
        schema = '<script type="application/ld+json">' + json.dumps(structured, ensure_ascii=False).replace("<", "\\u003c") + "</script>"
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(description)}">
<meta name="theme-color" content="#154c44">
<link rel="canonical" href="{e(canonical)}">
<meta property="og:type" content="{'article' if structured else 'website'}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{e(canonical)}"><meta property="og:locale" content="zh_CN">
<link rel="icon" href="{path('assets/favicon.svg')}" type="image/svg+xml">
<link rel="stylesheet" href="{path('assets/style.css')}">
<link rel="alternate" type="application/rss+xml" title="{e(CONFIG['name'])}" href="{path('feed.xml')}">
{schema}
<script defer src="{path('assets/site.js')}"></script>
</head>
<body class="{page_class}">
<a class="skip-link" href="#main">跳到正文</a>
<header class="site-header"><div class="header-inner">
<a class="brand" href="{path()}"><img class="brand-mark" src="{path('assets/favicon.svg')}" alt="" width="34" height="34"><span class="brand-text">Omega <span>Insights</span></span></a>
<nav class="nav" aria-label="主导航"><a href="{path('#articles')}">文章</a><a href="{path('about/')}">关于</a><a href="{CONFIG['organization_url']}">GitHub <span aria-hidden="true">↗</span></a></nav>
</div></header>
{body}
<footer class="site-footer"><div class="footer-inner"><div><strong>Omega Insights</strong><p>Thinking through intelligence. Grounded in the physical world.</p></div><nav aria-label="页脚导航"><a href="{path('feed.xml')}">RSS 订阅</a><a href="{CONFIG['repository_url']}">网站源码 ↗</a><a href="{path('about/')}">关于本站</a></nav><small>© {dt.date.today().year} BAAI-Humanoid · 研究观察与技术讨论</small></div></footer>
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
        for field in ("booktitle", "volume", "eprint", "archivePrefix", "doi"):
            if item.get(field):
                fields[field] = clean(item[field])
        kind = item.get("type", "misc")
        if kind not in ("misc", "inproceedings", "article"):
            raise ValueError(f"Unsupported reference type: {kind}")
        result.append("@" + kind + "{" + key + ",\n" + ",\n".join(f"  {k} = {{{v}}}" for k, v in fields.items()) + "\n}")
    return "\n\n".join(result) + "\n"


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "assets", OUT / "assets")
    posts = []
    for meta_file in sorted((ROOT / "content" / "posts").glob("*.json")):
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        slug = meta["slug"]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            raise ValueError(f"Invalid slug: {slug}")
        source = meta_file.with_suffix(".md").read_text(encoding="utf-8")
        # Authors use {{BASE}} in local image URLs so project-site deployments also work.
        source = source.replace("{{BASE}}", BASE)
        refs_file = ROOT / "content" / "references" / f"{slug}.json"
        refs = json.loads(refs_file.read_text(encoding="utf-8"))
        renderer = markdown.Markdown(extensions=["extra", "toc", "sane_lists"], extension_configs={"toc": {"slugify": slugify, "toc_depth": "2-2", "permalink": False}})
        content = renderer.convert(source)
        content = content.replace("<table>", '<div class="table-scroll" role="region" aria-label="技术对照表" tabindex="0"><table>').replace("</table>", "</table></div>")
        minutes = meta.get("reading_minutes") or max(1, round(len(re.findall(r"[\u4e00-\u9fff]|\b[a-zA-Z]+\b", source)) / 330))
        meta["reading_minutes"] = minutes
        article_url = absolute(f"insights/{slug}/")
        reference_base = f"downloads/{slug}"
        write(reference_base + ".md", "# " + meta["title"] + "\n\n" + meta["subtitle"] + "\n\n" + source)
        write(reference_base + ".bib", bibliography(refs))
        write(reference_base + "-references.json", json.dumps(refs, ensure_ascii=False, indent=2) + "\n")
        authors = "、".join(meta.get("authors", ["BAAI-Humanoid"]))
        article = f'''<main id="main">
<header class="article-header container"><a class="eyebrow text-link" href="{path('#articles')}">INSIGHTS / 研究观察</a><h1 class="article-title">{e(meta['title'])}</h1><p class="article-deck">{e(meta['subtitle'])}</p><div class="article-meta"><span>{e(authors)}</span><time datetime="{meta['date']}">{meta['date']}</time><span>约 {minutes} 分钟阅读</span><span>{len(refs)} 项参考资料</span></div>{tags(meta['tags'])}</header>
<div class="article-layout container"><aside class="toc"><details class="toc-inner" open><summary>本文目录</summary>{renderer.toc.replace(chr(34) + "toc" + chr(34), chr(34) + "toc-list" + chr(34))}<a class="text-link toc-top" href="#main">返回顶部 ↑</a></details></aside><div><article class="article-body prose">{content}</article><section class="article-actions" aria-label="文章文件"><h2>继续研究</h2><p>下载正文与引用，复查原始实验，也欢迎通过 GitHub 提交补充与更正。</p><div><a class="button" download href="{path(reference_base + '.md')}">下载 Markdown</a><a class="button" download href="{path(reference_base + '.bib')}">下载 BibTeX</a><a class="button" download href="{path(reference_base + '-references.json')}">引用 JSON</a><button class="button" data-print hidden type="button">打印 / 保存 PDF</button><a class="text-link" href="{CONFIG['repository_url']}/issues/new">提出更正 ↗</a></div></section></div></div>
</main>'''
        schema = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": meta["title"], "description": meta["summary"], "inLanguage": "zh-CN", "datePublished": meta["date"], "dateModified": meta.get("updated", meta["date"]), "author": {"@type": "Organization", "name": authors, "url": CONFIG["organization_url"]}, "mainEntityOfPage": article_url, "citation": [r["url"] for r in refs]}
        write(f"insights/{slug}/index.html", shell(meta["title"] + " · " + CONFIG["name"], meta["summary"], article, article_url, "article-page", schema))
        posts.append(meta)
    posts.sort(key=lambda post: post["date"], reverse=True)
    if not posts:
        raise ValueError("No posts found")
    previews = ""
    for i, post in enumerate(posts, 1):
        previews += f'''<article class="featured-post"><div class="post-number">{i:02d}</div><div class="post-preview"><div class="hero-meta"><time datetime="{post['date']}">{post['date']}</time><span>研究观察 · {post['reading_minutes']} 分钟</span></div><h3 class="post-title"><a href="{path('insights/' + post['slug'] + '/')}">{e(post['title'])}</a></h3><p class="post-excerpt">{e(post['summary'])}</p>{tags(post['tags'])}<a class="read-link" href="{path('insights/' + post['slug'] + '/')}">阅读全文 <span aria-hidden="true">↗</span></a></div></article>'''
    home = f'''<main id="main" class="container"><section class="hero"><p class="eyebrow">OMEGA INSIGHTS / BAAI-HUMANOID</p><h1 class="hero-title">让智能<br><span>走进物理世界。</span></h1><p class="hero-deck">记录具身智能的技术进展，讨论系统选择，<br class="desktop-break">沉淀可以被实验检验的判断。</p><div class="hero-meta"><span>全身移动操作</span><span>灵巧操控</span><span>数据与学习</span></div></section><section id="articles" aria-labelledby="articles-title"><div class="section-heading"><h2 id="articles-title">研究与思考</h2><span>{len(posts):02d} 篇文章</span></div>{previews}</section><section class="research-strip" aria-label="研究关注"><div><span class="eyebrow">01 / CONTROL</span><h2>与物理世界交互</h2><p>在运动、接触与扰动中，建立可靠的全身控制和操作能力。</p></div><div><span class="eyebrow">02 / SYSTEMS</span><h2>让系统协同工作</h2><p>理解规划、动作与反馈的接口，把单次演示推进到稳定执行。</p></div><div><span class="eyebrow">03 / DATA</span><h2>让经验进入下一轮学习</h2><p>连接数据采集、训练与实机评测，让每次失败都能留下可用的证据。</p></div></section></main>'''
    write("index.html", shell(CONFIG["name"], CONFIG["description"], home, absolute()))
    about = f'''<main id="main" class="container"><header class="article-header"><p class="eyebrow">ABOUT / 关于</p><h1 class="article-title">从研究问题，<br>到物理世界里的答案。</h1><p class="article-deck">Omega Insights 是 BAAI-Humanoid 的技术观察与讨论空间。</p></header><div class="prose about-grid"><section><h2>我们关注什么</h2><p>根据团队在 <a href="{CONFIG['organization_url']}">GitHub 组织主页</a>公开的研究方向，我们关注人形机器人的全身移动操作：协调运动与操作、接触丰富的全身控制、双臂与灵巧操作、遥操作和数据，以及仿真到真实部署。</p><p>本站记录公开技术路线的梳理、系统设计的取舍，以及值得进一步验证的问题。</p></section><section><h2>如何阅读这些文章</h2><p>我们尽量将公开事实、厂商报告的实验结果和自己的判断分开呈现。数值应结合原文中的任务、数据与评测设置理解；不同公司的演示不能直接构成统一排行榜。</p><p>文章包含逐项引用、资料范围和核验日期。若后续出现新证据，我们将通过 Git 保留修订记录。</p></section><section><h2>引用与更正</h2><p>每篇技术长文提供 Markdown、BibTeX 和结构化参考资料下载。BibTeX 为原始资料的引用条目；网页资料与学术论文会保持各自身份。</p><p>欢迎在<a href="{CONFIG['repository_url']}/issues/new">网站仓库提出更正</a>，也欢迎提交有来源的补充。</p></section></div></main>'''
    write("about/index.html", shell("关于 · " + CONFIG["name"], CONFIG["description"], about, absolute("about/")))
    write("404.html", shell("页面未找到 · " + CONFIG["name"], "页面未找到", f'<main id="main" class="container error-page"><p class="eyebrow">404</p><h1>这条路径还没有留下足迹。</h1><p>你可以回到首页，继续阅读我们的研究与思考。</p><a class="button" href="{path()}">返回首页</a></main>', absolute("404.html")))
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    for key, value in {"title": CONFIG["name"], "link": absolute(), "description": CONFIG["description"], "language": "zh-CN"}.items():
        ET.SubElement(channel, key).text = value
    for post in posts:
        item = ET.SubElement(channel, "item")
        url = absolute(f"insights/{post['slug']}/")
        values = {"title": post["title"], "link": url, "guid": url, "description": post["summary"], "pubDate": dt.datetime.strptime(post["date"], "%Y-%m-%d").strftime("%a, %d %b %Y 00:00:00 +0800")}
        for key, value in values.items():
            ET.SubElement(item, key).text = value
    write("feed.xml", ET.tostring(rss, encoding="unicode", xml_declaration=True))
    sitemap = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for value in ["", "about/"] + [f"insights/{post['slug']}/" for post in posts]:
        ET.SubElement(ET.SubElement(sitemap, "url"), "loc").text = absolute(value)
    write("sitemap.xml", ET.tostring(sitemap, encoding="unicode", xml_declaration=True))
    write("robots.txt", "User-agent: *\nAllow: /\nSitemap: " + absolute("sitemap.xml") + "\n")
    write(".nojekyll", "")
    print(f"Built {len(posts)} post(s) into {OUT}")


if __name__ == "__main__":
    main()
