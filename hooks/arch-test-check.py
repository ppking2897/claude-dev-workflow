"""PreToolUse hook：Claude 執行 git commit 前，跑專案宣告的架構測試，沒過就擋下 commit。

不看語言：專案的 CLAUDE.md（或 .claude/CLAUDE.md、AGENTS.md）有一行

    - 架構測試指令：`<指令>`

就在 repo 根目錄用 bash 跑那個指令（`/arch-test` 做完時寫上）。指令結束碼不是 0 → exit 2 擋下，
把輸出的最後幾行給 Claude 看。沒有 git commit、不在 git repo、沒宣告那一行 → 什麼都不做。
hook 讀不到輸入或程式出錯時放行；有宣告卻跑不了（找不到 bash、逾時）時擋下，免得檢查壞了沒人發現。
"""
import json
import os
import re
import shutil
import subprocess
import sys

DECL = re.compile(r"架構測試指令[：:]\s*`([^`]+)`")
DOCS = ("CLAUDE.md", os.path.join(".claude", "CLAUDE.md"), "AGENTS.md")
TAIL = 60
TIMEOUT = 840  # settings.json 的 hook timeout 設 900 秒，留一點時間印訊息


def commit_cwd(data):
    """是 git commit 就回傳要檢查的目錄，不是就回傳 None。"""
    cmd = (data.get("tool_input") or {}).get("command", "")
    if not re.search(r"\bgit\b[^;&|\n]*\bcommit(?![\w-])", cmd):
        return None
    cwd = data.get("cwd") or os.getcwd()
    m = re.search(r"\bgit\s+-C\s+(\"[^\"]+\"|'[^']+'|\S+)", cmd) or re.search(r"(?:^|&&|;)\s*cd\s+(\"[^\"]+\"|'[^']+'|\S+)", cmd)
    if m:
        p = m.group(1).strip("\"'")
        cand = p if os.path.isabs(p) else os.path.join(cwd, p)
        if os.path.isdir(cand):
            cwd = cand
    return cwd


def declared_command(root):
    for rel in DOCS:
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                m = DECL.search(line)
                if m:
                    return m.group(1).strip(), rel
    return None, None


def bash_path():
    """Windows 上 PATH 裡的 bash 可能是 WSL 的，改用 Git 附的那支。"""
    if os.name != "nt":
        return "bash"
    env = os.environ.get("CLAUDE_CODE_GIT_BASH_PATH")
    if env and os.path.isfile(env):
        return env
    git = shutil.which("git")  # ...\Git\cmd\git.exe 或 ...\Git\mingw64\bin\git.exe
    d = os.path.dirname(git) if git else None
    for _ in range(4):
        if not d:
            break
        cand = os.path.join(d, "bin", "bash.exe")
        if os.path.isfile(cand):
            return cand
        d = os.path.dirname(d)
    return None


def main():
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))  # PowerShell 管線會在前面加 BOM
    except Exception:
        return 0
    cwd = commit_cwd(data)
    if not cwd:
        return 0
    try:
        root = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=cwd, capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=15).stdout.strip()
    except Exception:
        return 0
    if not root:
        return 0
    cmd, doc = declared_command(root)
    if not cmd:
        return 0

    sys.stderr.reconfigure(encoding="utf-8")
    bash = bash_path()
    if not bash:
        print(f"❌ 架構測試沒跑：找不到 Git 附的 bash（{doc} 宣告了 `{cmd}`），commit 已擋下。\n"
              f"設環境變數 CLAUDE_CODE_GIT_BASH_PATH 指到 Git 的 bash.exe 後再 commit。", file=sys.stderr)
        return 2
    try:
        r = subprocess.run([bash, "-c", cmd], cwd=root, capture_output=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        print(f"❌ 架構測試超過 {TIMEOUT} 秒沒跑完，commit 已擋下。\n指令：{cmd}（宣告在 {doc}）", file=sys.stderr)
        return 2
    if r.returncode == 0:
        return 0

    out = (r.stdout + b"\n" + r.stderr).decode("utf-8", errors="replace").splitlines()
    tail = "\n".join(line for line in out[-TAIL:])
    print(f"❌ 架構測試沒過，commit 已擋下。\n"
          f"指令：{cmd}（宣告在 {doc}，結束碼 {r.returncode}）\n"
          f"--- 輸出最後 {TAIL} 行 ---\n{tail}\n"
          f"--- 修好違規再 commit；規則與例外清單見專案的架構規則文件 ---", file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        code = main()
    except Exception:
        code = 0
    sys.exit(code)
