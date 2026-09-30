#!/usr/bin/env python3
"""从 lore.kernel.org 同步 syzbot 报告 + LKML patch 到 sync/。

在 GitHub Actions 上定时运行（见 .github/workflows/sync.yml）。
注：lore.kernel.org 的 HTTP 搜索有 Anubis 反爬，GitHub 云 IP 通常能过；
若被拦，会检测到并报错退出（此时回退到 git public-inbox 方案）。
"""
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UA = "Mozilla/5.0 (compatible; kernel-debug-cookbook-sync/1.0; +https://github.com/Ruiery/kernel-debug-cookbook)"
BASE = "https://lore.kernel.org/all/"
ATOM_NS = {"a": "http://www.w3.org/2005/Atom"}


def fetch_atom(query, days):
    """查询 lore，返回 Atom XML 文本。"""
    q = f"{query} d:{days}.day.ago.."
    url = BASE + "?q=" + urllib.parse.quote(q) + "&x=A"
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/atom+xml",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read().decode("utf-8", "replace")
    if "anubis" in body.lower() or "not a bot" in body.lower():
        raise RuntimeError("被 Anubis 反爬拦截（需回退到 git public-inbox 方案）")
    return body


def parse_atom(xml_text):
    """解析 Atom，返回 [{title, msgid, link, updated}]。"""
    root = ET.fromstring(xml_text)
    entries = []
    for e in root.findall("a:entry", ATOM_NS):
        title = (e.findtext("a:title", "", ATOM_NS) or "").strip()
        link = e.find("a:link", ATOM_NS)
        href = link.get("href", "") if link is not None else ""
        updated = (e.findtext("a:updated", "", ATOM_NS) or "").strip()
        # message-id 从链接里取（形如 https://lore.kernel.org/all/<msgid>/）
        m = re.search(r"/all/([^/]+)/?$", href)
        msgid = m.group(1) if m else ""
        entries.append({"title": title, "msgid": msgid, "link": href, "updated": updated})
    return entries


def write_entries(entries, dest_dir):
    """把条目写成 markdown（文件名用 message-id，稳定去重）。"""
    os.makedirs(dest_dir, exist_ok=True)
    n = 0
    for e in entries:
        if not e["title"] or not e["msgid"]:
            continue
        fn = os.path.join(dest_dir, re.sub(r"[^A-Za-z0-9@._-]", "_", e["msgid"]) + ".md")
        with open(fn, "w", encoding="utf-8") as f:
            f.write("---\n")
            f.write(f"title: {e['title']}\n")
            f.write("source: lore\n")
            f.write(f"link: {e['link']}\n")
            f.write(f"date: {e['updated']}\n")
            f.write("---\n\n")
            f.write(f"# {e['title']}\n\n")
            f.write(f"- 来源：{e['link']}\n")
            f.write(f"- 时间：{e['updated']}\n")
        n += 1
    print(f"{dest_dir}: 写入 {n} 条")


def main():
    ok = True
    # 1) syzbot 报告（最值钱：bug 标题 + 链接）
    try:
        write_entries(parse_atom(fetch_atom("s:syzbot", 7)), "sync/syzbot")
    except Exception as ex:
        ok = False
        print(f"syzbot 同步失败: {ex}", file=sys.stderr)
    # 2) 子系统 LKML patch（先粗筛，v1 按关键词，后续可细化）
    try:
        write_entries(parse_atom(fetch_atom('s:"PATCH" (s:mm OR s:sched OR s:locking)', 1)), "sync/lkml")
    except Exception as ex:
        ok = False
        print(f"lkml 同步失败: {ex}", file=sys.stderr)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
