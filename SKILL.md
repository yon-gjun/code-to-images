---
name: "code-to-images"
description: "Convert code files to A4-ratio PNG/SVG images with line numbers and syntax highlighting, then merge to PDF. 支持中英文双语说明。"
---

# Code → A4 图片 + PDF / A4 Images + PDF

**v2.2.0** — 49 种语言 · 多语言自动识别 · 忠实缩进 · Auto word-wrapping

---

📖 [中文](#chinese) · [English](#english)

---

## 中文说明 / Chinese

> 🇨🇳 中文 | [中文](#chinese)

将源代码文件转换为多页 A4 比例图片（SVG+PNG），然后合并为一个 PDF。

### 功能

- ✅ **49 种语言自动识别** — 按扩展名 / 文件名 / 内容自动选择语法规则：Python、C/C++、Arduino、Java、JavaScript、TypeScript、Go、Rust、Ruby、Shell、Lua、SQL、PHP、C#、CSS、HTML、JSON、YAML、**仓颉 Cangjie**、Kotlin、Swift、Dart、R、Perl、MATLAB、Objective-C、Scala、Haskell、Julia、Zig、Groovy、PowerShell、Batch、Visual Basic、Makefile、Dockerfile、INI/TOML、Markdown、LaTeX、CMake、Solidity、Erlang、Elixir、Clojure、F#、Pascal、Fortran、汇编
- ✅ **多语言注释与字符串** — 跨行块注释（`/* */`、`<!-- -->`、`--[[ ]]`、`{- -}`、`#= =#`、`(* *)`、`{ }` 等）、三引号字符串（Python/Julia 的 `"""` `'''`）、`#`/`//`/`--`/`;`/`!`/`'` 行注释
- ✅ **语言特性高亮** — HTML/XML 标签、`@` 注解与指令（Java/Python/ObjC/Swift）、`$` 变量（Shell/PHP/Perl/PowerShell）、Makefile 目标行与 YAML 键、Markdown 标题
- ✅ **行号** — 自适应装订线宽度
- ✅ **语法高亮** — 关键字、寄存器、宏、数字、字符串、变量、标签、注释分别着色
- ✅ **6 种等宽字体** — Cascadia Code / Fira Code / JetBrains Mono / Consolas / Courier New / Source Code Pro
- ✅ **字号自动适配** — 根据最长行自动缩放，填满 A4 宽度
- ✅ **每页行数自适应** — 根据字号和行高自动计算
- ✅ **忠实缩进** — 保留源码实际前导空格 / Tab，C 风格大括号与 Python 风格空格缩进都正确呈现
- ✅ **代码超宽自动换行** — 在 `;,(){}[]` 标点后折行，续行不产生新行号
- ✅ **Tab 制表位** — 正确按制表位对齐
- ✅ **固定 A4 比例** — 794×1123px (96 DPI)
- ✅ **PDF 输出** — 每个源文件一份 PDF

> 💡 `.m` 文件自动嗅探：含 `@interface`/`#import`/`NSString` 识别为 Objective-C，否则识别为 MATLAB；`Makefile`/`Dockerfile`/`CMakeLists.txt` 按文件名识别。

### 依赖

```bash
npm install -g @resvg/resvg-js
pip install img2pdf
```

### 使用

1. 编辑 `gen_code_pdfs.py` 顶部的 `FILES` 列表，填入源文件名
2. 按需修改 `FONT_KEY`、`FONT_SIZE` 等配置
3. 运行：`python gen_code_pdfs.py`
4. 输出：`文件名.pdf` + `文件名_images/` 目录（中间 SVG/PNG）

### 配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `FONT_KEY` | `cascadia` | 字体：`cascadia`/`firacode`/`jetbrains`/`consolas`/`courier`/`sourcecode` |
| `FONT_SIZE` | `14` | 基础字号 (px)，超宽代码自动缩小 |
| `LINE_HEIGHT_RATIO` | `1.65` | 行高系数 |
| `TAB_WIDTH` | `4` | Tab 制表位宽度 |
| `MIN_FONT_SIZE` | `7` | 自动缩小时的最小字号 |
| `WRAP_IDENT` | `2` | 续行额外缩进字符数 |

---

## English / English

> 🇬🇧 English | [中文](#chinese)

Convert source code files into multi-page A4-ratio images (SVG+PNG), then merge into a single PDF.

### Features

- ✅ **49-language auto-detection** — Picks syntax rules by extension / basename / content sniff: Python, C/C++, Arduino, Java, JavaScript, TypeScript, Go, Rust, Ruby, Shell, Lua, SQL, PHP, C#, CSS, HTML, JSON, YAML, Cangjie, Kotlin, Swift, Dart, R, Perl, MATLAB, Objective-C, Scala, Haskell, Julia, Zig, Groovy, PowerShell, Batch, Visual Basic, Makefile, Dockerfile, INI/TOML, Markdown, LaTeX, CMake, Solidity, Erlang, Elixir, Clojure, F#, Pascal, Fortran, Assembly
- ✅ **Rich comments & strings** — Cross-line block comments (`/* */`, `<!-- -->`, `--[[ ]]`, `{- -}`, `#= =#`, `(* *)`, `{ }`…), triple-quoted strings (Python/Julia `"""` `'''`), `#`/`//`/`--`/`;`/`!`/`'` line comments
- ✅ **Language-specific tokens** — HTML/XML tags, `@` annotations & directives (Java/Python/ObjC/Swift), `$` variables (Shell/PHP/Perl/PowerShell), Makefile targets & YAML keys, Markdown headings
- ✅ **Line numbers** — Adaptive gutter width
- ✅ **Syntax highlighting** — Keywords, registers, macros, numbers, strings, variables, tags, comments
- ✅ **6 monospace fonts** — Cascadia Code / Fira Code / JetBrains Mono / Consolas / Courier New / Source Code Pro
- ✅ **Auto font size** — Scales to fill A4 width based on longest line
- ✅ **Auto lines per page** — Computed from font size and line height
- ✅ **Faithful indentation** — Preserves actual leading whitespace / tabs for both brace-based and space-based languages
- ✅ **Auto word-wrapping** — Breaks after `;,(){}[]`, continuation lines get no new line number
- ✅ **Tab stops** — Proper tab alignment
- ✅ **Fixed A4 ratio** — 794×1123px (96 DPI)
- ✅ **PDF output** — One PDF per source file

> 💡 `.m` content sniffing: files with `@interface`/`#import`/`NSString` are treated as Objective-C, otherwise MATLAB; `Makefile`/`Dockerfile`/`CMakeLists.txt` are detected by basename.

### Prerequisites

```bash
npm install -g @resvg/resvg-js
pip install img2pdf
```

### Usage

1. Edit the `FILES` list at the top of `gen_code_pdfs.py`
2. Configure `FONT_KEY`, `FONT_SIZE`, etc.
3. Run: `python gen_code_pdfs.py`
4. Output: `filename.pdf` + `filename_images/` directory (intermediate SVG/PNG)

### Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `FONT_KEY` | `cascadia` | Font: `cascadia`/`firacode`/`jetbrains`/`consolas`/`courier`/`sourcecode` |
| `FONT_SIZE` | `14` | Base font size (px), auto-reduces for wide code |
| `LINE_HEIGHT_RATIO` | `1.65` | Line height multiplier |
| `TAB_WIDTH` | `4` | Tab stop width |
| `MIN_FONT_SIZE` | `7` | Minimum font size when auto-reducing |
| `WRAP_IDENT` | `2` | Extra indent for continuation lines |

---

## Python Batch Script

Save as `gen_code_pdfs.py` and run with `python gen_code_pdfs.py`:

```python
#!/usr/bin/env python3
"""Batch convert code files -> A4 images + PDF. Multi-language auto-detection."""
import os, sys, subprocess, json

# ===== CONFIG =====
# Language is auto-detected from each file's extension / basename / content (see LANG / EXT2LANG / BASE2LANG below).
FILES = [/* List source files here, e.g. 'main.c', 'game.py', 'app.ts', 'Makefile' */]
FONT_KEY = '***'   # cascadia | firacode | jetbrains | consolas | courier | sourcecode
FONT_SIZE = 14; LINE_HEIGHT_RATIO = 1.65; TAB_WIDTH = 4; MIN_FONT_SIZE = 7; WRAP_IDENT = 2
NODE_EXE = os.environ.get('NODE_EXE', 'node')   # full path to node if not on PATH

FONT_NAMES = {'cascadia':'Cascadia Code','firacode':'Fira Code','jetbrains':'JetBrains Mono',
    'consolas':'Consolas','courier':'Courier New','sourcecode':'Source Code Pro'}
A4_W, A4_H = 794, 1123; HDR_H = 60; PAD_R = 36; PAD_T = 72; PAD_B = 28
CONTENT_H = A4_H - PAD_T - PAD_B; CHAR_RATIO = 0.60; WRAP_PUNCT = set(';,(){}[]')
CO = {'keyword':'#d63384','register':'#e8590c','macro':'#9c36b5',
      'number':'#2b8a3e','string':'#099268','comment':'#868e96','var':'#1971c2','tag':'#0b7285','text':'#212529'}
BG='#ffffff'; HDR_BG='#f1f3f5'; HDR_BD='#dee2e6'; GT_BG='#f8f9fa'; GT_BD='#e9ecef'; LN_COLOR='#868e96'

# Per-language rules (keyword set, comment styles, string quotes, ...).
LANG = {
    'python': {'name':'Python','kw':{'def','class','import','from','return','if','for',...},
               'sp':set(),'hash':'comment','slash':False,'dash':False,'block':None,'quotes':'"\'','backtick':False,
               'triple':('"""',"'''"),'atword':True},
    'c':      {'name':'C','kw':{'void','char','int','for','if','while',...},'sp':{'P0',...,'P7','RST'},
               'hash':'macro','slash':True,'dash':False,'block':('/*','*/'),'quotes':'"\'','backtick':False},
    # ... 40+ languages: see gen_code_pdfs.py (LANG / EXT2LANG / BASE2LANG)
}
EXT2LANG = {'.py':'python', '.c':'c', '.h':'c', '.cpp':'c++', '.java':'java', '.js':'js', '.go':'go',
            '.rs':'rust', '.rb':'ruby', '.sh':'shell', '.lua':'lua', '.sql':'sql', '.php':'php',
            '.cs':'c#', '.css':'css', '.html':'html', '.xml':'html', '.json':'json', '.yaml':'yaml',
            '.ts':'typescript', '.kt':'kotlin', '.swift':'swift', '.m':'ambig_m', '.mm':'objective-c',
            '.r':'r', '.pl':'perl', '.scala':'scala', '.hs':'haskell', '.jl':'julia', '.zig':'zig',
            '.groovy':'groovy', '.ps1':'powershell', '.bat':'batch', '.vb':'vb', '.ino':'arduino',
            '.mk':'makefile', '.ini':'ini', '.toml':'ini', '.md':'markdown', '.tex':'tex',
            '.cmake':'cmake', '.sol':'solidity', '.erl':'erlang', '.ex':'elixir', '.clj':'clojure',
            '.fs':'fsharp', '.pas':'pascal', '.f90':'fortran', '.asm':'assembly'}
BASE2LANG = {'makefile':'makefile','dockerfile':'dockerfile','cmakelists.txt':'cmake'}

# [Full script with LANG/EXT2LANG tables at: gen_code_pdfs.py (local, v2.2.0)]
```
