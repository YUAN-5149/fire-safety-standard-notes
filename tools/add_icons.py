# -*- coding: utf-8 -*-
"""把 favicon / PWA 宣告掛進所有頁面的 <head>（可重複執行，不會重複插入）。

用法：python tools/add_icons.py
"""
import os, glob, re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
MARK = '<!-- icons -->'

BLOCK = '''<!-- icons -->
<link rel="icon" href="icons/favicon.ico" sizes="32x32">
<link rel="icon" href="icons/icon-192.png" type="image/png" sizes="192x192">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<link rel="manifest" href="site.webmanifest">
<meta name="theme-color" content="#b03a2e">'''

VIEWPORT = re.compile(r'(<meta name="viewport"[^>]*>)')

added, skipped, failed = [], [], []
for f in sorted(glob.glob(os.path.join(REPO, '*.html'))):
    name = os.path.basename(f)
    t = open(f, encoding='utf-8').read()
    if MARK in t:
        skipped.append(name)
        continue
    if not VIEWPORT.search(t):
        failed.append(name)
        continue
    t = VIEWPORT.sub(lambda m: m.group(1) + '\n' + BLOCK, t, count=1)
    open(f, 'w', encoding='utf-8').write(t)
    added.append(name)

print('已加入 %d 個：' % len(added))
for n in added:
    print('   ', n)
if skipped:
    print('已有宣告、略過 %d 個' % len(skipped))
if failed:
    print('⚠ 找不到 viewport、未處理：', failed)
