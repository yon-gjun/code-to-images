---
name: "code-to-images"
description: "Convert code files to A4-ratio PNG/SVG images with line numbers and syntax highlighting, then merge to PDF"
---

# Code → A4 Images + PDF (Improved)

Convert source code files into multi-page A4-ratio images (SVG+PNG) then merge into a single PDF, with:

- **Line numbers** with adaptive gutter width
- **Syntax highlighting** (keywords, registers, macros, numbers, strings, comments)
- **File name header** with page info per sheet
- **Light theme** (white background, professional look)
- **Multiple font choices**: Cascadia Code, Fira Code, JetBrains Mono, Consolas, Courier New, Source Code Pro
- **Auto-fit to A4**: Font size automatically adjusted so code fills the page width; lines per page computed from available height
- **Intelligent width handling**: Long lines truncated with "…" marker, clipped at page boundary
- **Proper tab stop handling**: Tabs advance to correct tab stops (not just `\t × 4`)
- **Final output**: one PDF per source file

## Prerequisites

- Python 3 (tested with 3.14+)
- Node.js and `@resvg/resvg-js` for SVG→PNG conversion
- Python packages: `img2pdf`

```bash
npm install -g @resvg/resvg-js
pip install img2pdf
```

## Workflow

### 1. Get the source code

Ask the user to provide the source code file(s). Save them to the workspace.

### 2. Generate SVGs + PNGs + PDF (all-in-one)

Run the batch script below. It reads every source code file and for each one:
1. Reads all lines, finds the longest line
2. Auto-calculates optimal font size to fit A4 width (capped at `FONT_SIZE`)
3. Auto-calculates lines per page from available A4 height
4. Splits code into pages
5. Generates SVG for each page (fixed A4 viewBox, syntax-highlighted)
6. Renders each SVG to PNG via `@resvg/resvg-js`
7. Merges all PNG pages into a single PDF via `img2pdf`

Output structure:
```
filename.c/
├── code_page_1.svg
├── code_page_1.png
├── code_page_2.svg
├── code_page_2.png
└── ...
filename.c.pdf    ← merged PDF
```

## Python Batch Script

Save as `gen_code_pdfs.py` and run with `python gen_code_pdfs.py`:

```python
"""Batch convert code files → A4 images + PDF. One PDF per source file."""
import os, sys, subprocess, json, math

# ===== CONFIG =====
FILES = [
    # List source files here, e.g.:
    # 'main.c', 'key.c', 'KEY.h', 'adc.h', 'ADC.c',
    # 'DS1302.c', 'DS1302.h', 'EEPROM.c', 'EEPROM.h',
]

FONT_KEY = 'cascadia'        # Available: cascadia, firacode, jetbrains, consolas, courier, sourcecode
FONT_SIZE = 14               # Base font size (px). Auto-reduced if longest line exceeds A4 width.
LINE_HEIGHT_RATIO = 1.65     # Line height = font_size × this ratio
TAB_WIDTH = 4                # Tab stop width (in spaces)
MIN_FONT_SIZE = 7            # Smallest font size when auto-reducing

# Font family definitions (ordered by preference)
FONT_FAMILIES = {
    'cascadia':  '"Cascadia Code","Fira Code","JetBrains Mono","Consolas","Courier New",monospace',
    'firacode':  '"Fira Code","Cascadia Code","JetBrains Mono","Consolas","Courier New",monospace',
    'jetbrains': '"JetBrains Mono","Cascadia Code","Fira Code","Consolas","Courier New",monospace',
    'consolas':  '"Consolas","Courier New","Cascadia Code","Fira Code",monospace',
    'courier':   '"Courier New","Consolas","Cascadia Code",monospace',
    'sourcecode': '"Source Code Pro","Cascadia Code","Fira Code","Consolas",monospace',
}

# ===== LAYOUT (A4 at 96 DPI = 794 × 1123 px) =====
A4_W, A4_H = 794, 1123
HDR_H = 60            # Header bar height
PAD_L = 68            # Left padding (gutter + gap)
PAD_R = 36            # Right margin
PAD_T = 72            # Top padding (header bottom + gap)
PAD_B = 28            # Bottom margin
CONTENT_W = A4_W - PAD_L - PAD_R    # ~690px for code
CONTENT_H = A4_H - PAD_T - PAD_B    # ~1023px for code

# ===== COLOR SCHEME (light theme) =====
KW = {'void','char','int','u8','u16','u32','uchar','unsigned',
      'for','if','else','while','switch','case','break','return',
      'static','bit','sbit','xdata','idata','code','interrupt',
      'do','default','continue','struct','typedef','enum','const',
      '#ifndef','#define','#endif','#ifdef','extern'}
RG = {'P0','P1','P2','P3','P4','P5','P6','P7','RST','SCLK','IO','SCK'}
CO = {'keyword':'#d63384','register':'#e8590c','macro':'#099268',
      'number':'#2b8a3e','string':'#099268','comment':'#868e96',
      'var':'#1971c2','text':'#212529'}
BG       = '#ffffff'
HDR_BG   = '#f1f3f5'
HDR_BD   = '#dee2e6'
GT_BG    = '#f8f9fa'
GT_BD    = '#e9ecef'
LN_COLOR = '#868e96'
TRUNC_CLR = '#e74c3c'   # Truncation indicator color ("…")

# Character width ratio for monospace fonts (pixels per px of font-size)
CHAR_RATIO = 0.60


def tokenize(line):
    """Tokenize a line into (text, type) pairs for syntax highlighting."""
    t, i, n = [], 0, len(line)
    while i < n:
        if line[i] == '#':
            j = i + 1
            while j < n and line[j] != '\n': j += 1
            t.append((line[i:j], 'macro')); break
        if line[i:i+2] == '//':
            t.append((line[i:], 'comment')); break
        if line[i:i+2] == '/*':
            j = i + 2
            while j < n and line[j:j+2] != '*/': j += 1
            if j < n: j += 2
            t.append((line[i:j], 'comment')); break
        if line[i] in '"\'':
            q = line[i]
            j = i + 1
            while j < n and line[j] != q:
                if line[j] == '\\': j += 1
                j += 1
            if j < n: j += 1
            t.append((line[i:j], 'string')); i = j; continue
        if line[i] in ' \t':
            j = i
            while j < n and line[j] in ' \t': j += 1
            t.append((line[i:j], 'space')); i = j; continue
        if line[i].isdigit() or (line[i] == '0' and i+1 < n and line[i+1] in 'xXbB'):
            if line[i] == '0' and i+1 < n and line[i+1] in 'xXbB': j = i + 2
            else: j = i
            while j < n and (line[j].isalnum() or line[j] in '.xXa-fA-FbBoOdD'): j += 1
            t.append((line[i:j], 'number')); i = j; continue
        if line[i].isalpha() or line[i] == '_':
            j = i
            while j < n and (line[j].isalnum() or line[j] == '_'): j += 1
            w = line[i:j]
            if w in KW: t.append((w, 'keyword'))
            elif w in RG: t.append((w, 'register'))
            else: t.append((w, 'text'))
            i = j; continue
        t.append((line[i], 'text')); i += 1
    if not t:
        t.append(('', 'space'))
    return t


def compute_layout(lines, font_size, font_family, line_height_ratio):
    """Compute rendering constants for given font and content."""
    fs = font_size
    cw = fs * CHAR_RATIO                   # character width in px
    lh = fs * line_height_ratio            # line height in px

    # Compute gutter width from maximum line number digits
    max_ln = len(str(len(lines)))
    gutter = max(44, max_ln * cw + 20)     # at least 44px
    left_gap = 12
    code_x = gutter + left_gap
    code_w = A4_W - code_x - PAD_R

    # Compute text baseline offset for vertical centering in line height
    baseline_ofs = fs * 0.85

    return fs, cw, lh, gutter, code_x, code_w, baseline_ofs


def compute_optimal_font(lines, base_fs, min_fs, line_height_ratio):
    """Auto-calculate optimal font size to fit the longest line into A4 width."""
    # Estimate gutter width for line numbers
    max_ln_digits = len(str(len(lines)))
    est_gutter = max(44, max_ln_digits * (base_fs * CHAR_RATIO) + 20)
    est_code_x = est_gutter + 12
    est_code_w = A4_W - est_code_x - PAD_R

    # Find longest code line (ignoring trailing newline)
    max_chars = 0
    for line in lines:
        raw = line.rstrip('\n').rstrip('\r')
        # For tab characters, approximate display width
        display_chars = 0
        i = 0
        while i < len(raw):
            if raw[i] == '\t':
                display_chars += TAB_WIDTH - (display_chars % TAB_WIDTH)
            else:
                display_chars += 1
            i += 1
        if display_chars > max_chars:
            max_chars = display_chars

    if max_chars == 0:
        max_chars = 1

    # Font size that fits the longest line into content width
    ideal_fs = est_code_w / (max_chars * CHAR_RATIO)

    # Clamp between min_fs and base_fs
    fs = max(min_fs, min(base_fs, ideal_fs))

    # Recalculate gutter with actual font size (slightly different)
    est_gutter2 = max(44, max_ln_digits * (fs * CHAR_RATIO) + 20)
    est_code_x2 = est_gutter2 + 12
    est_code_w2 = A4_W - est_code_x2 - PAD_R

    # Recalculate with updated gutter
    ideal_fs2 = est_code_w2 / (max_chars * CHAR_RATIO)
    fs = max(min_fs, min(base_fs, ideal_fs2))

    return fs


def gen_svg_page(pg_lines, start_ln, page_num, total_pages, total_lines,
                 fname, font_key, fs, lh, cw, gutter, code_x, code_w,
                 baseline_ofs, is_truncated_width):
    """Generate an A4 SVG page with syntax-highlighted code."""
    font_stack = FONT_FAMILIES.get(font_key, FONT_FAMILIES['cascadia'])
    ff_sans = 'Arial,Helvetica,sans-serif'

    out = []
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {A4_W} {A4_H}">')
    out.append(f'<defs>')
    out.append(f'  <clipPath id="pageClip"><rect x="0" y="0" width="{A4_W}" height="{A4_H}"/></clipPath>')
    out.append(f'</defs>')
    out.append(f'<g clip-path="url(#pageClip)">')

    # Background
    out.append(f'<rect width="{A4_W}" height="{A4_H}" fill="{BG}"/>')

    # Header bar
    out.append(f'<rect x="0" y="0" width="{A4_W}" height="{HDR_H}" fill="{HDR_BG}"/>')
    out.append(f'<line x1="0" y1="{HDR_H}" x2="{A4_W}" y2="{HDR_H}" stroke="{HDR_BD}" stroke-width="1.5"/>')

    # Header text: file name + page info + font info
    font_label = font_key.capitalize()
    out.append(f'<text x="20" y="24" fill="#343a40" font-size="16" font-family="{ff_sans}" font-weight="700">📄 {fname}</text>')
    out.append(f'<text x="20" y="44" fill="#868e96" font-size="11" font-family="{ff_sans}">第 {page_num} 页 · 共 {total_pages} 页 · {total_lines} 行 · {font_label} {fs}px</text>')

    # Right-side info: page X of Y
    if is_truncated_width:
        out.append(f'<text x="{A4_W - 20}" y="24" fill="{TRUNC_CLR}" font-size="11" font-family="{ff_sans}" text-anchor="end">✂ 行过长已截断</text>')

    # Gutter (line number background)
    out.append(f'<rect x="0" y="{HDR_H}" width="{gutter + 8}" height="{A4_H - HDR_H}" fill="{GT_BG}"/>')
    out.append(f'<line x1="{gutter + 8}" y1="{HDR_H}" x2="{gutter + 8}" y2="{A4_H}" stroke="{GT_BD}" stroke-width="1"/>')

    # Code content area (with clip to prevent overflow)
    code_area_w = code_x + code_w + PAD_R
    out.append(f'<clipPath id="codeClip"><rect x="{PAD_L}" y="{PAD_T}" width="{code_w}" height="{CONTENT_H}"/></clipPath>')
    out.append(f'<g clip-path="url(#codeClip)">')

    # Render each line
    for idx, line in enumerate(pg_lines):
        line_y = PAD_T + idx * lh
        text_baseline = line_y + baseline_ofs
        ln = start_ln + idx

        # Line number
        out.append(f'<text x="{gutter - 8}" y="{text_baseline:.1f}" fill="{LN_COLOR}" '
                   f'text-anchor="end" font-size="{fs - 1}" font-family="{font_stack}">{ln}</text>')

        if not line.strip():
            continue

        # Tokenize and render
        toks = tokenize(line)
        tx = code_x
        for val, typ in toks:
            if typ == 'space':
                # Advance x per character with proper tab stops
                for ch in val:
                    if ch == '\t':
                        # Advance to next tab stop
                        cur_col = int(round(tx / cw))
                        next_stop = ((cur_col // TAB_WIDTH) + 1) * TAB_WIDTH
                        tx = next_stop * cw
                    else:
                        tx += cw
            else:
                c = CO.get(typ, '#212529')
                e = val.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                out.append(f'<text x="{tx:.1f}" y="{text_baseline:.1f}" fill="{c}" '
                           f'font-size="{fs}" font-family="{font_stack}">{e}</text>')
                tx += len(val) * cw

    out.append('</g>')  # end code clip

    # Truncation indicator for lines that exceed content width
    # Check each line; add "…" at the right edge if too long
    for idx, line in enumerate(pg_lines):
        raw = line.rstrip('\n').rstrip('\r')
        display_len = 0
        for ch in raw:
            if ch == '\t':
                display_len += TAB_WIDTH - (display_len % TAB_WIDTH)
            else:
                display_len += 1
        if display_len * cw > code_w:
            line_y = PAD_T + idx * lh
            tb = line_y + baseline_ofs
            marker_x = code_x + code_w - cw
            out.append(f'<text x="{marker_x:.1f}" y="{tb:.1f}" fill="{TRUNC_CLR}" '
                       f'font-size="{fs}" font-family="{font_stack}" font-weight="bold">…</text>')

    # Footer page number
    out.append(f'<text x="{A4_W // 2}" y="{A4_H - 10}" text-anchor="middle" '
               f'fill="#adb5bd" font-size="10" font-family="{ff_sans}">- {page_num} -</text>')

    out.append('</g>')  # end pageClip
    out.append('</svg>')
    return '\n'.join(out)


# ===== MAIN LOOP =====
BASE = os.getcwd()

for fname in FILES:
    src = os.path.join(BASE, fname)
    if not os.path.exists(src):
        print(f'SKIP {fname}')
        continue

    with open(src, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    total = len(lines)

    # Compute optimal font size for this file
    fs = compute_optimal_font(lines, FONT_SIZE, MIN_FONT_SIZE, LINE_HEIGHT_RATIO)

    # Compute layout constants
    _, cw, lh, gutter, code_x, code_w, baseline_ofs = \
        compute_layout(lines, fs, FONT_FAMILIES.get(FONT_KEY), LINE_HEIGHT_RATIO)

    # Compute lines per page from available content height
    lines_per_page = max(1, int(CONTENT_H / lh))

    # Check if any line exceeds the content width (for truncation warning)
    any_truncated = False
    for line in lines:
        raw = line.rstrip('\n').rstrip('\r')
        dl = sum(TAB_WIDTH - (i % TAB_WIDTH) if ch == '\t' else 1
                 for i, ch in enumerate(raw))
        if dl * cw > code_w:
            any_truncated = True
            break

    # Split into pages
    np = (total + lines_per_page - 1) // lines_per_page
    out_dir = os.path.join(BASE, fname + '_images')
    os.makedirs(out_dir, exist_ok=True)

    # Generate SVGs
    for p in range(1, np + 1):
        s = (p - 1) * lines_per_page
        e = min(s + lines_per_page, total)
        svg = gen_svg_page(
            lines[s:e], s + 1, p, np, total, fname,
            FONT_KEY, fs, lh, cw, gutter, code_x, code_w,
            baseline_ofs, any_truncated
        )
        with open(os.path.join(out_dir, f'code_page_{p}.svg'), 'w', encoding='utf-8') as f:
            f.write(svg)

    print(f'{fname}: {total} lines, font={fs}px, {lines_per_page} ln/page, {np} pages -> SVG OK')

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
```

## Customization

| Parameter | Default | Description |
|-----------|---------|-------------|
| `FONT_KEY` | `cascadia` | Font choice: `cascadia`, `firacode`, `jetbrains`, `consolas`, `courier`, `sourcecode` |
| `FONT_SIZE` | `14` | Base font size (px). Auto-reduced if longest line exceeds A4 width. |
| `LINE_HEIGHT_RATIO` | `1.65` | Line spacing relative to font size |
| `TAB_WIDTH` | `4` | Tab stop width (in spaces) |
| `MIN_FONT_SIZE` | `7` | Smallest font size when auto-reducing for wide code |
| `KW` / `RG` | — | Keywords and register/pin names to highlight |
| `CO` | — | Color map for token types |

## How the auto-fit works

1. **Width fit**: finds the longest code line, calculates the font size needed to make it fit within A4's content width (capped at `FONT_SIZE`). If the code is narrow enough, uses `FONT_SIZE`; if too wide, shrinks down to `MIN_FONT_SIZE`.
2. **Lines per page**: from the remaining A4 height (after header/margins), divides by `font_size × LINE_HEIGHT_RATIO`.
3. **Truncation**: if even at `MIN_FONT_SIZE` a line still overflows, a red "…" marker appears at the right edge; content beyond the page is clipped cleanly via SVG clipPath.
4. **Tab stops**: tab characters advance to the next tab stop (`TAB_WIDTH`-character intervals) rather than a fixed 4-space width, preserving original indentation structure.

## Tips

- Always unpack tokens as `for val, typ in tokens` — `val` = code text, `typ` = type name for color lookup
- All SVGs use a fixed A4 viewBox (794×1123 at 96 DPI), so every page is identical in dimensions
- If node PNG conversion is slow, break into smaller batches
- Keep the `_images/` folders (SVG+PNG) for later editing; the PDF is the deliverable
- To use a different DPI for print quality, scale `A4_W` and `A4_H` (e.g., ×2 for 192 DPI: 1588×2246)
