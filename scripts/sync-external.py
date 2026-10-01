#!/usr/bin/env python3
"""从 lore public-inbox（git 协议）同步 LKML patch 到 sync/lkml/、syzbot 报告到 sync/syzbot/。

为什么用 git 而非 HTTP：lore.kernel.org 的 HTTP 搜索被 Anubis 反爬拦
（本地和 GitHub Actions 的 IP 都被拦）；git 协议不拦，`--depth N` 浅克隆可用。

syzbot 报告直接发到各子系统列表（subject 带 [syzbot]），同样走 git 捞；
官方仪表盘 syzkaller.appspot.com 是 Google 域名（国内需代理），暂不覆盖。
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

LISTS = ["linux-mm", "linux-block", "linux-rt-users"]  # 子系统列表，可增
DEPTH = 500  # 每次浅克隆最近 N 封邮件（约一天）
OUT_LKML = "sync/lkml"
OUT_SYZBOT = "sync/syzbot"


def clone(listname, depth):
    tmp = tempfile.mkdtemp()
    url = f"https://lore.kernel.org/{listname}/0"
    r = subprocess.run(
        ["git", "clone", "--quiet", "--depth", str(depth), url, tmp],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if r.returncode != 0:
        raise RuntimeError(f"clone {listname} 失败: {r.stderr.strip()}")
    return tmp


def get_messages(repo, grep, prefix):
    """返回 [(hash, subject)]，只取 subject 以 prefix 开头的邮件。"""
    r = subprocess.run(
        ["git", "-C", repo, "log", "--format=%H%x1f%s", f"--grep={grep}"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    out = []
    for line in r.stdout.splitlines():
        if "\x1f" in line:
            h, s = line.split("\x1f", 1)
            s = s.strip()
            if s.startswith(prefix):
                out.append((h, s))
    return out


def get_message(repo, h):
    """读原始邮件（public-inbox 把每封邮件存成 commit 的 m blob）。"""
    r = subprocess.run(
        ["git", "-C", repo, "show", f"{h}:m"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return r.stdout


def parse_email(raw):
    msgid = ""
    m = re.search(r"^message-id:\s*<([^>]+)>", raw, re.M | re.I)
    if m:
        msgid = m.group(1)
    body = raw.split("\n\n", 1)[1].strip() if "\n\n" in raw else ""
    return msgid, body


def write_markdown(dest, listname, title, msgid, body, source=None):
    key = msgid or re.sub(r"[^A-Za-z0-9]+", "_", title)[:80]
    fn = os.path.join(dest, re.sub(r"[^A-Za-z0-9@._-]", "_", key) + ".md")
    link = f"https://lore.kernel.org/{listname}/{msgid}/" if msgid else ""
    with open(fn, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(f"title: {title}\n")
        f.write(f"list: {listname}\n")
        if source:
            f.write(f"source: {source}\n")
        f.write(f"message_id: {msgid}\n")
        f.write(f"link: {link}\n")
        f.write("---\n\n")
        f.write(f"# {title}\n\n")
        f.write(f"来源：[{link}]({link})\n\n" if link else "")
        if body:
            f.write("```\n" + body[:8000] + "\n```\n")


def main():
    os.makedirs(OUT_LKML, exist_ok=True)
    os.makedirs(OUT_SYZBOT, exist_ok=True)
    ok = True
    for listname in LISTS:
        repo = None
        try:
            repo = clone(listname, DEPTH)
            patches = get_messages(repo, "PATCH", "[PATCH")
            for h, s in patches:
                raw = get_message(repo, h)
                msgid, body = parse_email(raw)
                write_markdown(OUT_LKML, listname, s, msgid, body)
            syzbot = get_messages(repo, "syzbot", "[syzbot")
            for h, s in syzbot:
                raw = get_message(repo, h)
                msgid, body = parse_email(raw)
                write_markdown(OUT_SYZBOT, listname, s, msgid, body, source="syzbot")
            print(f"{listname}: {len(patches)} 条 patch, {len(syzbot)} 条 syzbot 报告")
        except Exception as ex:
            ok = False
            print(f"{listname} 同步失败: {ex}", file=sys.stderr)
        finally:
            if repo:
                shutil.rmtree(repo, ignore_errors=True)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
