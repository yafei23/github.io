+++
title = "第一篇文章：Hello World"
date = 2026-06-08T10:00:00+08:00
draft = false
tags = ["随笔"]
+++

这是用 **Hugo + PaperMod** 搭建的博客的第一篇文章。

## 怎么写新文章

在仓库根目录运行：

```bash
hugo new posts/我的新文章.md
```

然后把 front matter 里的 `draft = true` 改成 `false`，写正文，`git push` 即可自动发布。

## 本地预览

```bash
hugo server -D
```

打开 http://localhost:1313 就能看到效果。
