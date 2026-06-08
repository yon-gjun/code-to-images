# code-to-images

> 将源代码文件转换为带行号 + 语法高亮的 A4 图片，并合并为 PDF。
> Convert source code files into A4 images with line numbers, syntax highlighting, then merge to PDF.

**v2.0** — Auto-fit, font choices, tab stops, width truncation.

---

## 功能 / Features

- ✅ **行号** — 自适应装订线宽度（千行文件自动加宽）
- ✅ **语法高亮** — 关键字、寄存器、宏、数字、字符串、注释分别着色
- ✅ **6 种等宽字体** — Cascadia Code / Fira Code / JetBrains Mono / Consolas / Courier New / Source Code Pro
- ✅ **字号自动适配** — 根据最长代码行自动缩放，代码刚好占满 A4 宽度
- ✅ **每页行数自适应** — 根据字号和行高自动计算，充分利用 A4 高度
- ✅ **Tab 制表位** — 正确按制表位对齐，保留原始缩进结构
- ✅ **超长行截断** — 超出 A4 宽度的行自动截断 + 红色 `…` 标记
- ✅ **固定 A4 比例** — 794×1123px (96 DPI)，每页尺寸统一
- ✅ **PDF 输出** — 每个源文件生成一份 PDF

## 快速开始 / Quick Start

### 安装依赖

```bash
npm install -g @resvg/resvg-js
pip install img2pdf
```

### 使用

1. 将源代码文件放在 `gen_code_pdfs.py` 同目录
2. 编辑 `FILES` 列表，填入文件名
3. 按需修改配置（`FONT_KEY`、`FONT_SIZE` 等）
4. 运行：

```bash
python gen_code_pdfs.py
```

5. 输出：
   - `filename.c.pdf` — 合并后的 PDF
   - `filename.c_images/` — 中间 SVG + PNG 文件

## 配置 / Configuration

在 `gen_code_pdfs.py` 顶部可调参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `FONT_KEY` | `cascadia` | 字体：`cascadia` / `firacode` / `jetbrains` / `consolas` / `courier` / `sourcecode` |
| `FONT_SIZE` | `14` | 基础字号 (px)，超宽代码自动缩小到 `MIN_FONT_SIZE` |
| `LINE_HEIGHT_RATIO` | `1.65` | 行高 = 字号 × 这个系数 |
| `TAB_WIDTH` | `4` | Tab 制表位宽度（空格数） |
| `MIN_FONT_SIZE` | `7` | 自动缩小时的最小字号 |
| `CO` | — | 语法着色颜色映射 |
| `KW` / `RG` | — | 关键字 / 寄存器名列表 |

## 自动适配逻辑 / Auto-fit Logic

1. **宽度适配**：扫描所有代码行，找到最长行（正确处理 Tab），计算令其刚好占满 A4 内容宽度的字号，上限为 `FONT_SIZE`，下限为 `MIN_FONT_SIZE`
2. **每页行数**：用 A4 可用高度 ÷ (`字号 × LINE_HEIGHT_RATIO`)，充分利用页面空间
3. **截断处理**：即使缩到最小字号仍超出时，在行末加红色 `…`，内容由 SVG clipPath 干净裁剪
4. **Tab 制表位**：Tab 推进到下一个 `TAB_WIDTH` 倍数列位置，而非固定宽度

## 输出结构 / Output Structure

```
filename.c/
├── code_page_1.svg
├── code_page_1.png
├── code_page_2.svg
├── code_page_2.png
└── ...
filename.c.pdf    ← merged PDF
```

## 效果预览 / Preview

```
┌─────────────────────────────────────────────┐
│ 📄 main.c                                   │
│ 第 1 页 · 共 32 页 · 1557 行 · Cascadia 14px│
├─────────────────────────────────────────────┤
│   1  #include "stc15.h"                    │
│   2  #include "stdio.h"                    │
│   3                                        │
│   4  #include "DS1302.h"                   │
│   5  #include "EEPROM.h"                   │
│  ...                                       │
└─────────────────────────────────────────────┘
```

---

## 📖 中文完整说明

### 这是什么？

`code-to-images` 是一个 Python 工具，能把你的源代码文件（`.c`、`.h`、`.py`、`.js` 等）变成带**行号**和**语法高亮**的 A4 比例图片，再自动合并成一个 PDF。打印代码、分享代码片段、做代码审查报告的绝佳工具。

### 核心理念

代码打印/分享最烦人的就是**格式乱掉**——缩进没了、行号不对、超出页面被截断、字号不合适。这个工具就是要解决这些问题：

1. **打开脚本** `gen_code_pdfs.py`
2. **在 `FILES` 列表里填上源文件名**
3. **运行 `python gen_code_pdfs.py`**
4. **拿到 PDF**

就是这么简单。

### 自动适配算法（详细版）

每处理一个源文件，脚本会做这几件事：

#### ① 计算最优字号

```
扫描所有代码行 → 找到最长的那一行（Tab 按 TAB_WIDTH 展开计算宽度）
→ 计算：理想字号 = A4内容宽度 ÷ (最长行字符数 × 0.60)
→ 取整并 clamp 到 [MIN_FONT_SIZE, FONT_SIZE] 区间
```

所以如果你的代码每行都很短（比如配置文件），它会用你设的 `FONT_SIZE=14`；如果代码很长（比如一行的寄存器配置有 200 个字符），它会自动缩小字号，保证能完整显示。

#### ② 计算每页行数

```
行高 = 字号 × LINE_HEIGHT_RATIO（默认 1.65）
每页行数 = A4内容高度 ÷ 行高
```

字号大了 → 每页行数减少 → 页面更多，但字更大更清晰
字号小了 → 每页行数增加 → 页面更少，一页塞更多代码

**全部自动计算，不需要手动调。**

#### ③ Tab 制表位处理

这是大多数代码截图工具的痛点。`code-to-images` 用真正的制表位算法：

```
遇到 Tab 字符 → 当前列位置向上取整到下一个 TAB_WIDTH（默认 4）的倍数
```

这和 VS Code、Source Insight 等编辑器的行为完全一致，缩进结构**原样保留**。

#### ④ 超长行截断

即使字号缩到 `MIN_FONT_SIZE`（默认 7px）还是放不下的超长行：
- 行末自动加红色 `…` 标记，告诉你这行没显示完
- SVG 用 `clipPath` 干净裁剪超出部分——不会出现文字溢出到页边距外面的情况
- 如果文件中存在任何超长行，页头会显示 `✂ 行过长已截断` 提示

### 6 种字体怎么选？

| 字体名 | `FONT_KEY` | 特点 |
|--------|-----------|------|
| **Cascadia Code** | `cascadia` | 微软出品，连字(ligatures)支持好，默认推荐 |
| **Fira Code** | `firacode` | 连字丰富，设计感强 |
| **JetBrains Mono** | `jetbrains` | JetBrains 专用字体，瘦高风格 |
| **Consolas** | `consolas` | Windows 老牌等宽字体，兼容性好 |
| **Courier New** | `courier` | 打字机风格，复古 |
| **Source Code Pro** | `sourcecode` | Adobe 出品，开源佳作 |

在每个页面的头部会显示当前使用的字体名和字号，一目了然。

### 输出文件说明

执行完后会生成：

```
filename.c_images/       ← 中间文件目录
├── code_page_1.svg      ← 第1页 SVG（可再次编辑）
├── code_page_1.png      ← 第1页 PNG（用于合成 PDF）
├── code_page_2.svg
├── code_page_2.png
└── ...
filename.c.pdf           ← 最终的 PDF，直接打印或分享
```

SVG 文件是矢量格式，可以用来：
- 在浏览器里放大缩小
- 用 Inkscape 等工具编辑颜色/字体
- 直接拖进 Word/PPT

### 常见用法

**批量打印多文件：**
```python
FILES = [
    'main.c', 'adc.c', 'dma.c', 'spi.c',
    'main.h', 'adc.h', 'dma.h', 'spi.h',
]
```

**提高打印质量（300 DPI）：**
```python
A4_W, A4_H = 2480, 3508  # A4 at 300 DPI
```

**默认字体换成 Fira Code：**
```python
FONT_KEY = 'firacode'
```

## 许可证 / License

MIT
