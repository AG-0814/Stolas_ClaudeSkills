#!/usr/bin/env python3
"""把 stolas-web 主檔 (Markdown) 轉成 PDF 名詞速查。

用法：python build_web_pdf.py 主檔.md 輸出.pdf [--table "比較表標題"]

版面：
- 第 1 頁封面 (固定一頁)：標頭 (主題背景卡第一句) → 關鍵字地圖 (主檔 Mermaid 心智圖，去掉〔待拆〕) → 比較表一張 (有的話)
  → 「每個詞一句話」(封面放得下才放)。腳本會實際排版量高度，放不下的項目依優先順序移到後面。
- 第 2 頁起依序流動：每個詞一句話、資料來源 (8 筆以上另起一頁)。單一條目、表格、標題都不跨頁切斷。
- 比較表由 --table 指定 (呼叫者依 references/web-print.md 判斷哪張最能替封面輔助說明)。
  沒有指定時才退回機械挑法：表頭與第一欄中恰好是主檔關鍵字的格數最多者，平手取列數多者。
  指定的標題對不上任何表時，列出所有標題並以代碼 4 結束。
- 配色依 frontmatter 的學科標籤 (學群) 讀 assets/palette.json，沒有學科時用預設配色。
- 不收驗收紀錄、比喻與其餘比較表，內容只取自主檔，不補寫。

降級：沒有 mermaid-cli 時，封面改放文字版目錄樹；沒有 Playwright 時，只輸出 HTML (同名 .html) 並以代碼 3 結束。
"""
import html, json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_pdf import find_chrome  # noqa: E402

def palette(category):
    try:
        pal = json.load(open(os.path.join(HERE, '..', 'assets', 'palette.json'), encoding='utf-8'))
    except Exception:
        return '#394A56', '#EDF0F3'
    g = pal['groups'].get(category or '') or pal['default']
    return g['ink'], g['soft']

def parse(md, want=None):
    head = md.split('\n# ')[0]
    fm = dict(re.findall(r'^(\w+):\s*(.+)$', head, re.M))
    cat = None
    m = re.search(r'學科/[^/\s]+/([^/\s]+)', head)
    if m: cat = m.group(1)
    if not fm.get('topic'):
        h1 = re.search(r'^# (.+?)(：.*)?$', md, re.M)
        fm['topic'] = h1.group(1) if h1 else ''
    bg = md.split('## 主題背景卡')[1].split('\n## ')[0].strip() if '## 主題背景卡' in md else ''
    first = re.split(r'(?<=[。])', re.sub(r'\s*\n\s*', '', bg))[0] if bg else ''
    sec = md.split('## 心智圖')[1] if '## 心智圖' in md else ''
    mm = re.findall(r'```mermaid\n(.*?)```', sec, re.S)
    mm = '\n'.join(l for l in mm[0].splitlines() if '〔待拆〕' not in l) + '\n' if mm else ''
    tree = md.split('## 目錄樹')[1].split('\n## ')[0].strip().strip('`').replace('text\n', '') if '## 目錄樹' in md else ''
    tree = '\n'.join(l for l in tree.splitlines() if '〔待拆〕' not in l)
    body = md.split('## 關鍵字')[1].split('\n## ')[0] if '## 關鍵字' in md else ''
    ents, tables = [], []
    for blk in re.split(r'\n(?=### K\d+ )', body):
        m = re.match(r'### (K\d+) (.+)', blk.strip())
        if not m: continue
        one = re.search(r'\*\*一句話白話版\*\*：(.+)', blk)
        ents.append((m.group(1), m.group(2).strip(), one.group(1).strip() if one else ''))
        for t in re.finditer(r'\*\*比較表：(.+?)\*\*[^\n]*\n\s*\n?((?:\s*\|.*\n?)+)', blk):
            rows = [[c.strip() for c in r.strip().strip('|').split('|')] for r in t.group(2).strip().splitlines()]
            rows = [r for r in rows if not all(re.fullmatch(r':?-+:?', c) for c in r)]
            if len(rows) >= 2:
                tables.append({'title': t.group(1), 'rows': rows, 'owner': m.group(1) + ' ' + re.sub(r'\s*\(.*', '', m.group(2))})
    srcs = []
    if '## 資料來源' in md:
        srcs = [l.lstrip('-* ').strip() for l in md.split('## 資料來源')[1].strip().splitlines() if re.match(r'\s*[-*] ', l)]
    names = {re.sub(r'\s*\(.*', '', e[1]) for e in ents}
    def score(t):
        cells = {re.sub(r'\s*\(.*', '', c).strip() for c in t['rows'][0] + [r[0] for r in t['rows']]}
        return len(names & cells)
    if want:
        norm = lambda x: re.sub(r'\s+', '', x)
        hit = [t for t in tables if norm(t['title']) == norm(want)] or [t for t in tables if norm(want) in norm(t['title'])]
        if not hit:
            print('[table] 找不到標題為「%s」的比較表，主檔中的比較表標題：' % want, file=sys.stderr)
            for t in tables: print('  - ' + t['title'], file=sys.stderr)
            sys.exit(4)
        best = hit[0]
    else:
        best = max(tables, key=lambda t: (score(t), len(t['rows'])), default=None)
    date = fm.get('updated') or fm.get('created') or ''
    return dict(topic=fm['topic'].strip(), date=date.strip(), cat=cat, first=first, mm=mm, tree=tree,
                ents=ents, best=best, ntab=len(tables), srcs=srcs)

def mermaid_svg(code, work, ink, soft):
    mmdc = shutil.which('mmdc')
    if not mmdc or not code.strip(): return None
    src, out = os.path.join(work, 'm.mmd'), os.path.join(work, 'm.svg')
    open(src, 'w', encoding='utf-8').write(code)
    tv = {'primaryColor': ink, 'fontFamily': 'Noto Sans CJK TC', 'fontSize': '15px'}
    for i in range(12):
        tv[f'cScale{i}'], tv[f'cScaleLabel{i}'], tv[f'cScaleInv{i}'] = soft, '#1C2024', ink
    cfg, pp = os.path.join(work, 'c.json'), os.path.join(work, 'p.json')
    json.dump({'theme': 'base', 'themeVariables': tv}, open(cfg, 'w'))
    chrome = find_chrome()
    json.dump({'executablePath': chrome, 'args': ['--no-sandbox']} if chrome else {'args': ['--no-sandbox']}, open(pp, 'w'))
    try:
        subprocess.run([mmdc, '-i', src, '-o', out, '-c', cfg, '-p', pp, '-b', 'white', '-q'], check=True, capture_output=True, timeout=90)
        svg = open(out, encoding='utf-8').read()
        return re.sub(r'(<svg[^>]*?)\swidth="[^"]*"', r'\1 width="100%"', svg, count=1)
    except Exception as e:
        print(f'[warn] 心智圖轉換失敗，封面改放文字版目錄樹：{e}', file=sys.stderr)
        return None

def esc(s): return html.escape(s)

def sec(no, title, inner, cls='', hint=''):
    h = f'<span class="hint">{esc(hint)}</span>' if hint else ''
    return f'<section class="{cls}"><div class="sh"><span class="no mono">{no}</span><h2>{esc(title)}</h2>{h}</div>{inner}</section>'

def build(md_path, pdf_path, want=None):
    d = parse(open(md_path, encoding='utf-8').read(), want)
    ink, soft = palette(d['cat'])
    css = open(os.path.join(HERE, '..', 'assets', 'web-print.css'), encoding='utf-8').read()
    css += f':root{{--ink:{ink};--soft:{soft}}}'
    work = tempfile.mkdtemp(prefix='stolas-web-')
    svg = mermaid_svg(d['mm'], work, ink, soft)
    mapbox = svg if svg else f'<pre class="tree">{esc(d["tree"])}</pre>'
    orig = ''
    m = re.search(r'\(([A-Za-z][^)]*)\)', d['first'])
    if m: orig = m.group(1).split(',')[0].strip()
    head = (f'<header><div class="meta mono"><span>STOLAS WEB · 名詞速查</span><span>{esc(d["cat"] or "")}{" · " if d["cat"] else ""}{esc(d["date"])}</span></div>'
            f'<div class="title"><h1>{esc(d["topic"])}</h1><span class="orig">{esc(orig)}</span></div>'
            f'<p class="bg">{esc(d["first"])}</p></header>')
    mapsec = sec('01', '關鍵字地圖', f'<div class="box">{mapbox}</div>', 'map', '「- 與 Kn」為關聯')
    ntab = d['ntab']
    stat = (f'<div class="stat"><span><b>{len(d["ents"])}</b>個關鍵字</span>'
            f'<span><b>{ntab}</b>張比較表{"，本冊收 1 張" if ntab > 1 else ""}</span><span><b>{len(d["srcs"])}</b>筆資料來源</span></div>')

    def table(no, cls=''):
        t = d['best']
        if not t: return ''
        th = ''.join(f'<th>{esc(c)}</th>' for c in t['rows'][0])
        tr = ''.join('<tr>' + ''.join(f'<td>{esc(c)}</td>' for c in r) + '</tr>' for r in t['rows'][1:])
        return sec(no, t['title'], f'<table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table><div class="from">收錄於 {esc(t["owner"])}</div>', ('tbl ' + cls).strip())

    def ones(no, cls=''):
        items = ''.join(f'<div class="one"><span class="k mono">{k}</span><b>{esc(n)}</b><p>{esc(o)}</p></div>' for k, n, o in d['ents'])
        return sec(no, '每個詞一句話', f'<div class="ones">{items}</div>', ('ones-sec ' + cls).strip())

    def sources(no):
        if not d['srcs']: return ''
        lis = ''.join(f'<li>{esc(s)}</li>' for s in d['srcs'])
        return sec(no, '資料來源', f'<ol>{lis}</ol>', 'newpage' if len(d['srcs']) >= 8 else 'srcs-flow')

    def doc(cover, rest):
        return f'<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>{esc(d["topic"])} 名詞速查</title><style>{css}</style></head><body><div class="cover">{head}{mapsec}{cover}{stat}</div>{rest}</body></html>'

    # 封面優先順序：心智圖 → 比較表 → 每個詞一句話；放不下的依序往後移
    n_t = '02' if d['best'] else None
    n_o = '03' if d['best'] else '02'
    n_s = f'{int(n_o) + 1:02d}'
    candidates = [
        doc(table('02') + ones(n_o), sources(n_s)),
        doc(table('02'), ones(n_o, 'newpage') + sources(n_s)),
    ]
    if d['best']:
        candidates.append(doc('', ones('02', 'newpage') + table('03', 'newpage') + sources('04')))
    html_out = os.path.splitext(pdf_path)[0] + '.html'
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        open(html_out, 'w', encoding='utf-8').write(candidates[-1])
        print(f'[warn] 沒有 Playwright，只輸出 HTML：{html_out}', file=sys.stderr); sys.exit(3)
    with sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception:
            b = p.chromium.launch(executable_path=find_chrome())
        pg = b.new_page(viewport={'width': 794, 'height': 1123})
        chosen = candidates[-1]
        for c in candidates:
            pg.set_content(c); pg.wait_for_timeout(250)
            if pg.evaluate("(()=>{const c=document.querySelector('.cover');return c.scrollHeight<=c.clientHeight+1})()"):
                chosen = c; break
        open(html_out, 'w', encoding='utf-8').write(chosen)
        pg.set_content(chosen); pg.wait_for_timeout(300)
        pg.pdf(path=pdf_path, format='A4', prefer_css_page_size=True, print_background=True)
        b.close()
    print(f'[ok] {pdf_path}')

if __name__ == '__main__':
    args = sys.argv[1:]
    want = None
    if '--table' in args:
        i = args.index('--table'); want = args[i + 1]; del args[i:i + 2]
    if len(args) != 2: sys.exit(__doc__)
    build(os.path.abspath(args[0]), os.path.abspath(args[1]), want)
