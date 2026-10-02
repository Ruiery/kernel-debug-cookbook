#!/usr/bin/env python3
"""抓 syzbot 仪表盘（syzkaller.appspot.com）的 bug 报告，按子系统过滤。

与 sync-external.py（lore git，CI 可跑、免代理）不同：本脚本走 HTTP 抓
仪表盘，拿到的是 syzbot 全量结构化 bug（崩溃报告 + 复现器 + fix commit）。
仪表盘是 Google 域名，国内需代理；且代理在本机，跑不了 GitHub Actions，
用于本地/手动一次性拉取。

用法：
  python3 scripts/sync-syzbot-dashboard.py \
      --subsystems mm,block,kernel,cgroups \
      --proxy http://127.0.0.1:7890 \
      --output sync/syzbot-dashboard \
      [--limit 5]   # 只抓前 N 个，调试用
"""
import argparse
import html as htmlmod
import os
import re
import sys
import time
import urllib.request

BASE = "https://syzkaller.appspot.com"


def build_opener(proxy):
    if proxy:
        return urllib.request.build_opener(
            urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    return urllib.request.build_opener()


def fetch(opener, url, retries=3):
    for i in range(retries):
        try:
            return opener.open(url, timeout=60).read().decode("utf-8", "replace")
        except Exception as e:
            if i == retries - 1:
                raise
            time.sleep(1 + i)


def list_bugs(opener):
    """返回 [(extid, title, [subsystems])]，解析 /upstream 的 open bug 列表。"""
    html = fetch(opener, f"{BASE}/upstream")
    bugs = []
    for m in re.finditer(r"<tr>.*?</tr>", html, re.S):
        row = m.group(0)
        e = re.search(r"bug\?extid=([a-zA-Z0-9]+)", row)
        if not e:
            continue
        t = re.search(r'bug\?extid=[a-zA-Z0-9]+">([^<]+)</a>', row)
        title = htmlmod.unescape(t.group(1).strip()) if t else ""
        subs = re.findall(r"/upstream/s/([a-zA-Z0-9?._-]+)", row)
        bugs.append((e.group(1), title, subs))
    return bugs


def parse_bug_page(page):
    """从 /bug 页面提取 title / subsystems / 崩溃报告 / 复现器 / fix commit。"""
    info = {}
    m = re.search(r"<title>(.*?)</title>", page, re.S)
    info["title"] = htmlmod.unescape(m.group(1).strip()) if m else ""
    info["subsystems"] = re.findall(r"/upstream/s/([a-zA-Z0-9?._-]+)", page)
    # 崩溃报告：第一个 <pre> 块
    pre = re.search(r"<pre>(.*?)</pre>", page, re.S)
    report = pre.group(1) if pre else ""
    report = re.sub(r"<[^>]+>", "", report)
    info["report"] = htmlmod.unescape(report).strip()
    # 复现器链接（/x/repro.syz?x=... / /x/repro.c?x=...）
    info["repro"] = re.findall(r"/x/repro\.(?:syz|c)\?x=[^\"'&]+", page)
    # fix commit
    fc = re.search(r"/commit\?hash=([a-f0-9]+)", page)
    info["fix_commit"] = fc.group(1) if fc else ""
    return info


def write_md(outdir, extid, info):
    fn = os.path.join(outdir, f"{extid}.md")
    link = f"{BASE}/bug?extid={extid}"
    subs = ",".join(info["subsystems"])
    with open(fn, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(f"title: {info['title']}\n")
        f.write(f"subsystems: {subs}\n")
        f.write(f"extid: {extid}\n")
        f.write(f"link: {link}\n")
        f.write("source: syzbot-dashboard\n")
        f.write("---\n\n")
        f.write(f"# {info['title']}\n\n")
        f.write(f"来源：[{link}]({link})\n\n")
        if info["fix_commit"]:
            f.write(f"修复 commit：`{info['fix_commit']}`\n\n")
        if info["repro"]:
            f.write("复现器：\n")
            for r in info["repro"]:
                f.write(f"- {BASE}/{r}\n")
            f.write("\n")
        if info["report"]:
            f.write("## 崩溃报告\n\n```\n" + info["report"][:8000] + "\n```\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proxy", default="http://127.0.0.1:7890")
    ap.add_argument("--subsystems", default="mm,block,kernel,cgroups")
    ap.add_argument("--output", default="sync/syzbot-dashboard")
    ap.add_argument("--limit", type=int, default=0, help="只抓前 N 个（调试）")
    a = ap.parse_args()
    targets = {s.strip() for s in a.subsystems.split(",") if s.strip()}
    opener = build_opener(a.proxy)
    bugs = list_bugs(opener)
    picked = [b for b in bugs if set(b[2]) & targets]
    # 按 extid 去重
    seen = {}
    for e, t, s in picked:
        seen.setdefault(e, (e, t, s))
    picked = list(seen.values())
    if a.limit:
        picked = picked[: a.limit]
    os.makedirs(a.output, exist_ok=True)
    ok = 0
    for extid, title, subs in picked:
        try:
            page = fetch(opener, f"{BASE}/bug?extid={extid}")
            info = parse_bug_page(page)
            write_md(a.output, extid, info)
            ok += 1
            print(f"[{ok}/{len(picked)}] {title}")
        except Exception as ex:
            print(f"  skip {extid}: {ex}", file=sys.stderr)
        time.sleep(0.2)
    print(f"目标子系统 {sorted(targets)}：匹配 {len(picked)} 个 bug，成功抓取 {ok} 个 → {a.output}")


if __name__ == "__main__":
    main()
