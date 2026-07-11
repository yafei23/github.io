# Send to Kindle（复刻 Instapaper）

把任意网页文章推送到 Kindle：提取正文 → 生成 EPUB → 邮件发送到 `@kindle.com`。

## 使用方式

1. **网页**：打开 [send-to-kindle.html](https://yafei23.github.io/send-to-kindle.html)，粘贴文章链接；
2. **书签工具**：把页面上的 Bookmarklet 拖到书签栏，在任何文章页一键发送；
3. **直接开 Issue**：在本仓库新建 Issue，标题或正文里带上文章 URL 即可。

Issue 创建后，GitHub Actions 会自动抓取、转换并发送，成功后自动评论并关闭 Issue。只有仓库所有者创建的 Issue 会触发发送。

## 首次配置

### 1. 获取 Kindle 接收邮箱

在 [Amazon 内容与设备管理](https://www.amazon.com/hz/mycd/digital-console/alldevicespreferences)（首选项 → 个人文档设置）中：

- 找到你的 Kindle 接收邮箱（形如 `xxx@kindle.com`）；
- 在「已认可的个人文档电子邮件列表」中**添加你的发件邮箱**（下面 `SMTP_USERNAME` 用的那个），否则 Amazon 会拒收。

### 2. 准备发件邮箱（以 Gmail 为例）

1. 开启 Google 账号两步验证；
2. 在 [App passwords](https://myaccount.google.com/apppasswords) 生成一个应用专用密码。

### 3. 配置仓库 Secrets

在仓库 **Settings → Secrets and variables → Actions** 中添加：

| Secret | 说明 | 示例 |
| --- | --- | --- |
| `KINDLE_EMAIL` | Kindle 接收邮箱 | `xxx@kindle.com` |
| `SMTP_USERNAME` | 发件邮箱 | `you@gmail.com` |
| `SMTP_PASSWORD` | 应用专用密码 | 16 位应用密码 |
| `SMTP_HOST` | 可选，默认 `smtp.gmail.com` | |
| `SMTP_PORT` | 可选，默认 `465`（SSL） | |

## 本地测试

```bash
pip install requests readability-lxml 'lxml[html_clean]' ebooklib
DRY_RUN=1 python scripts/send_to_kindle.py https://example.com/article
```

`DRY_RUN=1` 只生成 EPUB 不发邮件，产物在当前目录。

## 组成部分

- `scripts/send_to_kindle.py` — 抓取、正文提取（readability）、EPUB 打包（含图片内嵌）、SMTP 发送；
- `.github/workflows/send-to-kindle.yml` — Issue 触发的自动化流程；
- `send-to-kindle.html` — 提交页面 + Bookmarklet。
