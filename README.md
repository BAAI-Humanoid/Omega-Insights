# Omega Insights

BAAI-Humanoid's technical blog on embodied intelligence, whole-body mobile manipulation, and learning in the physical world.

- Repository: [BAAI-Humanoid/Omega-Insights](https://github.com/BAAI-Humanoid/Omega-Insights)
- Chinese edition: <https://baai-humanoid.github.io/Omega-Insights/>
- English edition: <https://baai-humanoid.github.io/Omega-Insights/en/>
- First essay: [As General-Purpose Models Get Stronger, What Should Embodied AI Teams Build?](https://baai-humanoid.github.io/Omega-Insights/en/insights/embodied-intelligence-physical-loop/), by **Zhenguo Sun**.

## GitHub Pages setup

The site is live. The following steps document the initial configuration for maintainers:

1. Push the repository files to `main`, including the hidden `.github/` directory.
2. In [Settings → Pages](https://github.com/BAAI-Humanoid/Omega-Insights/settings/pages), set **Build and deployment → Source** to **GitHub Actions**.
3. Check the build and deployment under [Actions → Build and deploy Insights](https://github.com/BAAI-Humanoid/Omega-Insights/actions/workflows/pages.yml). If the first push occurred before Pages was enabled, select **Run workflow** or rerun the failed deployment after completing setup.
4. Once deployment succeeds, visit <https://baai-humanoid.github.io/Omega-Insights/>.

This is a project site; the repository does not need the organization's root-site name. In `site.json`, `url` is `https://baai-humanoid.github.io` and `base_path` is `/Omega-Insights`. Pages, assets, RSS feeds, reference downloads, and the sitemap use this configuration.

To add an entry on the organization's GitHub profile, include the following in `.github/profile/README.md`:

```md
## Omega Insights

[Read our research perspectives and technical discussions](https://baai-humanoid.github.io/Omega-Insights/en/)
```

## Local preview

Requires Python 3.9 or later; CI uses Python 3.12. The browser frontend has no framework or CDN dependencies.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/build.py
.venv/bin/python scripts/check_site.py
.venv/bin/python scripts/preview.py
```

Open <http://127.0.0.1:8000/Omega-Insights/>. The preview script serves the configured project path. Opening HTML files directly or serving `dist/` at the root with a plain `http.server` will not reproduce that path correctly. On Windows, replace `.venv/bin/python` with `.venv\Scripts\python.exe`. Rebuild after editing an article.

## Adding an article

Add matching `.md` and `.json` files under `content/posts/`, with a reference list under `content/references/`. See [CONTRIBUTING.md](CONTRIBUTING.md) for the detailed format.

Each article has a complete Chinese and English edition. Chinese files live in `content/posts/`; English files live in `content/posts/en/`. Both editions use the same filename and `slug`, and share a reference JSON file with matching footnote IDs and source URLs. Author display names may be localized, while stable author IDs identify the same person across editions.

The language selector switches to the corresponding version of the current page. Home pages, About pages, articles, RSS feeds, and Markdown downloads are generated for each language. Language switching works without browser JavaScript.

```sh
git switch -c post/your-topic
# Edit the article, metadata, and references.
.venv/bin/python scripts/build.py
.venv/bin/python scripts/check_site.py
git add content assets
git commit -m "Add insight on your topic"
git push -u origin post/your-topic
```

Then open a pull request on GitHub. Pull requests run automated checks; merging into `main` publishes the site automatically. You can also edit Markdown in GitHub's web interface and submit a pull request there.

```text
content/posts/           Chinese articles and metadata
content/posts/en/        Complete English articles and metadata
content/references/      Shared structured references for each article
content/ui/              Chinese and English interface text
assets/                  Styles, progressive enhancement, and original diagrams
scripts/build.py         Builds pages, contents lists, downloads, RSS, and sitemap
scripts/check_site.py    Checks language links, anchors, footnotes, and references
scripts/preview.py       Serves a local preview under the project path
.github/workflows/       Pull request checks and automatic deployment from main
dist/                    Generated output; not committed to Git
```

## Citations and editorial scope

The first essay, by Zhenguo Sun, is based on an **internal team discussion on embodied AI held on September 24, 2026**. It was published on November 16, 2026, when its reference links were also checked. It examines the selected model versions and is not a list of the latest releases. Reported results retain their task and evaluation context; proposed research priorities do not imply that the team has already completed those experiments.

Each article ends with a **Cite this article** section and a separate BibTeX download for citing the blog post itself. This is distinct from the downloadable **reference bibliography**, which contains the external sources cited by the article. The blog's citation identifies its author, title, publication date, and stable URL.

Articles also provide Markdown, BibTeX reference bibliographies, and structured reference JSON. Undisclosed author names, dates, and DOIs are not invented, and company blog posts are not described as peer-reviewed papers.

Chinese Markdown downloads retain the original filename; English downloads use `.en.md`. Both editions share the external reference bibliography and reference JSON. English diagrams use `-en.svg` and preserve the technical meaning of their Chinese counterparts.

See the repository's existing [Apache-2.0 LICENSE](LICENSE). Third-party source material remains the property of its respective rights holders; the technical diagrams are original illustrations for this site.

## Official deployment documentation

- [GitHub Pages and project sites](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)
- [Publishing Pages with GitHub Actions](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
