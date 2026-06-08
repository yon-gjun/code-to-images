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

## 许可证 / License

MIT
