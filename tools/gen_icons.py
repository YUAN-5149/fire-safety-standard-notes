# -*- coding: utf-8 -*-
"""產生網站圖示（分頁 favicon、iOS 加到主畫面、Android/PWA）。

設計：磚紅底（#b03a2e，與全站 --accent 同色）＋ 白色「消」字圓角方塊，
與使用者其他學習站（橘底「裝」、藍底）的風格一致，16px 下靠顏色就能辨識。

用法：python tools/gen_icons.py
輸出：icons/ 底下所有尺寸 ＋ icons/favicon.ico
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT = os.path.join(REPO, 'icons')

BG = (176, 58, 46)          # #b03a2e 全站 --accent
FG = (255, 255, 255)
CHAR = '消'
FONT = r'C:\Windows\Fonts\msjhbd.ttc'   # 微軟正黑體 粗體

SS = 8   # 超取樣倍率，先畫大再縮，邊緣才乾淨


def tile(size, radius_ratio=0.22, char_ratio=0.74, pad_ratio=0.0):
    """畫一張 size×size 的圖示。pad_ratio>0 用於 maskable（留安全邊距）。"""
    S = size * SS
    img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    pad = int(S * pad_ratio)
    box = (pad, pad, S - pad - 1, S - pad - 1)
    inner = S - pad * 2
    r = int(inner * radius_ratio)
    d.rounded_rectangle(box, radius=r, fill=BG)

    # 以目標字高反推字級，再用實際 bbox 置中（CJK 字型的 ascent/descent 不可靠）
    target = inner * char_ratio
    fs = int(target)
    for _ in range(12):
        f = ImageFont.truetype(FONT, fs)
        bb = d.textbbox((0, 0), CHAR, font=f)
        h = bb[3] - bb[1]
        if h == 0:
            break
        adj = target / h
        if abs(adj - 1) < 0.01:
            break
        fs = max(1, int(fs * adj))
    f = ImageFont.truetype(FONT, fs)
    bb = d.textbbox((0, 0), CHAR, font=f)
    x = pad + (inner - (bb[2] - bb[0])) / 2 - bb[0]
    y = pad + (inner - (bb[3] - bb[1])) / 2 - bb[1]
    d.text((x, y), CHAR, font=f, fill=FG)

    return img.resize((size, size), Image.LANCZOS)


def flatten(img):
    """maskable 與 ico 需要不透明底。"""
    bg = Image.new('RGB', img.size, BG)
    bg.paste(img, mask=img.split()[3])
    return bg


os.makedirs(OUT, exist_ok=True)
made = []

# 小尺寸把字放大、圓角收斂，16px 才看得出是字而不是一團色塊
for size, rr, cr in [(16, 0.16, 0.86), (32, 0.18, 0.80), (48, 0.20, 0.78),
                     (64, 0.20, 0.76), (180, 0.22, 0.74),
                     (192, 0.22, 0.74), (512, 0.22, 0.74)]:
    p = os.path.join(OUT, 'icon-%d.png' % size)
    tile(size, rr, cr).save(p)
    made.append((os.path.basename(p), os.path.getsize(p)))

# iOS 主畫面：不吃透明與圓角，直接給滿版方形
flatten(tile(180, radius_ratio=0, char_ratio=0.70)).save(
    os.path.join(OUT, 'apple-touch-icon.png'))
made.append(('apple-touch-icon.png',
             os.path.getsize(os.path.join(OUT, 'apple-touch-icon.png'))))

# Android 自適應圖示：內容要縮在中央 80% 的安全區內
flatten(tile(512, radius_ratio=0, char_ratio=0.74, pad_ratio=0.14)).save(
    os.path.join(OUT, 'icon-512-maskable.png'))
made.append(('icon-512-maskable.png',
             os.path.getsize(os.path.join(OUT, 'icon-512-maskable.png'))))

# 舊版瀏覽器與 Windows 捷徑
ico = os.path.join(OUT, 'favicon.ico')
tile(64, 0.20, 0.76).save(ico, format='ICO',
                          sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64)])
made.append(('favicon.ico', os.path.getsize(ico)))

for n, s in made:
    print('%-26s %6.1f KB' % (n, s / 1024))
print('共 %d 個檔案 → %s' % (len(made), OUT))
