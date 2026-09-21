# code-to-images

> 将源代码文件转换为带行号 + 语法高亮的 A4 图片，并合并为 PDF。
> Convert source code files into A4 images with line numbers, syntax highlighting, then merge to PDF.

**v2.2.0** — 49 种语言自动识别 · 忠实缩进 · 自动换行 · 双语文档 / 49-language auto-detection · faithful indentation · auto word-wrapping · bilingual docs

---

📖 [中文](#chinese) · [English](#english)

---

## 中文说明 / Chinese

> 🇨🇳 中文 | [English](#english)

将源代码文件转换为带**行号**和**语法高亮**的 A4 比例图片（SVG + PNG），自动合并为一个 PDF。语言按扩展名 / 文件名 / 内容自动识别，无需手动指定。

### 功能

- ✅ **49 种语言自动识别** — 按扩展名 / 文件名 / 内容自动选择语法规则（含 `.m` 内容嗅探与 `Makefile`/`Dockerfile`/`CMakeLists.txt` 文件名识别）
- ✅ **行号** — 自适应装订线宽度（千行文件自动加宽）
- ✅ **语法高亮** — 关键字、寄存器/特殊标识符、宏、数字、字符串、变量、标签、注释分别着色
- ✅ **多行注释** — `/* */`、`<!-- -->`、`--[[ ]]`、`{- -}`、`#= =#`、`(* *)`、`{ }` 等跨行注释完整灰显
- ✅ **三引号字符串** — Python / Julia / 仓颉的 `"""` `'''` 跨行字符串
- ✅ **语言特性高亮** — HTML/XML 标签、`@` 注解与指令、`$` 变量（含 `${}`/`$()`）、Makefile 目标行、YAML 键、Markdown 标题
- ✅ **忠实缩进** — 直接保留源码的实际前导空格 / Tab，C 风格大括号与 Python 风格空格缩进都正确呈现
- ✅ **6 种等宽字体** — Cascadia Code / Fira Code / JetBrains Mono / Consolas / Courier New / Source Code Pro
- ✅ **字号自动适配** — 根据最长代码行自动缩放，填满 A4 宽度
- ✅ **每页行数自适应** — 根据字号和行高自动计算
- ✅ **标点自动换行** — 超宽代码在 `;,(){}[]` 后折行，续行不产生新行号
- ✅ **Tab 制表位** — 正确按制表位对齐
- ✅ **固定 A4 比例** — 794×1123px (96 DPI)，每页尺寸统一
- ✅ **PDF 输出** — 每个源文件一份 PDF

### 支持的语言（49 种）

**脚本 / 动态语言**：Python (`.py .pyw`)、JavaScript (`.js .jsx .mjs .cjs`)、TypeScript (`.ts .tsx .mts .cts`)、Ruby (`.rb`)、Perl (`.pl .pm .t`)、PHP (`.php .php3-5 .phtml`)、Lua (`.lua`)、Shell (`.sh .bash .zsh`)、PowerShell (`.ps1 .psm1 .psd1`)、Batch (`.bat .cmd`)、Visual Basic (`.vb .vba .bas`)、R (`.r`)、MATLAB (`.m`*)、Julia (`.jl`)

**编译型 / 系统语言**：C (`.c .h`)、C++ (`.cpp .cc .cxx .hpp .hh .hxx .c++`)、Arduino (`.ino .pde`)、Go (`.go`)、Rust (`.rs`)、Zig (`.zig`)、Swift (`.swift`)、Kotlin (`.kt .kts`)、Dart (`.dart`)、**仓颉 Cangjie (`.cj`)**、Objective-C (`.m`* `.mm`)、Scala (`.scala .sc`)、Haskell (`.hs .lhs`)、Erlang (`.erl .hrl`)、Elixir (`.ex .exs`)、Clojure (`.clj .cljs .cljc .edn`)、F# (`.fs .fsx .fsi`)、Pascal (`.pas .pp`)、Fortran (`.f .f90 .f95 .f03 .f08 .for`)、Assembly (`.asm .s .nasm`)、Solidity (`.sol`)

**标记 / 配置 / 数据**：Java (`.java`)、C# (`.cs`)、Groovy (`.groovy .gradle`)、CSS (`.css .scss .less`)、HTML/XML (`.html .htm .xhtml .xml .svg .vue`)、JSON (`.json .jsonc .json5`)、YAML (`.yml .yaml`)、INI/TOML (`.ini .cfg .conf .toml .properties`)、Markdown (`.md .markdown`)、LaTeX (`.tex .sty .cls`)、SQL (`.sql`)、Makefile (`Makefile`*)、Dockerfile (`Dockerfile`*)、CMake (`CMakeLists.txt`* `.cmake`)

> \* 特殊识别：`.m` 文件内容嗅探（含 `@interface`/`#import`/`NSString` 视为 Objective-C，否则 MATLAB）；`Makefile`/`Dockerfile`/`CMakeLists.txt` 按文件名识别。未识别的扩展名回退到通用配置，保证仍可正常出图。

### 安装依赖

```bash
npm install -g @resvg/resvg-js
pip install img2pdf
```

> 若 `node` 不在 PATH，可在运行前设置环境变量 `NODE_EXE` 指向 node 可执行文件；若 `@resvg/resvg-js` 安装在本地目录，设置 `NODE_PATH` 指向该 `node_modules`。

### 使用

1. 编辑 `gen_code_pdfs.py` 顶部 `FILES` 列表，填入源文件名
2. 按需修改配置（`FONT_KEY`、`FONT_SIZE` 等）
3. 运行：`python gen_code_pdfs.py`
4. 输出：`文件名.pdf` + `文件名_images/` 目录（SVG + PNG）

#### 批量打印多文件（自动识别各自语言）

```python
FILES = ['main.c', 'game.py', 'app.js', 'schema.sql', 'hello.cj']
```

#### 提高打印质量（300 DPI）

```python
A4_W, A4_H = 2480, 3508  # A4 at 300 DPI
```

#### 切换字体

```python
FONT_KEY = 'cascadia'  # cascadia / firacode / jetbrains / consolas / courier / sourcecode
```

### 新增一种语言

在 `gen_code_pdfs.py` 的 `LANG` 字典中增加一项，并在 `EXT2LANG` 里登记扩展名即可。例如新增仓颉（Cangjie）：

```python
# 1) 定义关键字集（官方 71 个系统保留字）
CJ_KW = S('as','abstract','break','Bool','case','catch','class','const','continue',
    'Rune','do','else','enum','extend','for','func','false','finally','foreign',
    'Float16','Float32','Float64','if','in','is','init','import','interface',
    'Int8','Int16','Int32','Int64','IntNative','let','mut','main','macro','match',
    'Nothing','open','operator','override','prop','public','package','private',
    'protected','quote','redef','return','spawn','super','static','struct',
    'synchronized','try','this','true','type','throw','This','unsafe','Unit',
    'UInt8','UInt16','UInt32','UInt64','UIntNative','var','VArray','where','while')

# 2) 在 LANG 中定义规则
LANG['cangjie'] = {'name':'Cangjie', 'kw': CJ_KW, 'sp': set(),
    'hash': None, 'slash': True, 'dash': False,
    'block': ('/*','*/'), 'quotes': '"\'', 'backtick': False,
    'triple': ('"""',), 'atword': True}

# 3) 登记扩展名
EXT2LANG['.cj'] = 'cangjie'
```

配置字段说明：

| 字段 | 含义 |
|------|------|
| `name` | 页眉显示的语言名 |
| `kw` | 关键字集合（粉色） |
| `sp` | 特殊标识符，如 MCU 寄存器（橙色） |
| `hash` | `'comment'` / `'macro'` / `None`（`#` 的处理方式） |
| `slash` | 是否支持 `//` 行注释 |
| `dash` | 是否支持 `--` 行注释 |
| `semi` / `bang` / `apos` | 是否支持 `;` / `!` / `'` 行注释 |
| `block` | 块注释 `(开始, 结束)` 元组，或 `None` |
| `quotes` | 字符串引号字符（不含反引号） |
| `backtick` | 是否支持反引号模板串 |
| `triple` | 三引号字符串定界符元组，如 `('"""', "'''")` |
| `atword` | 是否高亮 `@` 注解 / 指令 / 装饰器 |
| `dollar` | 是否高亮 `$` 变量（支持 `${}`、`$()`） |
| `tags` | 是否高亮 HTML/XML 标签 |
| `colon_target` | 是否高亮 Makefile 目标行 / YAML 键 |
| `hashline` | Markdown 标题整行高亮颜色 |

### 自动适配逻辑

1. **语言识别**：按扩展名查 `EXT2LANG`，再按文件名查 `BASE2LANG`，必要时内容嗅探（`.m`），取 `LANG` 中对应规则；未知扩展名回退通用配置
2. **宽度适配**：扫描所有代码行，找到最长行（正确处理 Tab），计算字号使其刚好占满 A4 内容宽度，上限 `FONT_SIZE`，下限 `MIN_FONT_SIZE`
3. **缩进计算**：保留源码实际前导空格 / Tab 的显示宽度，作为每行缩进像素
4. **每页行数**：A4 可用高度 ÷ (`字号 × LINE_HEIGHT_RATIO`)
5. **标点换行**：超宽行在 `;,(){}[]` 后折行，可用宽度扣除该行缩进，续行不产生新行号
6. **渲染**：行号在 codeClip 外渲染（始终可见），代码在 clip 内渲染，font-family 正确引用

### 输出结构

```
filename.c_images/
├── code_page_1.svg      ← 矢量 SVG（可编辑）
├── code_page_1.png      ← PNG 图片
├── code_page_2.svg
├── code_page_2.png
└── ...
filename.c.pdf           ← 最终 PDF
```

---

## English / English

> 🇬🇧 English | [中文](#chinese)

> Convert source code files into A4 images with line numbers and syntax highlighting, then merge to PDF.

### Features

- ✅ **49-language auto-detection** — picks syntax rules by extension / basename / content sniff (incl. `.m` content sniffing and `Makefile`/`Dockerfile`/`CMakeLists.txt` basename detection)
- ✅ **Line numbers** — Adaptive gutter width (auto-widens for 1000+ line files)
- ✅ **Syntax highlighting** — Keywords, registers/special identifiers, macros, numbers, strings, variables, tags, comments
- ✅ **Multi-line comments** — `/* */`, `<!-- -->`, `--[[ ]]`, `{- -}`, `#= =#`, `(* *)`, `{ }` cross-line support
- ✅ **Triple-quoted strings** — `"""` `'''` for Python / Julia / Cangjie
- ✅ **Language-specific tokens** — HTML/XML tags, `@` annotations & directives, `$` variables (incl. `${}`/`$()`), Makefile targets, YAML keys, Markdown headings
- ✅ **Faithful indentation** — preserves the file's actual leading whitespace / tabs; works for both brace-based and space-based languages
- ✅ **6 monospace fonts** — Cascadia Code / Fira Code / JetBrains Mono / Consolas / Courier New / Source Code Pro
- ✅ **Auto font size** — Scales to fill A4 width based on longest line
- ✅ **Auto lines per page** — Computed from font size and line height
- ✅ **Auto word-wrapping** — Breaks after `;,(){}[]`, continuation lines get no new line number
- ✅ **Tab stops** — Proper tab alignment
- ✅ **Fixed A4 ratio** — 794×1123px (96 DPI), uniform page dimensions
- ✅ **PDF output** — One PDF per source file

### Supported languages (49)

**Scripting / dynamic**: Python (`.py .pyw`), JavaScript (`.js .jsx .mjs .cjs`), TypeScript (`.ts .tsx .mts .cts`), Ruby (`.rb`), Perl (`.pl .pm .t`), PHP (`.php .php3-5 .phtml`), Lua (`.lua`), Shell (`.sh .bash .zsh`), PowerShell (`.ps1 .psm1 .psd1`), Batch (`.bat .cmd`), Visual Basic (`.vb .vba .bas`), R (`.r`), MATLAB (`.m`*), Julia (`.jl`)

**Compiled / systems**: C (`.c .h`), C++ (`.cpp .cc .cxx .hpp .hh .hxx .c++`), Arduino (`.ino .pde`), Go (`.go`), Rust (`.rs`), Zig (`.zig`), Swift (`.swift`), Kotlin (`.kt .kts`), Dart (`.dart`), **Cangjie (`.cj`)**, Objective-C (`.m`* `.mm`), Scala (`.scala .sc`), Haskell (`.hs .lhs`), Erlang (`.erl .hrl`), Elixir (`.ex .exs`), Clojure (`.clj .cljs .cljc .edn`), F# (`.fs .fsx .fsi`), Pascal (`.pas .pp`), Fortran (`.f .f90 .f95 .f03 .f08 .for`), Assembly (`.asm .s .nasm`), Solidity (`.sol`)

**Markup / config / data**: Java (`.java`), C# (`.cs`), Groovy (`.groovy .gradle`), CSS (`.css .scss .less`), HTML/XML (`.html .htm .xhtml .xml .svg .vue`), JSON (`.json .jsonc .json5`), YAML (`.yml .yaml`), INI/TOML (`.ini .cfg .conf .toml .properties`), Markdown (`.md .markdown`), LaTeX (`.tex .sty .cls`), SQL (`.sql`), Makefile (`Makefile`*), Dockerfile (`Dockerfile`*), CMake (`CMakeLists.txt`* `.cmake`)

> \* Special detection: `.m` files are sniffed (files with `@interface`/`#import`/`NSString` are Objective-C, otherwise MATLAB); `Makefile`/`Dockerfile`/`CMakeLists.txt` are detected by basename. Unknown extensions fall back to a generic config so rendering still succeeds.

### Prerequisites

```bash
npm install -g @resvg/resvg-js
pip install img2pdf
```

> If `node` is not on PATH, set the `NODE_EXE` environment variable to the node binary before running. If `@resvg/resvg-js` is installed locally, set `NODE_PATH` to that `node_modules` directory.

### Usage

1. Edit the `FILES` list at the top of `gen_code_pdfs.py`
2. Configure `FONT_KEY`, `FONT_SIZE`, etc.
3. Run: `python gen_code_pdfs.py`
4. Output: `filename.pdf` + `filename_images/` directory (SVG + PNG)

#### Batch processing (auto-detects each language)

```python
FILES = ['main.c', 'game.py', 'app.js', 'schema.sql', 'hello.cj']
```

#### Print quality (300 DPI)

```python
A4_W, A4_H = 2480, 3508  # A4 at 300 DPI
```

#### Change font

```python
FONT_KEY = 'cascadia'  # cascadia / firacode / jetbrains / consolas / courier / sourcecode
```

### Add a new language

Add an entry to the `LANG` dictionary and register its extension in `EXT2LANG`. Example for Cangjie:

```python
# 1) Define the keyword set (official 71 reserved words)
CJ_KW = S('as','abstract','break','Bool','case','catch','class','const','continue',
    'Rune','do','else','enum','extend','for','func','false','finally','foreign',
    'Float16','Float32','Float64','if','in','is','init','import','interface',
    'Int8','Int16','Int32','Int64','IntNative','let','mut','main','macro','match',
    'Nothing','open','operator','override','prop','public','package','private',
    'protected','quote','redef','return','spawn','super','static','struct',
    'synchronized','try','this','true','type','throw','This','unsafe','Unit',
    'UInt8','UInt16','UInt32','UInt64','UIntNative','var','VArray','where','while')

# 2) Add the rule to LANG
LANG['cangjie'] = {'name':'Cangjie', 'kw': CJ_KW, 'sp': set(),
    'hash': None, 'slash': True, 'dash': False,
    'block': ('/*','*/'), 'quotes': '"\'', 'backtick': False,
    'triple': ('"""',), 'atword': True}

# 3) Register the extension
EXT2LANG['.cj'] = 'cangjie'
```

Config fields:

| Field | Meaning |
|-------|---------|
| `name` | Language name shown in page header |
| `kw` | Keyword set (pink) |
| `sp` | Special identifiers, e.g. MCU registers (orange) |
| `hash` | `'comment'` / `'macro'` / `None` (how `#` is handled) |
| `slash` | Enable `//` line comment |
| `dash` | Enable `--` line comment |
| `semi` / `bang` / `apos` | Enable `;` / `!` / `'` line comments |
| `block` | Block comment `(start, end)` tuple, or `None` |
| `quotes` | String quote chars (excluding backtick) |
| `backtick` | Enable backtick template strings |
| `triple` | Triple-quoted string delimiters, e.g. `('"""', "'''")` |
| `atword` | Highlight `@` annotations / directives / decorators |
| `dollar` | Highlight `$` variables (supports `${}`, `$()`) |
| `tags` | Highlight HTML/XML tags |
| `colon_target` | Highlight Makefile targets / YAML keys |
| `hashline` | Markdown heading full-line color |

### Auto-fit Logic

1. **Language detection**: lookup extension in `EXT2LANG`, then basename in `BASE2LANG`, content-sniff when needed (`.m`), fetch rule from `LANG`; unknown extensions fall back to generic config
2. **Width fit**: scan all lines, find the longest, calculate font size to fill A4 content width (capped at `FONT_SIZE`, floored at `MIN_FONT_SIZE`)
3. **Indentation**: preserve the display width of each line's actual leading whitespace / tabs as indent pixels
4. **Lines per page**: A4 available height ÷ (`font_size × LINE_HEIGHT_RATIO`)
5. **Word-wrapping**: lines exceeding available width break after `;,(){}[]`, continuation lines show no extra line number
6. **Rendering**: line numbers outside codeClip (always visible), code content inside clip, font-family properly quoted

### Output Structure

```
filename.c_images/
├── code_page_1.svg      ← Vector SVG (editable)
├── code_page_1.png      ← PNG image
├── code_page_2.svg
├── code_page_2.png
└── ...
filename.c.pdf           ← Final PDF
```

---

## License

MIT
