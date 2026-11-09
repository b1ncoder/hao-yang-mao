# 薅羊毛公开页 · 模块结构（2026-11-09 改版）

线上地址：https://freenofree.ct.ws/（InfinityFree，/htdocs）
本地底本：`~/workspace/goals/pro/pages/`（唯一底本，GitHub Pages 自 2026-11-09 起暂停同步）

## 文件分工：改哪里，就只传哪里

| 文件 | 内容 | 什么时候改 | 同步时只传这个文件 |
| --- | --- | --- | --- |
| `index.html` | 外壳：头部、导航、统计卡、搜索框、各栏目结构（表头、备注）、页脚 | 栏目增减、改版、改备注 | `/htdocs/index.html` |
| `style.css` | 全部样式 | 改样式 | `/htdocs/style.css` |
| `app.js` | 渲染 + 统计 + 时段切换 + 搜索 | 改交互逻辑 | `/htdocs/app.js` |
| `data/news.js` | 最新科技新闻（10 条） | 新闻 3 小时刷新 | `/htdocs/data/news.js` |
| `data/x.js` | X 新闻 / X 羊毛小时快照（各留 12 小时） | X 每小时搜集 | `/htdocs/data/x.js` |
| `data/sec-pro.js` | Pro 活动表 | Pro 搜集有变化 | `/htdocs/data/sec-pro.js` |
| `data/sec-domain.js` | 免费域名表 | 域名栏目有变化 | `/htdocs/data/sec-domain.js` |
| `data/sec-ai.js` | AI 免费额度表 | AI 栏目有变化 | `/htdocs/data/sec-ai.js` |
| `data/sec-cloud.js` | 大云试用金表 | 大云栏目有变化 | `/htdocs/data/sec-cloud.js` |
| `data/sec-esim.js` | 免费 eSIM 表 | eSIM 栏目有变化 | `/htdocs/data/sec-esim.js` |
| `data/sec-student.js` | 学生福利表 | 学生栏目有变化 | `/htdocs/data/sec-student.js` |
| `data/sec-server.js` | 免费服务器表 | 服务器栏目有变化 | `/htdocs/data/sec-server.js` |
| `data/sec-videos.js` | 频道视频卡片 | 新增视频 | `/htdocs/data/sec-videos.js` |
| `data/sec-archive.js` | 已过期归档 | 活动过期归档 | `/htdocs/data/sec-archive.js` |

**不要再整站传 index.html。** 各数据文件互相独立，一个栏目想单独拿出来用，直接取它的 `data/sec-*.js` 即可（配合 `app.js` 里的渲染函数）。

## 数据格式

所有数据文件都是 `window.XXX = {...};` 的 JS 文件（不用 fetch，纯静态托管可用），内容是 JSON。写文件时注意 JSON 转义（标题里的引号、反斜杠要转义），写完用 `node --check <文件>` 检查语法。

- `data/news.js`：`{"updated": "2026-11-09 08:30", "items": [{"t": 标题, "u": 原文链接, "s": 来源, "d": "MM-DD HH:MM", "zh": 中文翻译（仅英文条目有）}]}`
- `data/x.js`：`{"news": [{"hour": "YYYY-MM-DD HH:00", "rows": [{"topic", "desc", "time": "MM-DD", "url", "label"}]}], "wool": [{"hour", "rows": [{"post", "content", "author", "status": "待核实"|"免费已结束", "statusClass": "wait"|"dead", "url", "label": "看原帖"}]}]}`，快照最新在前；某小时羊毛无新帖时 `rows: []`。
- `data/sec-*.js`（表）：`{"rows": [[单元格, 单元格, ...], ...]}`，每行 4 个单元格。单元格是纯文字字符串，或对象 `{"t": 文字, "u": 链接, "tag": {"text": 标签, "cls": "ok"|"wait"|"dead"|"watch"|"limit"}, "bad": true}`（`bad` 的是红字限制）。第一列自动加粗，`tag` 显示在第一列文字后面。
- `data/sec-videos.js`：`{"items": [{"id": "YouTube 视频 ID", "t": 标题, "u": 视频链接, "d": 一句话介绍}]}`（缩略图由 `id` 自动拼 `i.ytimg.com`）。
- `data/sec-archive.js`：`{"items": [{"t": 标题, "tag": {"text", "cls"}, "d": 说明}]}`。

## 渲染与统计

`app.js` 按顺序加载各数据文件后渲染：新闻 → X 两区 → 各栏目表 → 视频 → 归档，然后自动重算统计卡（栏目按表行数、X 按可见快照行数）。X 两区时段切换是**各管各的**（点哪个区的标签只切本区）。

## 回滚

`index.html.2026-11-09.bak` 是拆分前的单文件旧版（38,963 字节）。模块版出问题时，把它当 `index.html` 传上去即回滚。

## 备份（GitHub backup 分支，2026-11-09 建）

- 备份位置：GitHub 仓库 `b1ncoder/hao-yang-mao` 的 **`backup` 分支**（2026-11-09 从 main 建出），**绝不推 main**——main 仍是冻结的旧单文件版，GitHub Pages 暂停同步的状态不变。
- 备份内容：本目录的整站文件（`index.html`、`style.css`、`app.js`、`data/*.js` 共 11 个、`README.md`、`split-page.py`、`split-sections.py`、`push-page.py`、`backup-push.py`），一次快照一个 commit。
- 备份脚本：`backup-push.py`（用法：`python3 backup-push.py ["commit message"]`）。无变化时自动跳过；每次成功后把 commit SHA 记到 `~/workspace/goals/pro/pages.muse-github-snapshot-sync.json`。**backup 分支只由这个脚本写，不要在 GitHub 网页上直接改它**，否则下次快照会覆盖。
- 每次更新后的流程：先同步 InfinityFree（只传改动的文件），再跑 `backup-push.py` 同步备份分支。四个定时任务（新闻 3 小时、X 每小时、早晚 Pro 搜集）正文里都有这一条。
- 恢复：从 `backup` 分支拉下文件，按上表传到新主机的对应位置即可；`index.html.2026-11-09.bak` 不在备份分支里（main 分支上的旧单文件版就是它）。

## 本地验证

`node --check app.js data/*.js` 检查语法；`/tmp/domtest/test-page.js` 是 jsdom 自动化检查（渲染、切换、搜索、统计共 33 项）。
