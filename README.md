# code-to-images

> 将源代码文件转换为带行号 + 语法高亮的 A4 图片，并合并为 PDF。
> Convert source code files into A4 images with line numbers, syntax highlighting, then merge to PDF.

---

## 功能 / Features

- ✅ **行号** — 从 1 开始连续编号
- ✅ **语法高亮** — 关键字、寄存器、宏、数字、注释分别着色
- ✅ **文件头** — 文件名、页码、总行数
- ✅ **亮色主题** — 白底灰线，适合打印
- ✅ **A4 比例** — 794×1286px，可直接打印
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
3. 运行：

```bash
python gen_code_pdfs.py
```

4. 输出：
   - `filename.c.pdf` — 合并后的 PDF
   - `filename.c_images/` — 中间 SVG + PNG 文件

## 配置 / Configuration

在 `gen_code_pdfs.py` 中可调参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `LINES_PER_PAGE` | 50 | 每页行数 |
| `font_size` | 14 | 字体大小 (px) |
| `line_height` | 24 | 行间距 (px) |
| `COLOR_*` | — | 语法着色颜色 |
| `REGS` | `P0..P7` | 高亮的寄存器名 |

## 效果预览 / Preview

生成的第一页效果：

```
┌────────────────────────────────────────┐
│ 📄 main.c                             │
│ 第 1 页 · 共 32 页 · 1557 行         │
├────────────────────────────────────────┤
│   1  #include "stc15.h"              │
│   2  #include "stdio.h"              │
│   3                                   │
│   4  #include "DS1302.h"             │
│   5  #include "EEPROM.h"             │
│  ...                                  │
└────────────────────────────────────────┘
```

## 许可证 / License

MIT
