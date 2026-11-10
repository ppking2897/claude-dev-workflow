"""PreToolUse hook：Claude 執行 git commit 前，對照 TODO(等PM) 的題名與 feature-doc 待辦表。

只提醒、不擋（永遠 exit 0，不給 permissionDecision，照常走權限流程）。
沒有 git commit、不在 git repo、repo 沒有 .claude/docs/*.md 待辦表時，什麼都不做。

檢查三件事：
1. code 的標記題名（`TODO(等PM): <題名>，暫定…` 的 <題名>）在待辦表找不到同名的列
2. 標記的移除條件引用的「…」跟題名不同
3. 待辦表「屬於誰」是 PM 的列，code 裡沒有同名標記

題名比對只看括號前：待辦表「施工期間星號（必填…）」的題名是「施工期間星號」。
"""
import json
import os
import re
import subprocess
import sys

MARKER = re.compile(r"TODO\(等PM\):\s*([^，,；;]+?)\s*[，,；;]")
QUOTED = re.compile(r"移除條件[:：][^「]*「([^」]+)」")
SKIP_EXT = {".md", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".jar", ".zip", ".apk", ".so", ".ttf", ".otf"}


def title_of(text):
    """括號前的部分當題名（全形、半形括號都算）。"""
    return re.split(r"[（(]", text, maxsplit=1)[0].strip()


def run(args, cwd):
    try:
        return subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15).stdout
    except Exception:
        return ""


def commit_cwd(data):
    cmd = (data.get("tool_input") or {}).get("command", "")
    if not re.search(r"\bgit\b[^;&|]*\bcommit\b", cmd):
        return None
    cwd = data.get("cwd") or os.getcwd()
    m = re.search(r"\bgit\s+-C\s+(\"[^\"]+\"|'[^']+'|\S+)", cmd) or re.search(r"(?:^|&&|;)\s*(?:cd|Set-Location|sl|pushd)\s+(?:-(?:Literal)?Path\s+)?(\"[^\"]+\"|'[^']+'|\S+)", cmd)
    if m:
        p = m.group(1).strip("\"'")
        cand = p if os.path.isabs(p) else os.path.join(cwd, p)
        if os.path.isdir(cand):
            cwd = cand
    return cwd


def todo_rows(root):
    """回傳 [(doc 相對路徑, 題名, 屬於誰, 是否註明無程式標記)]：.claude/docs/*.md 裡「## 待辦」那一節的表格列。"""
    rows = []
    docs = os.path.join(root, ".claude", "docs")
    if not os.path.isdir(docs):
        return rows
    for name in sorted(os.listdir(docs)):
        if not name.endswith(".md"):
            continue
        path = os.path.join(docs, name)
        in_todo = False
        for line in open(path, encoding="utf-8", errors="replace"):
            if line.startswith("## "):
                in_todo = line.startswith("## 待辦")
                continue
            if not in_todo or not line.startswith("|") or line.startswith("|--") or line.startswith("| 項目"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 2:
                no_marker = "無程式標記" in line
                rows.append((".claude/docs/" + name, title_of(cells[0]), cells[1], no_marker))
    return rows


def markers(root):
    """回傳 [(檔案:行, 題名, 移除條件引用的題名或 None)]。"""
    out = []
    files = run(["git", "ls-files", "-co", "--exclude-standard"], root).splitlines()
    for rel in files:
        if os.path.splitext(rel)[1].lower() in SKIP_EXT:
            continue
        path = os.path.join(root, rel)
        try:
            with open(path, encoding="utf-8") as f:
                for no, line in enumerate(f, 1):
                    if "TODO(等PM)" not in line:
                        continue
                    m = MARKER.search(line)
                    if not m:
                        continue
                    q = QUOTED.search(line)
                    out.append((f"{rel}:{no}", title_of(m.group(1)), q.group(1) if q else None))
        except (UnicodeDecodeError, OSError):
            continue
    return out


def main():
    # Windows 的 stdin／stdout 預設是 cp950，Claude Code 傳的是 UTF-8
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    except Exception:
        return
    sys.stdout.reconfigure(encoding="utf-8")
    cwd = commit_cwd(data)
    if not cwd:
        return
    root = run(["git", "rev-parse", "--show-toplevel"], cwd).strip()
    if not root:
        return
    rows = todo_rows(root)
    if not rows:
        return

    titles = {r[1] for r in rows}
    found = markers(root)
    problems = []
    for loc, title, quoted in found:
        if title not in titles:
            problems.append(f"- {loc}：標記題名「{title}」在待辦表找不到同名的列")
        if quoted and quoted != title:
            problems.append(f"- {loc}：移除條件寫「{quoted}」，跟標記題名「{title}」不同")
    marked = {t for _, t, _ in found}
    for doc, title, owner, no_marker in rows:
        if owner == "PM" and not no_marker and title not in marked:
            problems.append(f"- {doc}：待辦「{title}」屬於 PM，code 裡沒有同名的 TODO(等PM) 標記（真的沒地方標就在待辦表那列註明「無程式標記」）")
    if not problems:
        return

    msg = ("⚠️ TODO(等PM) 題名對照（commit 前提醒，不阻擋）：\n" + "\n".join(problems) +
           "\n題名要跟待辦表一字不差，PM 答案回來時用題名搜才找得全。")
    print(json.dumps({
        "systemMessage": msg,
        "hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": msg},
    }, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # 提醒用的 hook，自己出錯也不能影響 commit
    sys.exit(0)
