#!/usr/bin/env python3
"""把 Stolas 教材 (Markdown) 轉成 PDF 學習筆記。

用法：python build_pdf.py input.md output.pdf [--onepage 一頁重點.html] [--category 學群] [--depth 淺|中|深]

加上 --onepage 時，先把一頁重點 HTML (依 assets/onepage-a4.html 填寫) 轉成一頁 A4，
檢查內容沒有超出頁面、沒有殘留【】佔位文字，再放在 PDF 的第一頁。
檢查不通過時以代碼 2 結束並說明原因，依提示刪減文字後重跑。
--category 與 --depth 依 assets/palette.json 套用一頁重點的配色 (學群決定色相，深淺決定底色深度)，
文字黑白依 WCAG 對比度自動選擇。學群不在表中時使用預設配色。

流程：Mermaid 區塊 → SVG (mermaid-cli) ；Markdown → HTML (pandoc，公式用 MathML，圖片內嵌)；
HTML → PDF (Chromium 列印)。每一步都有降級方案，缺工具時仍盡量產出可讀的 PDF。
圖片請在呼叫前以 ![說明](相對路徑.svg) 寫進 Markdown，路徑相對於 input.md 所在資料夾。
"""
import glob, json, os, re, shutil, subprocess, sys, tempfile

CSS = """<style>
*{font-family:'Noto Sans CJK TC','Noto Sans CJK SC','Noto Sans TC','PingFang TC','Microsoft JhengHei',sans-serif}
html,body{max-width:none!important;margin:0!important;padding:0!important}
body{font-size:11pt;line-height:1.75;color:#222}
h1,h2,h3{page-break-after:avoid;line-height:1.4}
h2{border-bottom:1px solid #ccc;padding-bottom:4px;margin-top:1.6em}
table{border-collapse:collapse;width:100%;margin:.8em 0;font-size:9.5pt}
th,td{border:1px solid #bbb;padding:4px 8px;vertical-align:top}
th{background:#f3f3f3}
tr,img,figure{page-break-inside:avoid}
img{max-width:100%;max-height:200mm;width:auto;height:auto;display:block;margin:.6em auto}
figcaption{text-align:center;font-size:9.5pt;color:#555}
blockquote{color:#555;border-left:3px solid #ccc;margin:.6em 0;padding-left:10px}
pre,code{font-family:'Noto Sans Mono CJK TC',monospace;font-size:9.5pt}
pre{background:#f6f6f6;padding:8px;white-space:pre-wrap}
</style>"""

def find_chrome():
    cands = glob.glob('/opt/pw-browsers/*/chrome-linux/chrome') + glob.glob(os.path.expanduser('~/.cache/ms-playwright/*/chrome-linux/chrome'))
    for name in ('chromium', 'chromium-browser', 'google-chrome'):
        p = shutil.which(name)
        if p: cands.append(p)
    return cands[0] if cands else None

def _fix_svg_size(path):
    """mermaid-cli 輸出的 SVG 寬度是 100%，放進 PDF 會被放大到跨頁 (心智圖尤其明顯)。改成依 viewBox 的固定尺寸，交給 CSS 等比縮小。"""
    try:
        svg = open(path, encoding='utf-8').read()
        m = re.search(r'viewBox="[-\d.]+ [-\d.]+ ([\d.]+) ([\d.]+)"', svg)
        if not m: return
        w, h = float(m.group(1)), float(m.group(2))
        head_end = svg.index('>', svg.index('<svg'))
        head = svg[:head_end]
        head = re.sub(r'\swidth="[^"]*"', '', head)
        head = re.sub(r'\sheight="[^"]*"', '', head)
        head = re.sub(r'max-width:\s*[\d.]+px;?', '', head)
        head += f' width="{w:.0f}" height="{h:.0f}"'
        open(path, 'w', encoding='utf-8').write(head + svg[head_end:])
    except Exception as e:
        print(f'[warn] 調整 Mermaid 圖尺寸失敗：{e}', file=sys.stderr)

def render_mermaid(md, workdir):
    blocks = re.findall(r'```mermaid\n(.*?)```', md, flags=re.S)
    if not blocks: return md
    mmdc, chrome = shutil.which('mmdc'), find_chrome()
    for i, code in enumerate(blocks):
        out = os.path.join(workdir, f'mermaid-{i}.svg')
        ok = False
        if mmdc:
            src = os.path.join(workdir, f'm{i}.mmd'); open(src, 'w').write(code)
            cfg = os.path.join(workdir, 'pp.json')
            json.dump({'executablePath': chrome, 'args': ['--no-sandbox']} if chrome else {'args': ['--no-sandbox']}, open(cfg, 'w'))
            try:
                subprocess.run([mmdc, '-i', src, '-o', out, '-p', cfg, '-b', 'white'], check=True, capture_output=True, timeout=90)
                ok = os.path.exists(out)
                if ok: _fix_svg_size(out)
            except Exception as e:
                print(f'[warn] mermaid 轉換失敗，保留原始碼：{e}', file=sys.stderr)
        repl = f'![]({out})' if ok else f'```\n{code}```'
        md = md.replace(f'```mermaid\n{code}```', repl, 1)
    return md

def md_to_html(md_path, html_path, resource_dir):
    if shutil.which('pandoc'):
        subprocess.run(['pandoc', md_path, '-f', 'markdown', '-s', '--mathml', '--embed-resources',
                        '--resource-path', resource_dir, '--metadata', 'pagetitle=Stolas 學習筆記', '-o', html_path],
                       check=True)
    else:
        import markdown  # 降級：公式會保留原始 LaTeX 文字
        print('[warn] 找不到 pandoc，公式將以原始文字呈現', file=sys.stderr)
        body = markdown.markdown(open(md_path).read(), extensions=['tables', 'fenced_code'])
        open(html_path, 'w').write(f'<html><head><meta charset="utf-8"></head><body>{body}</body></html>')
    h = open(html_path).read().replace('</head>', CSS + '</head>', 1)
    open(html_path, 'w').write(h)

def html_to_pdf(html_path, pdf_path):
    footer = '<div style="font-size:8px;width:100%;text-align:center;color:#888"><span class="pageNumber"></span> / <span class="totalPages"></span></div>'
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            kw = {}
            chrome = find_chrome()
            try:
                b = p.chromium.launch()
            except Exception:
                b = p.chromium.launch(executable_path=chrome)
            pg = b.new_page(); pg.goto('file://' + os.path.abspath(html_path)); pg.wait_for_timeout(300)
            pg.pdf(path=pdf_path, format='A4', print_background=True, display_header_footer=True,
                   header_template='<div></div>', footer_template=footer,
                   margin={'top': '18mm', 'bottom': '18mm', 'left': '16mm', 'right': '16mm'})
            b.close(); return
    except Exception as e:
        print(f'[warn] Playwright 列印失敗，改用其他方式：{e}', file=sys.stderr)
    chrome = find_chrome()
    if chrome:
        subprocess.run([chrome, '--headless', '--no-sandbox', f'--print-to-pdf={pdf_path}', 'file://' + os.path.abspath(html_path)], check=True, capture_output=True); return
    if shutil.which('wkhtmltopdf'):
        print('[warn] 使用 wkhtmltopdf，MathML 公式可能無法正確顯示', file=sys.stderr)
        subprocess.run(['wkhtmltopdf', '--encoding', 'utf-8', html_path, pdf_path], check=True); return
    sys.exit('找不到任何 HTML 轉 PDF 的工具')

def _lum(hexc):
    v = [int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    v = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in v]
    return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]

def fg_for(bg):
    L = _lum(bg)
    return '#111111' if (L + 0.05) / 0.05 >= 1.05 / (L + 0.05) else '#FFFFFF'

def apply_palette(html_path, category, depth):
    """依學群與深淺，在一頁重點 HTML 中注入配色變數。回傳套色後的暫存 HTML 路徑 (與原檔同資料夾，以保留圖片相對路徑)。"""
    pal_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'palette.json')
    try:
        pal = json.load(open(pal_file, encoding='utf-8'))
    except Exception as e:
        print(f'[warn] 讀不到配色表，使用模板預設色：{e}', file=sys.stderr); return html_path
    g = pal['groups'].get(category or '', None)
    if g is None:
        if category: print(f'[warn] 學群「{category}」不在配色表中，使用預設配色', file=sys.stderr)
        g = pal['default']
    depth = {'淺': '淺', '中': '中', '深': '深', 'shallow': '淺', 'mid': '中', 'deep': '深'}.get(depth or '中', '中')
    bg = g[depth]
    css = (f'<style>:root{{--accent:{bg};--accent-fg:{fg_for(bg)};'
           f'--accent-ink:{g["ink"]};--accent-soft:{g["soft"]}}}</style>')
    h = open(html_path, encoding='utf-8').read().replace('</head>', css + '</head>', 1)
    out = os.path.join(os.path.dirname(os.path.abspath(html_path)), '.stolas-onepage-colored.html')
    open(out, 'w', encoding='utf-8').write(h)
    return out

def render_onepage(html_path, pdf_path):
    """一頁重點 HTML → 單頁 A4 PDF。內容超出頁面或殘留佔位文字時以代碼 2 結束。"""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception:
            b = p.chromium.launch(executable_path=find_chrome())
        pg = b.new_page(viewport={'width': 794, 'height': 1123})
        pg.goto('file://' + os.path.abspath(html_path)); pg.wait_for_timeout(300)
        info = pg.evaluate("""() => {
            const page = document.querySelector('#onepage') || document.body;
            const over = page.scrollHeight - page.clientHeight;
            const boxes = [];
            page.querySelectorAll('section, header, footer, .card, .out, .cmp, td').forEach(el => {
                if (el.scrollHeight - el.clientHeight > 1 || el.scrollWidth - el.clientWidth > 1) boxes.push((el.innerText || '').slice(0, 24));
            });
            return {over, boxes, placeholder: (document.body.innerText.match(/【[^】]*】/g) || []).slice(0, 5)};
        }""")
        problems = []
        if info['over'] > 0: problems.append(f"內容超出頁面約 {info['over']}px，請刪減文字 (不要縮小字級)")
        if info['boxes']: problems.append('以下區塊內容溢出：' + '；'.join(info['boxes']))
        if info['placeholder']: problems.append('殘留佔位文字：' + '、'.join(info['placeholder']))
        if problems:
            b.close(); print('[onepage] ' + '\n[onepage] '.join(problems), file=sys.stderr); sys.exit(2)
        pg.pdf(path=pdf_path, width='794px', height='1123px', print_background=True,
               margin={'top': '0', 'bottom': '0', 'left': '0', 'right': '0'})
        b.close()

def merge_pdfs(first, rest, dst):
    try:
        from pypdf import PdfWriter
        w = PdfWriter()
        for f in (first, rest): w.append(f)
        with open(dst, 'wb') as fh: w.write(fh)
        return True
    except Exception as e:
        if shutil.which('qpdf'):
            subprocess.run(['qpdf', '--empty', '--pages', first, rest, '--', dst], check=True); return True
        print(f'[warn] 無法合併 PDF ({e})，一頁重點另存為獨立檔案', file=sys.stderr)
        return False

def main():
    args = sys.argv[1:]
    onepage = category = depth = None
    if '--onepage' in args:
        i = args.index('--onepage'); onepage = os.path.abspath(args[i + 1]); del args[i:i + 2]
    if '--category' in args:
        i = args.index('--category'); category = args[i + 1]; del args[i:i + 2]
    if '--depth' in args:
        i = args.index('--depth'); depth = args[i + 1]; del args[i:i + 2]
    if len(args) != 2: sys.exit(__doc__)
    src, dst = os.path.abspath(args[0]), os.path.abspath(args[1])
    work = tempfile.mkdtemp(prefix='stolas-pdf-')
    one_pdf = None
    if onepage:
        one_pdf = os.path.join(work, 'onepage.pdf')
        colored = apply_palette(onepage, category, depth)
        try:
            render_onepage(colored, one_pdf)
        finally:
            if colored != onepage and os.path.exists(colored): os.remove(colored)
    md = render_mermaid(open(src).read(), work)
    tmp_md = os.path.join(work, 'print.md'); open(tmp_md, 'w').write(md)
    html = os.path.join(work, 'print.html')
    md_to_html(tmp_md, html, os.path.dirname(src))
    body_pdf = os.path.join(work, 'body.pdf') if one_pdf else dst
    html_to_pdf(html, body_pdf)
    if one_pdf and not merge_pdfs(one_pdf, body_pdf, dst):
        shutil.copy(body_pdf, dst); shutil.copy(one_pdf, dst.replace('.pdf', '-onepage.pdf'))
    print(f'PDF 已產出：{dst}')

if __name__ == '__main__':
    main()
