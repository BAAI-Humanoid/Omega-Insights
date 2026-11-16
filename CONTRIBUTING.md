# 写作与更新

## 新增一篇文章

1. 建立中文 `content/posts/your-slug.md` 和完整英文 `content/posts/en/your-slug.md`，从 `##` 开始写章节；页面的大标题由元数据生成。Markdown 支持表格、代码、脚注。
2. 建立同名 `content/posts/your-slug.json`：

   ```json
   {
     "slug": "your-slug",
     "title": "文章标题",
     "subtitle": "一句话说明问题和视角",
     "summary": "首页显示的摘要",
     "date": "2026-11-16",
     "updated": "2026-11-16",
     "authors": ["BAAI-Humanoid"],
     "tags": ["技术观察", "具身智能"]
   }
   ```

   同时建立 `content/posts/en/your-slug.json`，翻译 `title`、`subtitle`、`summary` 和 `tags`，保持 `slug`、`date`、`authors` 与中文一致。`updated` 可以记录各语言的实际修订日期。构建会检查中英文文件是否配对，避免语言按钮落到不存在的文章。

3. 建立 `content/references/your-slug.json`，没有外部资料时填 `[]`。每项格式：

   ```json
   [
     {
       "id": "source-key",
       "title": "来源标题",
       "organization": "作者或机构",
       "url": "https://example.org/original-source",
       "published": "2026-09-01",
       "accessed": "2026-11-16"
     }
   ]
   ```

   不知道发布日期就省略 `published`。在正文用 `[^source-key]`，末尾写：

   ```md
   [^source-key]: 机构. [来源标题](https://example.org/original-source). 核验日期：2026-11-16.
   ```

   两种语言共用这份引用清单。脚注 ID、定义顺序和原始 URL 保持一致，脚注中的说明文字分别使用中文与英文。脚注 ID 必须与 JSON 的 `id` 相同。每个事实附近放引用，不只在文末列网址。多次引用同一来源可复用 ID。

4. 图片放在 `assets/`，用 `![有意义的替代文本]({{BASE}}/assets/your-figure.svg)` 引用。有文字的图示提供对应 `your-figure-en.svg`，并翻译英文正文中的图注、替代文本与辅助标签。图注要说明是原创示意、改绘还是引用；引用图片需核实授权。
5. 运行 `python scripts/build.py` 与 `python scripts/check_site.py`，用 `python scripts/preview.py` 检查桌面和手机阅读体验，并验证首页、关于页、文章的双向语言切换。提交分支并创建 PR；合并到 `main` 自动发布。

中文沿用 `/Omega-Insights/` 与 `/Omega-Insights/insights/your-slug/`；英文对应 `/Omega-Insights/en/` 与 `/Omega-Insights/en/insights/your-slug/`。无需手工编写切换链接、目录、RSS、语言标记或站点地图，它们由构建器生成。界面翻译集中维护在 `content/ui/zh-CN.json` 与 `content/ui/en.json`。

## 内容约定

- 交代资料范围、成文日期与来源核验日期。固定发布页优于不断更新的产品首页。
- 区分公开技术事实、厂商自己的实验、作者推断与团队行动建议。
- 实验结果同时记录任务、样本、数据来源和评测条件。不把“未见场景”改写成“未见任务”，不把动作采样频率当作模型推理频率。
- 使用原始论文、官方模型说明或项目页面作为技术事实来源；媒体材料明确标注二手信息。
- 只写已公开或已获作者确认可公开的组织信息。不要把拟开展的实验写成已有成果。
- 更正现有文章时更新 `updated`，重要实质修订在正文写简短修订说明。Git 历史保留变更。
