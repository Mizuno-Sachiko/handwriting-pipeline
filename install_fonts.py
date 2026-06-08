# -*- coding: utf-8 -*-
"""用户级安装字体（Windows，无需管理员）。

把指定目录下的 .ttf 复制到本地字体目录并注册到 HKCU，
新开的程序里即可选用。卸载就删掉那些文件、再删对应 HKCU 注册项。

用法：python install_fonts.py <字体目录> [--name 关键词]
  --name 只装文件名包含该关键词的字体（默认全装）
"""
import argparse
import ctypes
import os
import pathlib
import shutil
import winreg

from PIL import ImageFont


def install(font_dir, name_filter=None):
    font_dir = pathlib.Path(font_dir)
    files = [p for p in sorted(font_dir.glob("*.ttf"))
             if not name_filter or name_filter in p.stem]
    dest_dir = pathlib.Path(os.environ["LOCALAPPDATA"]) / "Microsoft" / "Windows" / "Fonts"
    dest_dir.mkdir(parents=True, exist_ok=True)
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts",
        0, winreg.KEY_SET_VALUE,
    )
    done = []
    for p in files:
        fam, style = ImageFont.truetype(str(p)).getname()
        dest = dest_dir / p.name
        if not dest.exists():
            shutil.copy2(p, dest)
        reg = f"{fam} (TrueType)" if style.lower() in ("regular", "") else f"{fam} {style} (TrueType)"
        winreg.SetValueEx(key, reg, 0, winreg.REG_SZ, str(dest))
        done.append((reg, p.name))
    winreg.CloseKey(key)
    ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001D, 0, 0, 0, 1000)  # 通知字体变更
    return done


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="用户级安装字体")
    ap.add_argument("font_dir", help="存放 .ttf 的目录")
    ap.add_argument("--name", help="只装文件名含此关键词的")
    args = ap.parse_args()
    done = install(args.font_dir, args.name)
    print(f"已安装 {len(done)} 个：")
    for reg, fn in done:
        print(" -", reg, "<=", fn)
