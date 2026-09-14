#!/usr/bin/env python3
"""Batch convert code files -> A4 images (SVG+PNG) + one PDF per file.

Multi-language build (v2.1.0):
  - Language auto-detection by file extension
  - Per-language keyword / comment / string / special-token rules
  - Faithful indentation: the file's actual leading whitespace / tabs are
    preserved (works for both brace-based and space-based languages)
"""
import os, sys, subprocess, json

# ===== CONFIG =====
FILES = ['disp_test.c']          # list of source file names (auto-detected language)
FONT_KEY = 'cascadia'            # cascadia | firacode | jetbrains | consolas | courier | sourcecode
FONT_SIZE = 14
LINE_HEIGHT_RATIO = 1.65
TAB_WIDTH = 4
MIN_FONT_SIZE = 7
WRAP_IDENT = 2

# Optional: full path to the node binary (defaults to "node" on PATH).
NODE_EXE = os.environ.get('NODE_EXE', 'node')

FONT_NAMES = {
    'cascadia':'Cascadia Code','firacode':'Fira Code','jetbrains':'JetBrains Mono',
    'consolas':'Consolas','courier':'Courier New','sourcecode':'Source Code Pro',
}

A4_W, A4_H = 794, 1123
HDR_H = 60; PAD_R = 36; PAD_T = 72; PAD_B = 28
CONTENT_H = A4_H - PAD_T - PAD_B
CHAR_RATIO = 0.60
WRAP_PUNCT = set(';,(){}[]')

CO = {'keyword':'#d63384','register':'#e8590c','macro':'#9c36b5',
      'number':'#2b8a3e','string':'#099268','comment':'#868e96',
      'var':'#1971c2','text':'#212529'}
BG='#ffffff'; HDR_BG='#f1f3f5'; HDR_BD='#dee2e6'
GT_BG='#f8f9fa'; GT_BD='#e9ecef'; LN_COLOR='#868e96'

# ---------------------------------------------------------------------------
# Language definitions
#   kw      : keyword set (pink)
#   sp      : special identifiers, e.g. MCU registers (orange)
#   hash    : 'comment' | 'macro' | None   (# handling)
#   slash   : // line comment
#   dash    : -- line comment
#   block   : (start, end) block comment tuple, or None
#   quotes  : quote chars for strings (excluding backtick)
#   backtick: template-literal / backtick string support
#   name    : display name
# ---------------------------------------------------------------------------
def S(*parts):
    s = set()
    for p in parts:
        if isinstance(p, (set, list, tuple, frozenset)):
            s |= set(p)
        else:
            s.add(p)
    return s

PY_KW = S('def','class','import','from','return','if','elif','else','for','while','break',
    'continue','in','is','not','and','or','None','True','False','with','as','try','except',
    'finally','raise','lambda','yield','pass','global','nonlocal','assert','del','async',
    'await','print','range','len','list','dict','set','tuple','str','int','float','bool',
    'super','enumerate','zip','map','filter','getattr','setattr','hasattr','type','isinstance',
    'open','exec','eval','property','staticmethod','classmethod','self','__init__','__name__')

C_KW = S('auto','break','case','char','const','continue','default','do','double','else','enum',
    'extern','float','for','goto','if','inline','int','long','register','return','short','signed',
    'sizeof','static','struct','switch','typedef','union','unsigned','void','volatile','while',
    'bit','sbit','xdata','idata','code','interrupt','data','pdata','using','reentrant',
    'u8','u16','u32','u64','uchar','uint','bool','boolean','true','false','NULL')
C_SP = S('P0','P1','P2','P3','P4','P5','P6','P7','RST','SCLK','IO','SCK','T0','T1','TF0','TF1','IE','IP','TMOD','TCON','SCON','PCON')

CXX_KW = S(C_KW, 'class','public','private','protected','new','delete','template','typename','this',
    'virtual','override','final','namespace','using','throw','try','catch','operator','constexpr',
    'const_cast','static_cast','dynamic_cast','reinterpret_cast','friend','explicit','mutable',
    'export','typeid','decltype','noexcept','nullptr','auto','concept','requires','std')

JAVA_KW = S('abstract','assert','boolean','break','byte','case','catch','char','class','const',
    'continue','default','do','double','else','enum','extends','final','finally','float','for',
    'goto','if','implements','import','instanceof','int','interface','long','native','new','package',
    'private','protected','public','return','short','static','strictfp','super','switch','synchronized',
    'this','throw','throws','transient','try','void','volatile','while','true','false','null','var',
    'record','sealed','permits','yield')

JS_KW = S('break','case','catch','class','const','continue','debugger','default','delete','do','else',
    'export','extends','false','finally','for','function','if','import','in','instanceof','new','null',
    'return','super','switch','this','throw','true','try','typeof','var','void','while','with','yield',
    'let','static','async','await','of','enum','interface','type','implements','public','private',
    'protected','readonly','as','from','namespace','declare','abstract','constructor','get','set',
    'keyof','infer','never','unknown','any','string','number','boolean','symbol','bigint','undefined')

GO_KW = S('break','case','chan','const','continue','default','defer','else','fallthrough','for','func',
    'go','goto','if','import','interface','map','package','range','return','select','struct','switch',
    'type','var','nil','true','false','string','int','byte','bool','any','rune','float64','uint')

RUST_KW = S('as','async','await','break','const','continue','crate','dyn','else','enum','extern','false',
    'fn','for','if','impl','in','let','loop','match','mod','move','mut','pub','ref','return','self','Self',
    'static','struct','super','true','trait','type','unsafe','use','where','while','macro_rules',
    'Some','None','Ok','Err','Result','Option','Vec','String','u8','u16','u32','u64','i8','i16','i32','i64',
    'f32','f64','bool','str','char','usize','isize','Box','Arc','Rc')

RUBY_KW = S('BEGIN','END','alias','begin','break','case','class','def','defined?','do','else','elsif',
    'end','ensure','false','for','if','in','module','next','nil','not','or','redo','rescue','retry',
    'return','self','super','then','true','undef','unless','until','when','while','yield','puts','require',
    'attr_accessor','attr_reader','attr_writer')

SH_KW = S('if','then','else','elif','fi','for','while','do','done','case','esac','in','function','return',
    'exit','export','local','echo','read','cd','source','select','until','break','continue','set','unset',
    'shift','let','eval','alias')

LUA_KW = S('and','break','do','else','elseif','end','false','for','function','goto','if','in','local',
    'nil','not','or','repeat','return','then','true','until','while','print','pairs','ipairs','require',
    'type','tostring','tonumber','table','string','math','ipairs')

SQL_KW = S('select','from','where','and','or','not','insert','into','values','update','set','delete',
    'create','table','drop','alter','index','view','database','join','inner','left','right','outer','on',
    'group','by','order','having','limit','distinct','union','all','as','count','sum','avg','min','max',
    'null','is','like','in','between','exists','primary','key','foreign','references','default','constraint',
    'unique','case','when','then','else','end','begin','commit','rollback','transaction','grant','revoke',
    'use','show','describe','with','returning','cast','coalesce')

PHP_KW = S('abstract','and','array','as','break','callable','case','catch','class','clone','const',
    'continue','declare','default','do','echo','else','elseif','empty','enddeclare','endfor','endforeach',
    'endif','endswitch','endwhile','eval','exit','extends','final','finally','for','foreach','function',
    'global','goto','if','implements','include','include_once','instanceof','insteadof','interface','isset',
    'list','namespace','new','or','print','private','protected','public','require','require_once','return',
    'static','switch','throw','trait','try','unset','use','var','while','xor','yield','true','false','null',
    'die','self','parent','static','function')

CS_KW = S('using','namespace','class','public','private','protected','internal','static','void','int',
    'string','bool','double','float','char','var','if','else','for','foreach','while','do','switch','case',
    'break','continue','return','new','null','true','false','this','base','interface','struct','enum',
    'delegate','event','async','await','try','catch','finally','throw','lock','get','set','abstract',
    'sealed','override','virtual','partial','readonly','const','typeof','nameof','object','dynamic','long',
    'short','byte','decimal','uint','ulong','sbyte')

JSON_KW = S('true','false','null')

# Language registry: name -> config
LANG = {
    'python': {'name':'Python','kw':PY_KW,'sp':set(),'hash':'comment','slash':False,'dash':False,
               'block':None,'quotes':'"\'','backtick':False},
    'c':      {'name':'C','kw':C_KW,'sp':C_SP,'hash':'macro','slash':True,'dash':False,
               'block':('/*','*/'),'quotes':'"\'','backtick':False},
    'c++':    {'name':'C++','kw':CXX_KW,'sp':C_SP,'hash':'macro','slash':True,'dash':False,
               'block':('/*','*/'),'quotes':'"\'','backtick':False},
    'java':   {'name':'Java','kw':JAVA_KW,'sp':set(),'hash':None,'slash':True,'dash':False,
               'block':('/*','*/'),'quotes':'"\'','backtick':False},
    'js':     {'name':'JavaScript','kw':JS_KW,'sp':set(),'hash':None,'slash':True,'dash':False,
               'block':('/*','*/'),'quotes':'"\'','backtick':True},
    'go':     {'name':'Go','kw':GO_KW,'sp':set(),'hash':None,'slash':True,'dash':False,
               'block':('/*','*/'),'quotes':'"\'','backtick':False},
    'rust':   {'name':'Rust','kw':RUST_KW,'sp':set(),'hash':None,'slash':True,'dash':False,
               'block':('/*','*/'),'quotes':'"\'','backtick':False},
    'ruby':   {'name':'Ruby','kw':RUBY_KW,'sp':set(),'hash':'comment','slash':False,'dash':False,
               'block':None,'quotes':'"\'','backtick':False},
    'shell':  {'name':'Shell','kw':SH_KW,'sp':set(),'hash':'comment','slash':False,'dash':False,
               'block':None,'quotes':'"\'','backtick':True},
    'lua':    {'name':'Lua','kw':LUA_KW,'sp':set(),'hash':None,'slash':False,'dash':True,
               'block':('--[[',']]'),'quotes':'"\'','backtick':False},
    'sql':    {'name':'SQL','kw':SQL_KW,'sp':set(),'hash':None,'slash':False,'dash':True,
               'block':('/*','*/'),'quotes':'"\'','backtick':False},
    'php':    {'name':'PHP','kw':PHP_KW,'sp':set(),'hash':'comment','slash':True,'dash':False,
               'block':('/*','*/'),'quotes':'"\'','backtick':False},
    'c#':     {'name':'C#','kw':CS_KW,'sp':set(),'hash':None,'slash':True,'dash':False,
               'block':('/*','*/'),'quotes':'"\'','backtick':False},
    'css':    {'name':'CSS','kw':set(),'sp':set(),'hash':None,'slash':True,'dash':False,
               'block':('/*','*/'),'quotes':'"\'','backtick':False},
    'html':   {'name':'HTML','kw':set(),'sp':set(),'hash':None,'slash':False,'dash':False,
               'block':('<!--','-->'),'quotes':'"\'','backtick':False},
    'json':   {'name':'JSON','kw':JSON_KW,'sp':set(),'hash':None,'slash':False,'dash':False,
               'block':None,'quotes':'"\'','backtick':False},
    'yaml':   {'name':'YAML','kw':set(),'sp':set(),'hash':'comment','slash':False,'dash':False,
               'block':None,'quotes':'"\'','backtick':False},
}

# Extension -> language key
EXT2LANG = {
    '.py':'python','.pyw':'python',
    '.c':'c','.h':'c',
    '.cpp':'c++','.cc':'c++','.cxx':'c++','.hpp':'c++','.hh':'c++','.hxx':'c++','.c++':'c++',
    '.java':'java',
    '.js':'js','.jsx':'js','.ts':'js','.tsx':'js','.mjs':'js','.cjs':'js',
    '.go':'go',
    '.rs':'rust',
    '.rb':'ruby',
    '.sh':'shell','.bash':'shell','.zsh':'shell',
    '.lua':'lua',
    '.sql':'sql',
    '.php':'php','.php3':'php','.php4':'php','.php5':'php','.phtml':'php',
    '.cs':'c#',
    '.css':'css','.scss':'css','.less':'css',
    '.html':'html','.htm':'html','.xhtml':'html',
    '.xml':'html','.svg':'html','.vue':'html',
    '.json':'json','.jsonc':'json','.json5':'json',
    '.yml':'yaml','.yaml':'yaml',
}

# Fallback for unknown extensions: minimal, comment-friendly.
DEFAULT_CFG = {'name':'Text','kw':set(),'sp':set(),'hash':'comment','slash':True,
               'dash':False,'block':('/*','*/'),'quotes':'"\'','backtick':False}


def detect_cfg(fname):
    ext = os.path.splitext(fname)[1].lower()
    key = EXT2LANG.get(ext)
    if key and key in LANG:
        return LANG[key]
    return DEFAULT_CFG


def display_len(text):
    n = 0
    for ch in text:
        if ch == '\t':
            n += TAB_WIDTH - (n % TAB_WIDTH)
        else:
            n += 1
    return n


def leading_display(line):
    """Display width of the leading whitespace of a line."""
    n = 0
    for ch in line:
        if ch == '\t':
            n += TAB_WIDTH - (n % TAB_WIDTH)
        elif ch == ' ':
            n += 1
        else:
            break
    return n


def tokenize_line(line, in_block, cfg):
    bstart, bend = cfg.get('block') or ('', '')
    t, i, n = [], 0, len(line)
    if in_block:
        if bstart:
            k = line.find(bend)
        else:
            k = -1
        if k < 0:
            return [(line, 'comment')], True
        t.append((line[:k+len(bend)], 'comment'))
        i = k + len(bend)
        in_block = False
    while i < n:
        c = line[i]
        # block comment
        if bstart and line[i:i+len(bstart)] == bstart:
            j = line.find(bend, i+len(bstart))
            if j < 0:
                return t + [(line[i:], 'comment')], True
            t.append((line[i:j+len(bend)], 'comment'))
            i = j + len(bend)
            continue
        # hash: comment or macro
        if cfg.get('hash') == 'comment' and c == '#':
            t.append((line[i:], 'comment')); break
        if cfg.get('hash') == 'macro' and c == '#' and line[:i].strip() == '':
            t.append((line[i:], 'macro')); break
        # // line comment
        if cfg.get('slash') and c == '/' and i+1 < n and line[i+1] == '/':
            t.append((line[i:], 'comment')); break
        # -- line comment
        if cfg.get('dash') and c == '-' and i+1 < n and line[i+1] == '-':
            t.append((line[i:], 'comment')); break
        # strings (incl. backtick templates)
        str_delims = set(ch for ch in cfg.get('quotes','"\'') if ch in '"\'')
        if cfg.get('backtick'):
            str_delims.add('`')
        if c in str_delims:
            q = c; j = i+1
            while j < n and line[j] != q:
                if line[j] == '\\': j += 1
                j += 1
            if j < n: j += 1
            t.append((line[i:j], 'string')); i = j; continue
        if c in ' \t':
            j = i
            while j < n and line[j] in ' \t': j += 1
            t.append((line[i:j], 'space')); i = j; continue
        if c.isdigit() or (c=='0' and i+1<n and line[i+1] in 'xXbB'):
            if c=='0' and i+1<n and line[i+1] in 'xXbB': j = i+2
            else: j = i
            while j < n and (line[j].isalnum() or line[j] in '.xXa-fA-FbBoOdD'): j += 1
            t.append((line[i:j], 'number')); i = j; continue
        if c.isalpha() or c == '_':
            j = i
            while j < n and (line[j].isalnum() or line[j] == '_'): j += 1
            w = line[i:j]
            if w in cfg['kw']: t.append((w,'keyword'))
            elif w in cfg.get('sp',set()): t.append((w,'register'))
            else: t.append((w,'text'))
            i = j; continue
        t.append((c,'text')); i += 1
    if not t:
        t.append(('','space'))
    return t, False


def tokenize_full(lines, cfg):
    result, in_block = [], False
    for line in lines:
        toks, in_block = tokenize_line(line, in_block, cfg)
        result.append(toks)
    return result


def wrap_line_tokens(tokens, max_px, cw, indent_px):
    text = ''.join(val for val, typ in tokens)
    if not text.strip():
        return [(tokens, False)]
    raw = text
    dl = display_len(raw.rstrip('\r\n'))
    if dl * cw <= max_px:
        return [(tokens, False)]

    max_chars = int(max_px / cw)
    parts = []
    remaining = raw
    is_first = True
    while remaining:
        avail = max_chars if is_first else int((max_px - indent_px) / cw)
        if avail < 10:
            avail = max_chars
        rem_dl = display_len(remaining.rstrip('\r\n'))
        limit_px = max_px if is_first else max_px - indent_px
        if rem_dl * cw <= limit_px:
            parts.append((tokenize_line(remaining, False, DEFAULT_CFG)[0], not is_first))
            break
        wrap_pos = -1
        pos = 0
        for i, ch in enumerate(remaining):
            if ch == '\t':
                pos += TAB_WIDTH - (pos % TAB_WIDTH)
            else:
                pos += 1
            if ch in WRAP_PUNCT:
                wrap_pos = i + 1
            elif ch == ' ' and pos > avail * 0.6:
                wrap_pos = i + 1
            if pos > avail and wrap_pos > 0:
                break
        if wrap_pos <= 0:
            pos = 0
            for i, ch in enumerate(remaining):
                if ch == '\t':
                    pos += TAB_WIDTH - (pos % TAB_WIDTH)
                else:
                    pos += 1
                if pos > avail:
                    wrap_pos = i
                    break
            if wrap_pos <= 0 or wrap_pos >= len(remaining):
                wrap_pos = len(remaining)
        if wrap_pos >= len(remaining):
            parts.append((tokenize_line(remaining, False, DEFAULT_CFG)[0], not is_first))
            break
        seg = remaining[:wrap_pos]
        parts.append((tokenize_line(seg, False, DEFAULT_CFG)[0], not is_first))
        remaining = remaining[wrap_pos:]
        is_first = False
    return parts


def compute_layout(lines, font_size):
    fs = round(font_size, 1)
    cw = round(fs * CHAR_RATIO, 1)
    lh = round(fs * LINE_HEIGHT_RATIO, 1)
    max_ln = len(str(len(lines)))
    gutter = round(max(44, max_ln * cw + 20), 1)
    code_x = round(gutter + 12, 1)
    code_w = round(A4_W - code_x - PAD_R, 1)
    baseline_ofs = round(fs * 0.85, 1)
    return fs, cw, lh, gutter, code_x, code_w, baseline_ofs


def compute_optimal_font(lines, base_fs, min_fs):
    max_digits = len(str(len(lines)))
    est_g = max(44, max_digits * (base_fs * CHAR_RATIO) + 20)
    est_w = A4_W - est_g - 12 - PAD_R
    max_chars = max((display_len(l.rstrip('\r\n')) for l in lines), default=1)
    if max_chars == 0: max_chars = 1
    fs = max(min_fs, min(base_fs, est_w / (max_chars * CHAR_RATIO)))
    est_g2 = max(44, max_digits * (fs * CHAR_RATIO) + 20)
    est_w2 = A4_W - est_g2 - 12 - PAD_R
    fs = max(min_fs, min(base_fs, est_w2 / (max_chars * CHAR_RATIO)))
    return round(fs, 1)


def gen_svg_page(display_lines, total_lines, page_num, total_pages,
                 fname, lang, font_key, fs, cw, lh, gutter, code_x, code_w, baseline_ofs):
    fn = FONT_NAMES.get(font_key, 'Cascadia Code')
    font_family = '"' + fn + '","Fira Code","Consolas","Courier New",monospace'
    ff_sans = 'Arial, Helvetica, sans-serif'
    wrap_px = WRAP_IDENT * cw

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {A4_W} {A4_H}">']
    out.append('<defs>')
    out.append(f'<clipPath id="pageClip"><rect x="0" y="0" width="{A4_W}" height="{A4_H}"/></clipPath>')
    out.append(f'<clipPath id="codeClip"><rect x="{code_x}" y="{PAD_T}" width="{code_w}" height="{CONTENT_H}"/></clipPath>')
    out.append('</defs>')
    out.append(f'<g clip-path="url(#pageClip)">')

    out.append(f'<rect width="{A4_W}" height="{A4_H}" fill="{BG}"/>')
    out.append(f'<rect x="0" y="0" width="{A4_W}" height="{HDR_H}" fill="{HDR_BG}"/>')
    out.append(f'<line x1="0" y1="{HDR_H}" x2="{A4_W}" y2="{HDR_H}" stroke="{HDR_BD}" stroke-width="1.5"/>')

    fl = font_key.capitalize()
    out.append(f'<text x="20" y="24" fill="#343a40" font-size="16" font-family="{ff_sans}" font-weight="700">FILE {fname}</text>')
    out.append(f'<text x="20" y="44" fill="#868e96" font-size="11" font-family="{ff_sans}">Pg {page_num}/{total_pages}  Lns {total_lines}  {lang}  Font {fl} {fs}px</text>')

    out.append(f'<rect x="0" y="{HDR_H}" width="{gutter+8}" height="{A4_H-HDR_H}" fill="{GT_BG}"/>')
    out.append(f'<line x1="{gutter+8}" y1="{HDR_H}" x2="{gutter+8}" y2="{A4_H}" stroke="{GT_BD}" stroke-width="1"/>')

    for idx, (tokens, is_cont, src_ln, lead) in enumerate(display_lines):
        if not src_ln:
            continue
        ly = PAD_T + idx * lh
        tb = ly + baseline_ofs
        out.append(f"<text x=\"{gutter-8}\" y=\"{tb:.1f}\" fill=\"{LN_COLOR}\" text-anchor=\"end\" font-size=\"{fs-1}\" font-family=\'{font_family}\'>{src_ln}</text>")

    out.append(f'<g clip-path="url(#codeClip)">')
    for idx, (tokens, is_cont, src_ln, lead) in enumerate(display_lines):
        ly = PAD_T + idx * lh
        tb = ly + baseline_ofs
        start_x = code_x + lead * cw
        tx = start_x
        seen_code = False
        for val, typ in tokens:
            if typ == 'space':
                if not seen_code:
                    continue
                for ch in val:
                    if ch == '\t':
                        col = int(round((tx - start_x) / cw))
                        ns = ((col // TAB_WIDTH) + 1) * TAB_WIDTH
                        tx = start_x + ns * cw
                    else:
                        tx += cw
            else:
                seen_code = True
                c = CO.get(typ, '#212529')
                e = val.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
                out.append(f"<text x=\"{tx:.1f}\" y=\"{tb:.1f}\" fill=\"{c}\" font-size=\"{fs}\" font-family=\'{font_family}\'>{e}</text>")
                tx += len(val) * cw
    out.append('</g>')

    out.append(f'<text x="{A4_W//2}" y="{A4_H-10}" text-anchor="middle" fill="#adb5bd" font-size="10" font-family="{ff_sans}">- {page_num} -</text>')
    out.append('</g></svg>')
    return '\n'.join(out)


# ===== MAIN =====
BASE = os.getcwd()
for fname in FILES:
    src = os.path.join(BASE, fname)
    if not os.path.exists(src):
        print(f'SKIP {fname}')
        continue
    cfg = detect_cfg(fname)
    with open(src, 'r', encoding='utf-8') as f:
        lines = [l.rstrip('\r\n') for l in f.readlines()]

    all_tokens = tokenize_full(lines, cfg)
    all_lead = [leading_display(l) for l in lines]
    fs = compute_optimal_font(lines, FONT_SIZE, MIN_FONT_SIZE)
    fs, cw, lh, gutter, code_x, code_w, baseline_ofs = compute_layout(lines, fs)
    lpp = max(1, int(CONTENT_H / lh))

    display_lines = []
    for idx, toks in enumerate(all_tokens):
        lead = all_lead[idx]
        avail_w = code_w - lead * cw
        indent_px = (lead + WRAP_IDENT) * cw
        wrapped = wrap_line_tokens(toks, avail_w, cw, indent_px)
        for i, (seg, isc) in enumerate(wrapped):
            cl = lead if i == 0 else lead + WRAP_IDENT
            display_lines.append((seg, isc, idx+1 if i == 0 else None, cl))

    td = len(display_lines)
    np = (td + lpp - 1) // lpp
    out_dir = os.path.join(BASE, fname + '_images')
    os.makedirs(out_dir, exist_ok=True)

    for p in range(1, np+1):
        s = (p-1) * lpp
        e = min(s + lpp, td)
        svg = gen_svg_page(display_lines[s:e], len(lines), p, np, fname, cfg['name'],
                           FONT_KEY, fs, cw, lh, gutter, code_x, code_w, baseline_ofs)
        with open(os.path.join(out_dir, f'code_page_{p}.svg'), 'w', encoding='utf-8') as f:
            f.write(svg)

    wraps = td - len(lines)
    print(f'{fname} [{cfg["name"]}]: {len(lines)} src -> {td} disp ({wraps} wraps), font={fs}px, {lpp} ln/pg, {np} pgs -> SVG OK')

    js = ('const fs=require("fs");const{Resvg}=require("@resvg/resvg-js");'
          'const dir=' + json.dumps(out_dir.replace('\\','\\\\')) + ';'
          'for(let p=1;p<='+str(np)+';p++){'
          'const s=dir+"\\\\code_page_"+p+".svg";'
          'const pn=dir+"\\\\code_page_"+p+".png";'
          'try{const d=fs.readFileSync(s,"utf8");const r=new Resvg(d,{background:"#ffffff"});'
          'const b=r.render();fs.writeFileSync(pn,b.asPng())}'
          'catch(e){console.log("  ERR:"+p+" "+e.message)}}')
    subprocess.run([NODE_EXE, '-e', js], check=True)
    print(f'{fname}: PNG OK')

    import img2pdf
    pngs = sorted([os.path.join(out_dir,f) for f in os.listdir(out_dir) if f.endswith('.png')],
                  key=lambda x: int(os.path.basename(x).replace('code_page_','').replace('.png','')))
    pdf_path = os.path.join(BASE, fname+'.pdf')
    with open(pdf_path, 'wb') as f:
        f.write(img2pdf.convert(pngs))
    print(f'{fname}: PDF -> {pdf_path} ({os.path.getsize(pdf_path)//1024}KB)')

print('\n=== All done! ===')
