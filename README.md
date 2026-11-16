# Omega Insights

BAAI-Humanoid 关于具身智能、全身移动操作与物理世界学习的技术博客。

- 仓库：[BAAI-Humanoid/Omega-Insights](https://github.com/BAAI-Humanoid/Omega-Insights)
- 网站：<https://baai-humanoid.github.io/Omega-Insights/>（首次部署成功后可用）
- English: <https://baai-humanoid.github.io/Omega-Insights/en/>
- 首篇文章：**通用模型越强，具身团队越该做什么？**

## 首次启用 GitHub Pages

1. 将本仓库的文件推送到 `main`，包括隐藏目录 `.github/`。
2. 在仓库 [Settings → Pages](https://github.com/BAAI-Humanoid/Omega-Insights/settings/pages) 的 **Build and deployment → Source** 中选择 **GitHub Actions**。
3. 在 [Actions → Build and deploy Insights](https://github.com/BAAI-Humanoid/Omega-Insights/actions/workflows/pages.yml) 查看构建与部署。若首次 push 发生在启用 Pages 之前，设置完成后选择 **Run workflow** 或重新运行失败的部署。
4. 部署成功后访问 <https://baai-humanoid.github.io/Omega-Insights/>。

这是项目网站，无需将仓库命名为组织根网站。`site.json` 的 `url` 为 `https://baai-humanoid.github.io`，`base_path` 为 `/Omega-Insights`；页面、资源、RSS、引用下载与站点地图均从配置生成。

可以在组织的 `.github/profile/README.md` 加上入口：

```md
## Omega Insights

[阅读我们的技术观察与思考](https://baai-humanoid.github.io/Omega-Insights/)
```

## 本地预览

需要 Python 3.9+；CI 使用 Python 3.12。浏览器端没有框架或 CDN 依赖。

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/build.py
.venv/bin/python scripts/check_site.py
.venv/bin/python scripts/preview.py
```

打开 <http://127.0.0.1:8000/Omega-Insights/>。预览脚本会按项目路径提供页面；不能直接双击 HTML，或仅在根目录用 `http.server` 预览。Windows 将 `.venv/bin/python` 换成 `.venv\Scripts\python.exe`。修改文章后重新执行 build。

## 新增文章

在 `content/posts/` 增加同名 `.md` 与 `.json` 文件，在 `content/references/` 增加对应引用清单。详细格式见 [CONTRIBUTING.md](CONTRIBUTING.md)。

每篇文章同时提供中文和完整英文版本：中文保存在 `content/posts/`，英文保存在 `content/posts/en/`，两者使用相同文件名和 `slug`。共用一份引用 JSON，脚注 ID 与来源保持一致。页头的 **中文 / EN** 按钮会切换到当前页面的另一语言版本，首页、关于页、文章、RSS 与 Markdown 下载均按语言生成；不依赖浏览器 JavaScript 即可切换。

```sh
git switch -c post/your-topic
# 编辑文章、元数据与引用
.venv/bin/python scripts/build.py
.venv/bin/python scripts/check_site.py
git add content assets
git commit -m "Add insight on your topic"
git push -u origin post/your-topic
```

随后在 GitHub 创建 PR。PR 自动检查；合并到 `main` 后自动发布。也可以在 GitHub 网页编辑 Markdown 并提交 PR。

```text
content/posts/           文章 Markdown + 元数据 JSON
content/posts/en/        对应的完整英文文章和元数据
content/references/      每篇文章的结构化引用
content/ui/              中英文界面文案
assets/                  样式、渐进增强脚本、原创示意图
scripts/build.py         生成文章、目录、首页、下载、RSS、站点地图
scripts/check_site.py    检查本地链接、锚点、脚注和引用完整性
scripts/preview.py       按项目路径提供本地预览
.github/workflows/       PR 检查 + main 自动发布
dist/                    生成产物，不提交 Git
```

## 引用与内容范围

首篇基于 2026 年 9 月 24 日分享材料，2026 年 11 月 16 日整理并核验引用。它讨论指定版本的技术路线，并非当前最新模型清单。外部实验数字保留任务和评测边界；团队建议不代表已经完成的内部实验。

每篇文章自动导出 Markdown、BibTeX 与 JSON 引用。BibTeX 对应原始来源；未公开的作者、日期、DOI 不会补造。官网博客不标作同行评审论文。

中文 Markdown 下载保留原文件名，英文使用 `.en.md`；BibTeX 与引用 JSON 由两个语言版本共用。英文图示使用 `-en.svg`，保持与中文图示相同的技术含义。

许可见仓库已有的 [Apache-2.0 LICENSE](LICENSE)。引用的第三方资料归其权利人所有；图示为本站原创技术示意。

## 官方部署文档

- [GitHub Pages 与项目网站](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)
- [使用 GitHub Actions 发布 Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
