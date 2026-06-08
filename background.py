# -*- coding: utf-8 -*-
"""生成背景图。

没有现成答题纸/稿纸时，用这里生成一张空白或带横线的 A4，
直接当 render 的背景。尺寸按 300dpi 的 A4（2481x3508）。
"""
from PIL import Image, ImageDraw

A4 = (2481, 3508)
PAPER = (252, 251, 247)          # 微暖白纸


def blank_a4(size=A4, color=PAPER):
    """纯空白纸。"""
    return Image.new("RGB", size, color)


def ruled_a4(size=A4, color=PAPER, line_spacing=116, top=130, margin=110,
             line_color=(176, 190, 205)):
    """带横线的稿纸：从 top 开始每 line_spacing 一条横线。"""
    img = Image.new("RGB", size, color)
    d = ImageDraw.Draw(img)
    w, h = size
    y = top + line_spacing
    while y < h - top:
        d.line([(margin, y), (w - margin, y)], fill=line_color, width=1)
        y += line_spacing
    return img


if __name__ == "__main__":
    ruled_a4().save("examples/ruled_bg.png")
    blank_a4().save("examples/blank_bg.png")
    print("已生成示例背景到 examples/")
