# freenofree 优化核查记录（2026-11-09）

三份外部 AI 建议逐条核实后的处理结果。本文件只放本地，不上传到 /htdocs。

## 已核实属实、当天已改并已上线

- **缓存 30 天**：三份报告一致，`Cache-Control: max-age=2592000`。已加 `.htaccess`（index.html `no-cache`、data/*.js `max-age=300`、css/js `max-age=86400`），style.css / app.js 引用加 `?v=20261109`。注意：InfinityFree 前端是 openresty，可能覆盖 .htaccess 头——上线后须用 curl -I 复核，若无效则改走“文件名/查询串带版本”路线。
- **导航锚点被 sticky 导航挡住**：属实（#pro 标题顶 21px < 导航底 46px）。已加 `scroll-padding-top: 56px` + `scroll-margin-top` + `prefers-reduced-motion`。
- **纯前端渲染、爬虫看空壳**：属实（无 JS 时正文 0 条；GPTBot 拿的是 JS 挑战页）。当天晚些时候已做 SSR（见下文“已做”）：内容直接写进 HTML，`<noscript>` 文案也随之改成“不开 JS 也能看”。另补了 RSS `feed.xml`、JSON-LD、sitemap/robots/canonical/og:image。
- **12 个 JS、无 defer、HTTP/1.1**：属实（14 请求、load 约 1.4s）。当晚已合并成 1 个 `bundle.js`（见下文“已做”），首页只加载它。
- **繁简混排**：属实，news.js / x.js 的 `zh` 字段是繁体。已用 OpenCC t2s 全量转简体，并留了 `convert-t2s.py` 供新闻 / X cron 写完数据后跑一遍。
- **Cloady 规格写法误导**：半属实。官网免费档确是 0.5核 / 1GB / 5GB / 每月 10GB 出站；站里“只有 0.3核 / 256MB”是 Eric 面板实测值，被写进了限制栏、没区分。已改成“官方免费档 0.5核/1GB/5GB”+“面板实测 0.3核/0.3G、应用限 250m/256MB，以面板为准”。
- **Oracle Always Free 缩水**：属实。2026-06-15 起 A1 由 4 OCPU / 24GB 下调至 2 OCPU / 12GB（1500 OCPU-h + 9000 GB-h/月），8 月 18 日起超限实例停用/删除；2 台 AMD 微型 + 200GB 存储未变。sec-server.js 与 sec-cloud.js 均已改成 2/12 并注明下调时间。
- **“每条都链向官网”不实**：属实。服务器栏 10 条只有 2 条有链接（AI 栏 3 条、域名栏 1 条无链接）。已补齐服务器栏 8 条 + eu.org 的官网链接；FreeLLMAPI / DeepSeek 路由 / Radium 三条无单一官网链接（聚合类 / 待核实），页眉页脚文案已改成“有官网链接的都链向官网；聚合类与待核实条目暂无单一官网链接”。
- **搜索 bug**：属实。搜完切时段，隐藏快照的行仍被 inline `display:none` 压住。已修：`showXHour` 重置展示快照的行内样式；搜索改为全量搜（含隐藏快照，命中后留对应时段）、150ms 节流、关键词进 `#q=`、结果区 `aria-live`。
- **对比度**：属实，`#9ca3af` 约 2.6:1。footer / `.news-meta` / `.news-updated` 已改 `#6b7280`（约 4.6:1）。
- **缺 favicon / robots / sitemap / canonical / og:image / twitter:card**：属实。已补：内联 SVG favicon、robots.txt、sitemap.xml、404.html、canonical、og:image（自制 1200×630 `og.png`）+ twitter 大卡、JSON-LD（WebSite）、RSS。
- **缺安全头、http 不跳 https、URL 不校验**：属实。已加 `.htaccess`（HSTS 除外——InfinityFree 免费档未必支持，待复核；X-Content-Type-Options / Referrer-Policy / X-Frame-Options / 强制 HTTPS 已写），`app.js` 新增 `safeUrl()` 只放行 http(s)。
- **视频缩略图无尺寸、hqdefault 4:3**：属实。已加 `width/height` + `srcset`（mq/hq/maxres）+ CSS `aspect-ratio: 16/9` + `preconnect i.ytimg.com`。
- **手机统计卡占首屏、导航截断**：属实。≤600px 时统计卡改 3 列、padding 收小；导航加右侧渐隐提示可横滑。
- **表格语义 / 可访问性**：部分属实。X 区表头确在 tbody 里、无 scope；已改成 thead/tbody + `scope="col"` + 视觉隐藏 caption；时段按钮加 `aria-pressed`；搜索框 focus 改 `:focus-visible`。
- **数据文件带缩进空白**：属实（x.js 25KB）。已全部压成 compact JSON（x.js → 约 19.5KB）。
- **“最后更新”三处不一致**：属实（页眉/页脚写死 2026-11-09，news.js 是 14:30）。已改成由 `news.js` 的 `updated` 日期动态渲染。
- **深色模式**：已加 `@media (prefers-color-scheme: dark)` 基础覆盖。
- **外链 nofollow**：只对 X 羊毛栏“未核实 / 已结束”行加 `nofollow`；已验证的官方链接保持普通外链。

## 核实后不属实 / 不用改的

- **“x.js 只有 8 个小时快照，与‘只留 12 小时’不符”**：核查时已有 9 个快照（08:00–16:00），“只留最近 12 小时”是保留上限、不是当时应有 12 个，不算错，未改文案。
- **“统计数字硬编码闪烁 stat-xnews=4 / xwool=3”**：当时最新快照确是 6 / 10，已把初始值改成 6 / 10；其余 8 个数字核对无误。
- **“62 个外链 4 个 403（techmeme、theneuron、everysaving、console.typesafe）”**：这 4 个是对方反爬墙，不是死链，不删不改；可后续加每日 link-check 报警（未做）。
- **“InfinityFree JS 挑战拦 GPTBot”**：属实，但 robots.txt 修不了挑战墙；根治要搬家（见需确认）。

## 已做（2026-11-09 晚，Eric 批准 1、2）

1. **构建时静态生成（SSR 预渲染）**：已上线。`build-static.py`（模板 `index.template.html` → 生成 `index.html`，内容直接写进 HTML，无 JS 也能看全量内容）。本地 jsdom 抽查 23 项全过：无 JS 时新闻 10 条、服务器表 10 行且 10 个链接、X 快照 9 个、统计 37/6/10；带 bundle 加载后计数不变、搜索与时段切换正常；stamp 不一致时 app.js 强制重渲染（自愈）也测过。
2. **12 个 JS 合并成 1 个 bundle.js**：已上线。`bundle.js` = 全部数据文件 + `app.js`，首页只加载它（`?v=<stamp>` 每次构建都变）；请求数从 14 个降到 3 个（HTML + CSS + bundle）。`app.js` 加了 hydration 守卫：静态内容已在就跳过渲染。
   流水线已同步改：4 个 cron（site-news-refresh-3h、x-hot-hourly、pro-promo-hunt、pro-promo-hunt-pm）正文里的同步步骤改为“改数据 → 跑 `build-static.py` → 传 `bundle.js` + `index.html` → 备份”。**只传数据文件不再更新页面**，这点已写进各 cron 正文与 README。
   注意：`index.html` 现在是生成物（约 47KB），不要手改；改结构改 `index.template.html`。

## 暂缓：已核实、可做，但需 Eric 拍板

3. **搬家到 Cloudflare Pages / GitHub Pages / Netlify + 自定义域名**：能根治 JS 挑战墙、HTTP/1.1、无 HSTS 三件事；但 GitHub Pages 是 Eric 2026-11-09 亲口暂停的，自定义域名要花钱（约一杯奶茶/年）。2026-11-09 晚 Eric 说“3 那个买域名暂时先不弄”。搬家后 .htaccess 失效，要改用 `_headers` / `_redirects`。
4. **.htaccess 是否生效**：InfinityFree 前端 openresty 可能覆盖响应头，上线后须 curl -I 复核；若不生效，缓存只能靠 `?v=` / 文件名版本化。
5. **每日 link-check**：62 个外链自动巡检报警，未做，可后续加进 cron。
6. **X 羊毛区 note 折叠、导航 scrollspy**：小优化，未做。

## 本次同步清单（SSR 版，只传这些到 /htdocs）

index.html（构建生成，约 47KB）、bundle.js（构建生成，约 47KB）、style.css、.htaccess、robots.txt、sitemap.xml、404.html、feed.xml、og.png。
不再传 data/*.js 与 app.js 到线上（它们只是本地底本与 bundle 原料，bundle.js 已包含它们）。
不上传到 /htdocs：index.template.html、build-static.py、convert-t2s.py、OPTIMIZATION-NOTES.md（本文件）、README.md（这些只放本地与 GitHub 备份分支）。
同步后跑 backup-push.py 备份到 GitHub backup 分支（备份清单已更新，含 bundle.js、模板、构建脚本与 og.png）。
