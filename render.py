# -*- coding: utf-8 -*-
"""文本转手写图片。

在 handright 的基础上加了两件事，让结果更接近真人手写：
  1. 多字体逐字随机混排——同一个字在全篇里换着不同字体写，重复字不再一模一样；
  2. 相关基线模型——相邻字几乎不差，但整行基线缓慢漂移、偶尔写斜一行，
     而不是每个字独立上下乱跳那种机器味。

handright 默认每画一个字都调 _get_font / _flow_layout，这里把这两个函数替换掉。
"""
import argparse
import math
import pathlib
import random

from PIL import Image, ImageFont
import handright._core as core
from handright._util import gauss
from handright import Template, handwrite


def patch_engine(fonts):
    """替换 handright 的取字体与逐字定位逻辑。fonts 是一组同尺寸 ImageFont。"""

    # 逐字随机挑一套字体，再叠原有的字号高斯微扰
    def _get_font_mixed(tpl, rand):
        base = rand.choice(fonts)
        size = max(round(gauss(rand, base.size, tpl.get_font_size_sigma())), 0)
        return base.font_variant(size=size) if size != base.size else base

    core._get_font = _get_font_mixed

    # 相关基线：进入新的一行时重设斜率/起伏参数，行内 y 随 x 平滑变化
    st = {"y": None}

    def _flow_layout(draw, x, y, char, tpl, rand):
        if y != st["y"]:
            st.update(
                y=y, x0=x,
                slope=rand.gauss(0, 0.009),      # 整行斜率：多数行平，偶尔明显斜一行
                base=rand.gauss(0, 1.2),         # 该行整体基线微偏
                amp=abs(rand.gauss(0, 1.1)),     # 行内缓慢起伏幅度
                freq=rand.uniform(0.002, 0.006),
                phase=rand.uniform(0, 2 * math.pi),
            )
        dx = x - st["x0"]
        yoff = (st["base"] + st["slope"] * dx
                + st["amp"] * math.sin(st["freq"] * dx + st["phase"])
                + rand.gauss(0, 0.6))            # 极小独立抖动，避免过于光滑
        font = core._get_font(tpl, rand)
        offset = core._draw_char(draw, char, (round(x), round(y + yoff)), font)
        x += gauss(rand, tpl.get_word_spacing() + offset, tpl.get_word_spacing_sigma())
        return x

    core._flow_layout = _flow_layout


def render(text, fonts, background, *, ink=(18, 18, 18), font_size=70,
           line_spacing=116, word_spacing=8, margin=175, top_margin=None,
           seed=11):
    """把 text 渲染成若干页图片（自动分页）。fonts 为字体文件路径列表。"""
    loaded = [ImageFont.truetype(str(p), font_size) for p in fonts]
    patch_engine(loaded)
    template = Template(
        background=background,
        font=loaded[0],                          # 仅用于尺寸校验，实际取字走 patch
        line_spacing=line_spacing,
        fill=ink,
        left_margin=margin, right_margin=margin,
        top_margin=margin if top_margin is None else top_margin,
        bottom_margin=margin,
        word_spacing=word_spacing,
        line_spacing_sigma=0.5,                  # 竖向交给相关基线模型，这里基本关掉
        font_size_sigma=font_size / 50,
        word_spacing_sigma=font_size / 22,
        perturb_x_sigma=font_size / 36,
        perturb_y_sigma=font_size / 70,
        perturb_theta_sigma=0.04,
    )
    return list(handwrite(text, template, seed=seed))


def _indent(text):
    """首行缩进两格，符合中文行文习惯。"""
    lines = [l.rstrip() for l in text.splitlines() if l.strip()]
    return "\n".join("　　" + l for l in lines)


def main():
    ap = argparse.ArgumentParser(description="文本转手写图片")
    ap.add_argument("--text", default="examples/sample.txt", help="输入文本文件")
    ap.add_argument("--fonts", nargs="+", required=True, help="一个或多个手写字体文件（自备）")
    ap.add_argument("--background", help="背景图片；不给则生成空白 A4")
    ap.add_argument("--out", default="out", help="输出目录")
    ap.add_argument("--ink", default="18,18,18", help="墨色 R,G,B")
    ap.add_argument("--size", type=int, default=70, help="字号")
    ap.add_argument("--line-spacing", type=int, default=116, help="行距")
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--no-indent", action="store_true", help="不做首行缩进")
    ap.add_argument("--scan", action="store_true", help="叠加扫描质感")
    ap.add_argument("--pdf", help="把所有页合成到这个 PDF")
    args = ap.parse_args()

    from background import blank_a4
    text = pathlib.Path(args.text).read_text(encoding="utf-8")
    if not args.no_indent:
        text = _indent(text)
    bg = Image.open(args.background).convert("RGB") if args.background else blank_a4()
    ink = tuple(int(v) for v in args.ink.split(","))

    pages = render(text, args.fonts, bg, ink=ink, font_size=args.size,
                   line_spacing=args.line_spacing, seed=args.seed)

    if args.scan:
        from scan import scan
        pages = [scan(p, seed=args.seed + i) for i, p in enumerate(pages)]

    outdir = pathlib.Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    for i, im in enumerate(pages, 1):
        im.save(outdir / f"page{i}.png")

    if args.pdf:
        from to_pdf import to_pdf
        to_pdf(pages, args.pdf)
    print(f"完成：{len(pages)} 页 -> {outdir}")


if __name__ == "__main__":
    main()
