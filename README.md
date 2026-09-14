# code-to-images

> 将源代码文件转换为带行号 + 语法高亮的 A4 图片，并合并为 PDF。
> Convert source code files into A4 images with line numbers, syntax highlighting, then merge to PDF.

**v2.1.0** — 多语言自动识别 · 忠实缩进 · 自动换行 · 双语文档

---

📖 [中文](#chinese) · [English](#english)

---

## 中文说明 / Chinese

> 🇨🇳 中文 | [English](#english)

将源代码文件（`.c`、`.h`、`.py`、`.js`、`.java`、`.go`、`.rs`、`.rb`、`.sh`、`.lua`、`.sql`、`.php`、`.cs`、`.css`、`.html`、`.json`、`.yaml` 等）转换为带**行号**和**语法高亮**的 A4 比例图片，自动合并为一个 PDF。

### 功能

- ✅ **多语言自动识别** — 按文件扩展名自动选择语法规则（无需手动指定语言）
- ✅ **行号** — 自适应装订线宽度（千行文件自动加宽）
- ✅ **语法高亮** — 关键字、寄存器/特殊标识符、宏、数字、字符串、注释分别着色
- ✅ **忠实缩进** — 直接保留源码的实际前导空格 / Tab，C 风格大括号与 Python 风格空格缩进都正确呈现
- ✅ **6 种等宽字体** — Cascadia Code / Fira Code / JetBrains Mono / Consolas / Courier New / Source Code Pro
- ✅ **字号自动适配** — 根据最长代码行自动缩放，填满 A4 宽度
- ✅ **每页行数自适应** — 根据字号和行高自动计算
- ✅ **标点自动换行** — 超宽代码在 `;,(){}[]` 后折行，续行不产生新行号
- ✅ **Tab 制表位** — 正确按制表位对齐
- ✅ **多行注释支持** — `/* */`、`<!-- -->`、`--[[ ]]` 等跨行注释完整灰显
- ✅ **固定 A4 比例** — 794×1123px (96 DPI)，每页尺寸统一
- ✅ **PDF 输出** — 每个源文件一份 PDF

### 支持的语言

| 语言 | 扩展名 | 注释 | 宏/特殊 |
|------|--------|------|---------|
| Python | `.py .pyw` | `#` | — |
| C | `.c .h` | `//` `/* */` | `#` 宏、P0–P7 等寄存器 |
| C++ | `.cpp .cc .cxx .hpp ...` | `//` `/* */` | `#` 宏 |
| Java | `.java` | `//` `/* */` | — |
| JavaScript / TypeScript | `.js .jsx .ts .tsx .mjs` | `//` `/* */` | 反引号模板串 |
| Go | `.go` | `//` `/* */` | — |
| Rust | `.rs` | `//` `/* */` | — |
| Ruby | `.rb` | `#` | — |
| Shell | `.sh .bash .zsh` | `#` | 反引号串 |
| Lua | `.lua` | `--` `--[[ ]]` | — |
| SQL | `.sql` | `--` `/* */` | — |
| PHP | `.php .php3 ...` | `#` `//` `/* */` | — |
| C# | `.cs` | `//` `/* */` | — |
| CSS | `.css .scss .less` | `//` `/* */` | — |
| HTML / XML | `.html .htm .xml .svg .vue` | `<!-- -->` | — |
| JSON | `.json .jsonc .json5` | （无） | true/false/null |
| YAML | `.yml .yaml` | `#` | — |

> 未识别的扩展名会回退到通用配置（关键字为空，`#` 视为注释，`//` 与 `/* */` 为注释），保证仍可正常出图。

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
FILES = ['main.c', 'game.py', 'app.js', 'schema.sql']
```

#### 提高打印质量（300 DPI）

```python
A4_W, A4_H = 2480, 3508  # A4 at 300 DPI
```

#### 切换字体

```python
FONT_KEY = '***'  # cascadia / firacode / jetbrains / consolas / courier / sourcecode
```

### 新增一种语言

在 `gen_code_pdfs.py` 的 `LANG` 字典中增加一项，并在 `EXT2LANG` 里登记扩展名即可。例如新增 Swift：

```python
# 1) 在 LANG 中定义规则
LANG['swift'] = {'name':'Swift',
    'kw': {'func','let','var','if','else','for','while','return','class','struct',
           'enum','switch','case','guard','try','catch','throw','nil','true','false'},
    'sp': set(),
    'hash': None, 'slash': True, 'dash': False,
    'block': ('/*','*/'), 'quotes': '"\'', 'backtick': False}

# 2) 登记扩展名
EXT2LANG['.swift'] = 'swift'
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
| `block` | 块注释 `(开始, 结束)` 元组，或 `None` |
| `quotes` | 字符串引号字符（不含反引号） |
| `backtick` | 是否支持反引号模板串 |

### 自动适配逻辑

1. **语言识别**：按扩展名从 `EXT2LANG` 查表，取 `LANG` 中对应规则；未知扩展名回退通用配置
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

- ✅ **Multi-language auto-detection** — picks syntax rules by file extension (no manual language selection)
- ✅ **Line numbers** — Adaptive gutter width (auto-widens for 1000+ line files)
- ✅ **Syntax highlighting** — Keywords, registers/special identifiers, macros, numbers, strings, comments
- ✅ **Faithful indentation** — preserves the file's actual leading whitespace / tabs; works for both brace-based and space-based languages
- ✅ **6 monospace fonts** — Cascadia Code / Fira Code / JetBrains Mono / Consolas / Courier New / Source Code Pro
- ✅ **Auto font size** — Scales to fill A4 width based on longest line
- ✅ **Auto lines per page** — Computed from font size and line height
- ✅ **Auto word-wrapping** — Breaks after `;,(){}[]`, continuation lines get no new line number
- ✅ **Tab stops** — Proper tab alignment
- ✅ **Multi-line comments** — Full `/* */`, `<!-- -->`, `--[[ ]]` cross-line support, rendered in gray
- ✅ **Fixed A4 ratio** — 794×1123px (96 DPI), uniform page dimensions
- ✅ **PDF output** — One PDF per source file

### Supported languages

| Language | Extensions | Comments | Macros / special |
|----------|------------|----------|------------------|
| Python | `.py .pyw` | `#` | — |
| C | `.c .h` | `//` `/* */` | `#` macro, P0–P7 registers |
| C++ | `.cpp .cc .cxx .hpp ...` | `//` `/* */` | `#` macro |
| Java | `.java` | `//` `/* */` | — |
| JavaScript / TypeScript | `.js .jsx .ts .tsx .mjs` | `//` `/* */` | backtick templates |
| Go | `.go` | `//` `/* */` | — |
| Rust | `.rs` | `//` `/* */` | — |
| Ruby | `.rb` | `#` | — |
| Shell | `.sh .bash .zsh` | `#` | backtick strings |
| Lua | `.lua` | `--` `--[[ ]]` | — |
| SQL | `.sql` | `--` `/* */` | — |
| PHP | `.php .php3 ...` | `#` `//` `/* */` | — |
| C# | `.cs` | `//` `/* */` | — |
| CSS | `.css .scss .less` | `//` `/* */` | — |
| HTML / XML | `.html .htm .xml .svg .vue` | `<!-- -->` | — |
| JSON | `.json .jsonc .json5` | (none) | true/false/null |
| YAML | `.yml .yaml` | `#` | — |

> Unknown extensions fall back to a generic config (no keywords, `#` as comment, `//` and `/* */` as comments) so rendering still succeeds.

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
FILES = ['main.c', 'game.py', 'app.js', 'schema.sql']
```

#### Print quality (300 DPI)

```python
A4_W, A4_H = 2480, 3508  # A4 at 300 DPI
```

#### Change font

```python
FONT_KEY = '***'  # cascadia / firacode / jetbrains / consolas / courier / sourcecode
```

### Add a new language

Add an entry to the `LANG` dictionary and register its extension in `EXT2LANG`. Example for Swift:

```python
LANG['swift'] = {'name':'Swift',
    'kw': {'func','let','var','if','else','for','while','return','class','struct',
           'enum','switch','case','guard','try','catch','throw','nil','true','false'},
    'sp': set(),
    'hash': None, 'slash': True, 'dash': False,
    'block': ('/*','*/'), 'quotes': '"\'', 'backtick': False}
EXT2LANG['.swift'] = 'swift'
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
| `block` | Block comment `(start, end)` tuple, or `None` |
| `quotes` | String quote chars (excluding backtick) |
| `backtick` | Enable backtick template strings |

### Auto-fit Logic

1. **Language detection**: lookup extension in `EXT2LANG`, fetch rule from `LANG`; unknown extensions fall back to generic config
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
