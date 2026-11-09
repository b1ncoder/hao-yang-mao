# 薅羊毛公开页 · 模块结构（2026-11-09 改版）

线上地址：https://freenofree.ct.ws/（InfinityFree，/htdocs）
本地底本：`~/workspace/goals/pro/pages/`（唯一底本，GitHub Pages 自 2026-11-09 起暂停同步）

## 构建流程（2026-11-09 SSR + bundle 改版后，必读）

首页是**静态预渲染**的：`index.html` 是生成物，内容（新闻、X 快照、栏目表、视频、归档、统计）已直接写在 HTML 里，不开 JS 也能看；JS 只负责搜索、时段切换、统计重算。

- **改页面结构** → 改 `index.template.html`（模板），不要直接改 `index.html`。
- **改任何 `data/*.js`** → 改完必须跑 `python3 build-static.py`，它会：繁简转简体 → 重新生成 `index.html` → 合并 `data/*.js` + `app.js` 成 `bundle.js`（首页唯一加载的脚本，带 `?v=<stamp>`）→ 刷新 `feed.xml` / `sitemap.xml`。
- **同步到线上** → 只传 `bundle.js` + `index.html`（+ 改过的 `style.css` / `.htaccess` / `robots.txt` 等静态文件）。**只传数据文件不会更新页面内容**，因为内容已经在 `index.html` 里了。
- 自愈：`bundle.js` 开头的 `window.SITE_BUILD.stamp` 与首页 `<body data-build>` 是同一值；两者不一致时 `app.js` 会用 bundle 里的数据强制重渲染，防止“只传了 bundle、没传首页”导致页面停留在旧内容。

## 文件分工：改哪里，就只传哪里

| 文件 | 内容 | 什么时候改 | 同步时只传这个文件 |
| --- | --- | --- | --- |
| `index.template.html` | 首页模板（外壳） | 栏目增减、改版、改备注 | 改完跑构建，传生成的 `index.html` |
| `index.html` | 生成的首页（静态内容已写进 HTML） | 由构建生成，不要手改 | `/htdocs/index.html`（每次构建后都传） |
| `bundle.js` | 生成物：全部数据文件 + `app.js` 合一 | 由构建生成，不要手改 | `/htdocs/bundle.js`（每次构建后都传） |
| `build-static.py` | 构建脚本 | 改构建逻辑 | 不上传 |
| `style.css` | 全部样式 | 改样式 | `/htdocs/style.css` |
| `app.js` | 渲染 + 统计 + 时段切换 + 搜索 | 改交互逻辑 | `/htdocs/app.js` |
| `data/news.js` | 最新科技新闻（10 条） | 新闻 3 小时刷新 | 改完跑构建，传 `bundle.js` + `index.html` |
| `data/x.js` | X 新闻 / X 羊毛小时快照（各留 12 小时） | X 每小时搜集 | 改完跑构建，传 `bundle.js` + `index.html` |
| `data/sec-pro.js` | Pro 活动表 | Pro 搜集有变化 | 改完跑构建，传 `bundle.js` + `index.html` |
| `data/sec-domain.js` | 免费域名表 | 域名栏目有变化 | 改完跑构建，传 `bundle.js` + `index.html` |
| `data/sec-ai.js` | AI 免费额度表 | AI 栏目有变化 | 改完跑构建，传 `bundle.js` + `index.html` |
| `data/sec-cloud.js` | 大云试用金表 | 大云栏目有变化 | 改完跑构建，传 `bundle.js` + `index.html` |
| `data/sec-esim.js` | 免费 eSIM 表 | eSIM 栏目有变化 | 改完跑构建，传 `bundle.js` + `index.html` |
| `data/sec-student.js` | 学生福利表 | 学生栏目有变化 | 改完跑构建，传 `bundle.js` + `index.html` |
| `data/sec-server.js` | 免费服务器表 | 服务器栏目有变化 | 改完跑构建，传 `bundle.js` + `index.html` |
| `data/sec-videos.js` | 频道视频卡片 | 新增视频 | 改完跑构建，传 `bundle.js` + `index.html` |
| `data/sec-archive.js` | 已过期归档 | 活动过期归档 | 改完跑构建，传 `bundle.js` + `index.html` |
| `.htaccess` | 缓存头（index `no-cache`、data 5 分钟）+ 安全头 + 强制 HTTPS + 404 | 改缓存/安全策略 | `/htdocs/.htaccess`（InfinityFree 前端可能覆盖响应头，上线后须 curl -I 复核） |
| `robots.txt` / `sitemap.xml` / `404.html` / `feed.xml` / `og.png` | 爬虫与分享文件（RSS 由新闻 + Pro 生成） | 改版 / 新闻更新后顺手刷新 feed | `/htdocs/` 对应位置 |
| `convert-t2s.py` | 繁简转换（OpenCC） | 构建脚本内部已调用，单独跑也行 | 只放本地，不上传 |
| `OPTIMIZATION-NOTES.md` | 2026-11-09 三份外部优化建议的核查与处理记录 | 有新建议时更新 | 只放本地，不上传 |

**“最后更新”由构建脚本从 `data/news.js` 的 `updated` 日期写进首页，不要再手写日期。** `bundle.js` 引用带 `?v=<stamp>`（构建自动生成，每次构建都变），`style.css` 引用带 `?v=YYYYMMDD`，改版时同步改版本号，否则老访客拿旧版。

**不要再只传数据文件。** 各数据文件仍是本地唯一底本、互相独立，一个栏目想单独拿出来用，直接取它的 `data/sec-*.js` 即可（配合 `app.js` 里的渲染函数）；但线上页面内容在 `index.html` 里，改数据后必须跑构建并传 `bundle.js` + `index.html`。

## 数据格式

所有数据文件都是 `window.XXX = {...};` 的 JS 文件（不用 fetch，纯静态托管可用），内容是 JSON。写文件时注意 JSON 转义（标题里的引号、反斜杠要转义），写完用 `node --check <文件>` 检查语法。

- `data/news.js`：`{"updated": "2026-11-09 08:30", "items": [{"t": 标题, "u": 原文链接, "s": 来源, "d": "MM-DD HH:MM", "zh": 中文翻译（仅英文条目有）}]}`
- `data/x.js`：`{"news": [{"hour": "YYYY-MM-DD HH:00", "rows": [{"topic", "desc", "time": "MM-DD", "url", "label"}]}], "wool": [{"hour", "rows": [{"post", "content", "author", "status": "已验证"|"未核实"|"免费已结束", "statusClass": "ok"|"wait"|"dead", "note": "限制说明（仅已验证行有）", "url", "label": "看原帖"|"看来源"}]}]}`，快照最新在前；每栏每小时最多 10 条（不够不硬凑，重复可收）；某小时羊毛无新线索时 `rows: []`。
- `data/sec-*.js`（表）：`{"rows": [[单元格, 单元格, ...], ...]}`，每行 4 个单元格。单元格是纯文字字符串，或对象 `{"t": 文字, "u": 链接, "tag": {"text": 标签, "cls": "ok"|"wait"|"dead"|"watch"|"limit"}, "bad": true}`（`bad` 的是红字限制）。第一列自动加粗，`tag` 显示在第一列文字后面。
- `data/sec-videos.js`：`{"items": [{"id": "YouTube 视频 ID", "t": 标题, "u": 视频链接, "d": 一句话介绍}]}`（缩略图由 `id` 自动拼 `i.ytimg.com`）。
- `data/sec-archive.js`：`{"items": [{"t": 标题, "tag": {"text", "cls"}, "d": 说明}]}`。

## 渲染与统计

首页内容已由构建静态写进 HTML；`bundle.js`（数据 + `app.js`）加载后只做 hydration：内容已在就跳过渲染（stamp 不一致时强制重渲染），然后接线时段切换、搜索，自动重算统计卡（栏目按表行数、X 按可见快照行数）。X 两区时段切换是**各管各的**（点哪个区的标签只切本区）。

## 回滚

`index.html.2026-11-09.bak` 是拆分前的单文件旧版（38,963 字节）。SSR 出问题时：先跑 `python3 build-static.py` 重新生成；仍不行就把 `index.template.html` 当 `index.html` 传上去（回到 JS 渲染版，但要把模板里的 bundle 脚本换回 12 个数据脚本）或直接传本 bak 文件回滚。

## 备份（GitHub backup 分支，2026-11-09 建）

- 备份位置：GitHub 仓库 `b1ncoder/hao-yang-mao` 的 **`backup` 分支**（2026-11-09 从 main 建出），**绝不推 main**——main 仍是冻结的旧单文件版，GitHub Pages 暂停同步的状态不变。
- 备份内容：本目录的整站文件（`index.html`、`index.template.html`、`build-static.py`、`bundle.js`、`style.css`、`app.js`、`data/*.js` 共 11 个、`.htaccess`、`robots.txt`、`sitemap.xml`、`404.html`、`feed.xml`、`og.png`、`README.md`、`OPTIMIZATION-NOTES.md`、`split-page.py`、`split-sections.py`、`push-page.py`、`backup-push.py`），一次快照一个 commit。
- 备份脚本：`backup-push.py`（用法：`python3 backup-push.py ["commit message"]`）。无变化时自动跳过；每次成功后把 commit SHA 记到 `~/workspace/goals/pro/pages.muse-github-snapshot-sync.json`。**backup 分支只由这个脚本写，不要在 GitHub 网页上直接改它**，否则下次快照会覆盖。
- 每次更新后的流程：先跑 `build-static.py`，再同步 InfinityFree（传 `bundle.js` + `index.html`），再跑 `backup-push.py` 同步备份分支。四个定时任务（新闻 3 小时、X 每小时、早晚 Pro 搜集）正文里都有这一条。
- 恢复：从 `backup` 分支拉下文件，按上表传到新主机的对应位置即可；`index.html.2026-11-09.bak` 不在备份分支里（main 分支上的旧单文件版就是它）。

## 本地验证

`node --check app.js data/*.js bundle.js` 检查语法；构建后跑 `python3 build-static.py`，再用 jsdom 抽查：无 JS 时首页应有全部内容（新闻 10 条、服务器表 10 行），带 bundle 加载后计数不变、搜索与时段切换正常（抽查脚本见 OPTIMIZATION-NOTES.md）。
