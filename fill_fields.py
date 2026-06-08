# -*- coding: utf-8 -*-
"""往表单空格里手写填字（可选）。

针对答题纸/表格那种"学号：____ 姓名：____"的横线空格，把字逐个写上去：
每字随机挑字体、微缩放、微旋转、基线浮动，整串自动缩放到下划线宽度内，
避免长内容撑出去怼到标签。坐标按你自己的背景实测填。
"""
import random
from PIL import Image, ImageFont, ImageDraw


def write_field(target, fonts, seg, baseline_y, text,
                ink=(18, 18, 18), max_size=60, rng=None):
    """在 target 图上、横线段 seg=(x0,x1) 上方、基线 baseline_y 处写 text。

    fonts 为字体文件路径列表，逐字随机挑选。
    """
    rng = rng or random.Random()
    loaded = [ImageFont.truetype(str(f), max_size) for f in fonts]
    segw = seg[1] - seg[0]
    margin = 20
    picks = [rng.choice(loaded) for _ in text]
    sizes = [max_size + rng.randint(-3, 4) for _ in text]
    gap = lambda sc: int(max_size * sc * 0.10)

    def total(sc):
        w = 0
        for f, s, c in zip(picks, sizes, text):
            bb = f.font_variant(size=max(int(s * sc), 8)).getbbox(c)
            w += (bb[2] - bb[0]) + gap(sc)
        return w - gap(sc)

    sc = 1.0
    while total(sc) > segw - margin and sc > 0.4:        # 整串缩放到下划线内
        sc -= 0.05

    x = (seg[0] + seg[1]) / 2 - total(sc) / 2
    for f, s, c in zip(picks, sizes, text):
        fs = max(int(s * sc), 8)
        f2 = f.font_variant(size=fs)
        bb = f2.getbbox(c)
        gw, gh = bb[2] - bb[0], bb[3] - bb[1]
        pad = 24
        tile = Image.new("RGBA", (gw + 2 * pad, gh + 2 * pad), (0, 0, 0, 0))
        ImageDraw.Draw(tile).text((pad - bb[0], pad - bb[1]), c, font=f2, fill=ink + (255,))
        tile = tile.rotate(rng.uniform(-4, 4), resample=Image.BICUBIC, expand=True)
        yj = rng.uniform(-3, 3)
        target.paste(tile, (int(x - pad), int(baseline_y - gh - pad - 12 + yj)), tile)
        x += gw + gap(sc)
