"""Batch convert code files → images + PDF. One PDF per source file."""
import os, sys, subprocess, json

# === CONFIG ===
FILES = [
    # List source files here, e.g.:
    # 'main.c', 'key.c', 'KEY.h', 'adc.h', 'ADC.c',
    # 'DS1302.c', 'DS1302.h', 'EEPROM.c', 'EEPROM.h',
]
BASE = os.getcwd()
LINES_PER_PAGE = 50

# Colors (light theme)
KW = {'void','char','int','u8','u16','u32','uchar','unsigned',
      'for','if','else','while','switch','case','break','return',
      'static','bit','sbit','xdata','idata','code','interrupt',
      'do','default','continue','struct','typedef','enum','const',
      '#ifndef','#define','#endif','#ifdef','extern'}
RG = {'P0','P1','P2','P3','P4','P5','P6','P7','RST','SCLK','IO','SCK'}
CO = {'keyword':'#d63384','register':'#e8590c','macro':'#099268',
      'number':'#2b8a3e','string':'#099268','comment':'#868e96',
      'var':'#1971c2','text':'#212529'}
BG='#ffffff'; HDR_BG='#f1f3f5'; HDR_BORDER='#dee2e6'
GT_BG='#f8f9fa'; GT_BORDER='#e9ecef'; LN_COLOR='#868e96'


def tokenize(line):
    """Return list of (value, type) tuples."""
    t, i, n = [], 0, len(line)
    while i < n:
        if line[i] == '#':
            j = i
            while j < n and line[j] != '\n':
                j += 1
            t.append((line[i:j], 'macro'))
            break
        if line[i:i+2] == '//':
            t.append((line[i:], 'comment'))
            break
        if line[i:i+2] == '/*':
            j = i + 2
            while j < n and line[j:j+2] != '*/':
                j += 1
            if j < n:
                j += 2
            t.append((line[i:j], 'comment'))
            break
        if line[i] == '"':
            j = i + 1
            while j < n and line[j] != '"':
                if line[j] == '\\':
                    j += 1
                j += 1
            if j < n:
                j += 1
            t.append((line[i:j], 'string'))
            i = j
            continue
        if line[i] in ' \t':
            j = i
            while j < n and line[j] in ' \t':
                j += 1
            t.append((line[i:j], 'space'))
            i = j
            continue
        if line[i].isdigit() or (line[i] == '0' and i+1 < n and line[i+1] in 'xX'):
            if line[i] == '0' and i+1 < n and line[i+1] in 'xX':
                j = i + 2
            else:
                j = i
            while j < n and (line[j].isalnum() or line[j] in '.xXa-fA-F'):
                j += 1
            t.append((line[i:j], 'number'))
            i = j
            continue
        if line[i].isalpha() or line[i] == '_':
            j = i
            while j < n and (line[j].isalnum() or line[j] == '_'):
                j += 1
            w = line[i:j]
            if w in KW:
                t.append((w, 'keyword'))
            elif w in RG:
                t.append((w, 'register'))
            else:
                t.append((w, 'text'))
            i = j
            continue
        t.append((line[i], 'text'))
        i += 1
    if not t:
        t.append(('', 'space'))
    return t


def gen_svg_page(pg_lines, start_ln, page_num, total_pages, total_lines, fname):
    lh = 24
    fs = 14
    cw = 8.4
    gutter = 56
    xc = gutter + 16
    hh = 60
    mt = 2
    mb = 4
    mw = 794
    max_l = max((len(l) for l in pg_lines), default=10)
    w = max(mw, xc + max_l * cw + 30)
    h = hh + len(pg_lines) * lh + mt + mb + 20
    out = []
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">')
    out.append('<style>')
    out.append(f'  text {{ font-family: "Cascadia Code","Fira Code","JetBrains Mono","Consolas","Courier New",monospace; font-size: {fs}px; }}')
    out.append('</style>')
    out.append(f'<rect width="{w}" height="{h}" fill="{BG}"/>')
    out.append(f'<rect x="0" y="0" width="{w}" height="{hh}" fill="{HDR_BG}"/>')
    out.append(
        f'<line x1="0" y1="{hh}" x2="{w}" y2="{hh}" stroke="{HDR_BORDER}" stroke-width="1.5"/>')
    out.append(
        f'<text x="20" y="24" fill="#343a40" font-size="16" font-family="Arial,Helvetica,sans-serif" font-weight="700">📄 {fname}</text>')
    out.append(
        f'<text x="20" y="48" fill="#868e96" font-size="12" font-family="Arial,Helvetica,sans-serif">第 {page_num} 页 · 共 {total_pages} 页 · {total_lines} 行</text>')
    cy = hh + mt
    out.append(f'<rect x="0" y="{hh}" width="{xc - 8}" height="{h - hh}" fill="{GT_BG}"/>')
    out.append(
        f'<line x1="{xc - 8}" y1="{hh}" x2="{xc - 8}" y2="{h}" stroke="{GT_BORDER}" stroke-width="1"/>')
    for idx, line in enumerate(pg_lines):
        y = cy + idx * lh
        ln = start_ln + idx
        out.append(
            f'<text x="{xc - 14}" y="{y + lh // 2 + 4}" fill="{LN_COLOR}" text-anchor="end" font-size="12">{ln}</text>')
        if not line.strip():
            continue
        toks = tokenize(line)
        x = xc
        for val, typ in toks:
            if typ == 'space':
                x += (val.count(' ') + val.count('\t') * 4) * cw
            else:
                c = CO.get(typ, '#212529')
                e = val.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                out.append(f'<text x="{x:.1f}" y="{y + lh // 2 + 4}" fill="{c}">{e}</text>')
                x += len(val) * cw
    out.append(
        f'<text x="{w // 2}" y="{h - 8}" text-anchor="middle" fill="#adb5bd" font-size="10" font-family="Arial,Helvetica,sans-serif">- {page_num} -</text>')
    out.append('</svg>')
    return '\n'.join(out)


# === Main loop ===
for fname in FILES:
    src = os.path.join(BASE, fname)
    if not os.path.exists(src):
        print(f'SKIP {fname}')
        continue

    with open(src, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    total = len(lines)
    np = (total + LINES_PER_PAGE - 1) // LINES_PER_PAGE
    out_dir = os.path.join(BASE, fname + '_images')
    os.makedirs(out_dir, exist_ok=True)

    # Generate SVGs
    for p in range(1, np + 1):
        s = (p - 1) * LINES_PER_PAGE
        e = min(s + LINES_PER_PAGE, total)
        svg = gen_svg_page(lines[s:e], s + 1, p, np, total, fname)
        with open(os.path.join(out_dir, f'code_page_{p}.svg'), 'w', encoding='utf-8') as f:
            f.write(svg)
    print(f'{fname}: {total} lines, {np} pages -> SVG OK')

    # Convert SVGs to PNGs via node + @resvg/resvg-js
    js = (
        'const fs=require("fs");const{Resvg}=require("@resvg/resvg-js");'
        'const dir=' + json.dumps(out_dir.replace('\\', '\\\\')) + ';'
                                                                    'for(let p=1;p<=' + str(np) + ';p++){'
        'const s=dir+"\\\\code_page_"+p+".svg";'
        'const pn=dir+"\\\\code_page_"+p+".png";'
        'try{const d=fs.readFileSync(s,"utf8");const r=new Resvg(d,{background:"#ffffff"});'
        'const b=r.render();fs.writeFileSync(pn,b.asPng())}'
        'catch(e){console.log("  ERR:"+p+" "+e.message)}}'
    )
    subprocess.run(['node', '-e', js], check=True)
    print(f'{fname}: PNG OK')

    # Merge PNGs into a single PDF via img2pdf
    import img2pdf
    png_files = sorted(
        [os.path.join(out_dir, f) for f in os.listdir(out_dir) if f.endswith('.png')],
        key=lambda x: int(os.path.basename(x).replace('code_page_', '').replace('.png', ''))
    )
    pdf_path = os.path.join(BASE, fname + '.pdf')
    with open(pdf_path, 'wb') as f:
        f.write(img2pdf.convert(png_files))
    kb = os.path.getsize(pdf_path) // 1024
    print(f'{fname}: PDF -> {pdf_path} ({kb}KB)')

print('\n=== All done! ===')
