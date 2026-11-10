"""PM 問卷產生器範本：複製到 scratchpad，改「設定」區後執行。

用法：py -I -X utf8 <複製後的檔案>.py
輸出：<OUT_DIR>/to-questionnaire-<SLUG>.html、.md，以及 <OUT_DIR>/<IMG_DIR_NAME>/ 圖片資料夾。
格式說明見同層的 ../questionnaire-format.md。
"""
import base64, html, pathlib, shutil

HERE = pathlib.Path(__file__).resolve().parent
ASSETS = pathlib.Path.home() / ".claude/skills/my-flow/questionnaire"

# ===================== 設定（每次改這裡） =====================
OUT_DIR = pathlib.Path("交付資料夾")
SLUG = "project-topic-1030"                      # 檔名用，英文
IMG_DIR_NAME = "專案主題問卷1030"                 # 圖片資料夾名
TITLE = "專案 主題：待 PM 確認（10-30）"
DOWNLOAD_NAME = "專案主題-1030-回覆.md"           # 「下載回答」的檔名
PURPOSE = "已照設計稿做完 OOO。對照時有 N 個地方設計稿沒畫、畫得不一致，或跟之前的規則衝突。App 先照「目前做成」的暫定做法開發，需要 PM 決定最後怎麼做。"
FROM_TO = ("App 開發", "PM")
USAGE = "照回覆調整 App 的文案與行為。"
BACKGROUND = "設計稿是 Figma「…」的 …（節點 ID）。每題的圖用紅框加編號標出要看的地方，編號對應下方說明。"
EXTRA_Q = "還有什麼我們沒問到、但開發應該知道的事？"

# 圖片：key → (來源路徑, 輸出檔名, 圖說：畫面名稱＋節點 ID)
IMAGES = {
    "a": (OUT_DIR / "target/1.png", "p1-screen.png", "設計稿 1「畫面名稱」（節點 ID）"),
}

def fig(key, boxes):
    """boxes：[(編號, left%, top%, width%, height%)]，以圖片寬高的百分比定位。"""
    return {"key": key, "boxes": boxes}

QUESTIONS = [
  {"section": "1. 主題", "items": [
    {"id": "1.1", "p": "P1",                       # p：追蹤清單的題號
     "q": "一句話的問題？",
     "figs": [fig("a", [(1, 3.0, 15.0, 94.0, 9.0)])],
     "notes": ["① 紅框 1 是什麼。", "為什麼要問（設計稿沒畫／前後不一致／跟之前的回覆衝突）。"],
     "app": "App 目前的暫定做法。",
     "ask": "要 PM 決定的事（給選項或例子）。"},
  ]},
]
# ============================================================

IMG_DIR = OUT_DIR / IMG_DIR_NAME
IMG_DIR.mkdir(parents=True, exist_ok=True)
for key, (src, name, _) in IMAGES.items():
    assert pathlib.Path(src).exists(), src
    shutil.copyfile(src, IMG_DIR / name)

def b64(key):
    return "data:image/png;base64," + base64.b64encode(pathlib.Path(IMAGES[key][0]).read_bytes()).decode()

def render_fig(f):
    k = f["key"]
    boxes = "".join(
        f'<div class="box" style="left:{l}%;top:{t}%;width:{w}%;height:{h}%"><span class="badge">{n}</span></div>'
        for n, l, t, w, h in f["boxes"])
    return (f'<div class="fig"><div class="cap">{html.escape(IMAGES[k][2])}</div>'
            f'<div class="shot"><img src="{b64(k)}" alt="{html.escape(IMAGES[k][2])}">{boxes}</div></div>')

BASE_CSS = (ASSETS / "base.css").read_text(encoding="utf-8")
BASE_JS = ((ASSETS / "base.js").read_text(encoding="utf-8")
           .replace("__STORAGE_KEY__", repr(SLUG + "-v1"))
           .replace("__DOWNLOAD_NAME__", repr(DOWNLOAD_NAME)))
EXTRA_CSS = """
main { max-width: 1100px; }
.bar-inner { max-width: 1100px; }
.question h3 .pid { margin-left: auto; font-size: 12px; color: var(--muted); font-family: var(--font-mono); }
.figs{display:flex;flex-wrap:wrap;gap:20px 40px;padding-left:28px}
.fig{width:300px}
.fig .cap{font-size:13px;color:var(--muted);margin-bottom:6px;min-height:2.6em;line-height:1.4}
.shot{position:relative}
.shot img{display:block;width:100%;border:1px solid var(--line);border-radius:6px;background:#fff}
.box{position:absolute;border:3px solid #d22;border-radius:4px}
.badge{position:absolute;left:-30px;top:50%;transform:translateY(-50%);width:24px;height:24px;border-radius:50%;background:#d22;color:#fff;font-size:14px;font-weight:700;display:flex;align-items:center;justify-content:center;line-height:1}
.app,.ask{font-size:15px;padding:10px 14px;border-left:5px solid #9aa3ad;background:var(--bg);border-radius:0 6px 6px 0;max-width:80ch}
.ask{border-left-color:var(--accent);background:var(--accent-soft)}
.app b,.ask b{display:block}
.toc{margin:0;padding-left:0;list-style:none;display:grid;gap:2px}
.toc a{color:inherit}
.question{scroll-margin-top:80px}
"""

total = sum(len(s["items"]) for s in QUESTIONS)
parts = []
for sec in QUESTIONS:
    parts.append(f'<section><h2>{html.escape(sec["section"])}</h2>')
    for it in sec["items"]:
        qid = "q-" + it["id"].replace(".", "-")
        figs = "".join(render_fig(f) for f in it["figs"])
        notes = "".join(f"<li>{html.escape(n)}</li>" for n in it["notes"])
        parts.append(
            f'<div class="question" id="{qid}-card" data-qid="{qid}" data-num="{it["id"]}" data-text="{html.escape(it["q"] + "（" + it["p"] + "）")}">'
            f'<h3 id="{qid}-h"><span class="qnum">{it["id"]}</span>{html.escape(it["q"])}<span class="pid">{it["p"]}</span></h3>'
            + (f'<div class="figs">{figs}</div>' if figs else "")
            + (f'<ul class="notes">{notes}</ul>' if notes else "")
            + f'<div class="app"><b>App 目前做成</b>{html.escape(it["app"])}</div>'
            + f'<div class="ask"><b>想請 PM 確認</b>{html.escape(it["ask"])}</div>'
            + f'<label class="sr" for="{qid}">回答</label><textarea id="{qid}" rows="3" placeholder="請填寫；不確定的話寫「不知道」也可以"></textarea></div>')
    parts.append('</section>')
toc = "".join(f'<li><a href="#q-{it["id"].replace(".", "-")}-card">{it["id"]} {html.escape(it["q"])}</a></li>'
              for sec in QUESTIONS for it in sec["items"])

page = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(TITLE)}</title>
<style>{BASE_CSS}{EXTRA_CSS}</style>
</head>
<body>
<div class="bar"><div class="bar-inner"><div class="progress"><span id="progress-text">已回答 0 題</span><div class="meter"><span id="meter"></span></div></div><div class="actions"><button type="button" id="copy-btn" class="primary">複製回答</button><button type="button" id="download-btn">下載回答（.md）</button></div><span class="status" id="status" role="status" aria-live="polite"></span></div></div>
<main>
<h1>{html.escape(TITLE)}</h1>
<p><strong>目的：</strong> {html.escape(PURPOSE)}</p>
<p><strong>From：</strong> {html.escape(FROM_TO[0])}，<strong>To：</strong> {html.escape(FROM_TO[1])}，<strong>回答的用途：</strong> {html.escape(USAGE)}</p>
<section><h2>背景</h2><p>{html.escape(BACKGROUND)}</p></section>
<section><h2>作答方式</h2>
<p>共 {total} 題，每題都附了「App 目前做成」，同意的話回「可以」即可；不同意的話，寫希望怎麼做就好。不確定的請寫「不知道」或目前的想法，不要跳過。</p>
<p>填的內容會自動存在這台電腦的瀏覽器裡，關掉再開還在。填完按上方「下載回答（.md）」把檔案傳回來，或按「複製回答」貼到訊息裡。</p>
</section>
<section><h2>題目一覽</h2><ol class="toc">{toc}</ol></section>
{''.join(parts)}
<section><h2>還有其他的嗎？</h2>
<div class="question" data-qid="q-extra-1" data-num="" data-text="{html.escape(EXTRA_Q)}"><h3 id="q-extra-1-h">{html.escape(EXTRA_Q)}</h3>
<label class="sr" for="q-extra-1">回答</label><textarea id="q-extra-1" rows="3" placeholder="請填寫；不確定的話寫「不知道」也可以"></textarea></div>
</section>
</main>
<script>{BASE_JS}</script>
</body>
</html>"""
out_html = OUT_DIR / f"to-questionnaire-{SLUG}.html"
out_html.write_text(page, encoding="utf-8")

md = [f"# {TITLE}", "", f"**目的：** {PURPOSE}", "",
      f"**From：** {FROM_TO[0]}，**To：** {FROM_TO[1]}，**回覆用途：** {USAGE}", "",
      "## 背景", "", BACKGROUND + "HTML 版的圖有紅框與編號；這份 Markdown 只放原圖，編號說明照抄。", "",
      "## 怎麼回覆", "", "直接寫在每題的 `>` 後面，或開會時一起過。不確定的請寫「不確定」或目前的想法，不要跳過。", ""]
for sec in QUESTIONS:
    md += [f"## {sec['section']}", ""]
    for it in sec["items"]:
        for f in it["figs"]:
            md += [f"![{IMAGES[f['key']][2]}]({IMG_DIR_NAME}/{IMAGES[f['key']][1]})", ""]
        md += [f"### {it['id']} {it['q']}（{it['p']}）", "",
               f"_{' '.join(it['notes'])} App 目前做成：{it['app']}_", "",
               f"**想請 PM 確認：** {it['ask']}", "", ">", ""]
md += ["## 還有其他要補充的嗎？", "", "有我們沒問到、但開發應該知道的事，請寫在這裡。", "", ">", ""]
(OUT_DIR / f"to-questionnaire-{SLUG}.md").write_text("\n".join(md), encoding="utf-8")
print(out_html, out_html.stat().st_size, total)
