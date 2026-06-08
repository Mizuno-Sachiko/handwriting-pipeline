# -*- coding: utf-8 -*-
"""把多页图片合成单个 PDF（满足"扫描成一个 pdf"这类要求）。"""
from PIL import Image


def to_pdf(pages, path, dpi=300):
    Image.init()                       # 注册 JPEG 等编码器，PDF 保存要用
    imgs = [p.convert("RGB") for p in pages]
    imgs[0].save(path, save_all=True, append_images=imgs[1:], resolution=dpi)
    return path
