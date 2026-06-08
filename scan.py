# -*- coding: utf-8 -*-
"""扫描质感。

把干净的渲染页处理成"手机扫描/拍照"的样子：转灰度、纸张轻微歪斜、
打光不匀、纸面噪点、轻微发虚，最后压一道 JPEG 感的对比度。
每页传不同 seed，倾斜、打光中心和强度、纸白、噪点都会各页不同，
模拟一页页分别扫的细微差异。
"""
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance


def scan(im, seed):
    rng = np.random.default_rng(seed)
    g = im.convert("L")
    ang = rng.uniform(-0.9, 0.9)                              # 每页纸张角度不同
    g = g.rotate(ang, resample=Image.BICUBIC, expand=False, fillcolor=245)
    arr = np.asarray(g).astype(np.float32)
    h, w = arr.shape
    arr = arr * rng.uniform(0.94, 0.965) + rng.uniform(5, 9)  # 纸白逐页微浮动
    # 打光梯度：中心和强度逐页轻微随机，幅度不大
    cx = w * (0.5 + rng.uniform(-0.08, 0.08))
    cy = h * (0.5 + rng.uniform(-0.08, 0.08))
    sx = rng.uniform(0.07, 0.12)
    sy = rng.uniform(0.06, 0.10)
    yy, xx = np.mgrid[0:h, 0:w]
    grad = 1 - sx * (((xx - cx) / (w / 2)) ** 2) - sy * (((yy - cy) / (h / 2)) ** 2)
    arr *= grad
    arr += rng.normal(0, rng.uniform(3.0, 3.8), arr.shape)   # 噪点逐页不同
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    out = Image.fromarray(arr, "L").filter(ImageFilter.GaussianBlur(0.5))
    return ImageEnhance.Contrast(out).enhance(rng.uniform(1.05, 1.10))
