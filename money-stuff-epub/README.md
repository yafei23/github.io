# Money Stuff 中文导读 → EPUB

把 Matt Levine 的 **Money Stuff**（Bloomberg Opinion）专栏整理成 EPUB 电子书的工具。

## 产物

- `MoneyStuff_中文导读合集.epub` —— 最近 **10 期**专栏的**中文导读/概要**合集，按时间倒序。

> ⚠️ **关于版权**：Money Stuff 是 Bloomberg 的版权专栏。本仓库提供的是**中文导读/概要**
> （编者根据每期公开标题与主题清单撰写），**不是原文全文翻译**。原文请用你自己的订阅在
> [Bloomberg Opinion](https://www.bloomberg.com/opinion/authors/ARbTQlRLRjE/matthew-s-levine)
> 阅读。如需把**自己收到的邮件**做个人格式转换，见下方「全文模式」。

## 用法

### 1. 生成中文导读合集（开箱即用）

```bash
python3 build_epub.py
```

读取 `content.py` 中的 10 期数据，输出 `MoneyStuff_中文导读合集.epub`。
纯 Python 标准库，无需安装任何依赖。

### 2. 全文模式（用你自己保存的邮件）

`build_epub.py` 里的 `build_epub(meta, chapters, out_path)` 是通用的 EPUB 生成函数。
你可以把自己邮箱里保存的 Money Stuff 邮件（HTML / .eml）解析成章节后喂进去：

```python
from build_epub import build_epub

meta = {"title": "Money Stuff 合集", "author": "Matt Levine", "language": "en"}
chapters = [
    {"title": "Edition title", "body": "<p>...你解析出的正文 HTML...</p>"},
    # ...
]
build_epub(meta, chapters, "out.epub")
```

解析邮件的部分（提取正文 HTML）可用标准库 `email` + `html.parser`，按你保存邮件的格式实现即可。

## 文件

| 文件 | 说明 |
|------|------|
| `build_epub.py` | EPUB 3 生成器（纯标准库）+ 命令行入口 |
| `content.py`    | 10 期专栏的中文导读数据 |

## 收录的 10 期（按时间倒序）

1. Robinhood 上线 AI 代理 — *Robinhood Adds Some Agents*（2026-05-27）
2. 指数基金对 SpaceX 说不了「不」 — *Index Funds Can't Say No to SpaceX*（2026-05-26）
3. SpaceX 的投资者无从抱怨 — *SpaceX Investors Can't Complain*（2026-05-21）
4. 「预测」成了新的公开市场 — *Predicting Is the New Public Market*
5. 有时候 Andrew Left 是对的 — *Sometimes Andrew Left Was Right*
6. GameStop 的股票不够用了 — *GameStop Doesn't Have Enough Stock*（2026-05-04）
7. 把没人用的电卖掉 — *Sell the Electricity No One Is Using*（2026-04-30）
8. 短线交易引发的逼空 — *Short-Swing Short Squeeze*（2026-04-29）
9. 机器人来做预测 — *The Robots Make the Predictions*（2026-04-28）
10. 一切皆是大宗商品欺诈 — *Everything Is Commodities Fraud*（2026-04-27）
