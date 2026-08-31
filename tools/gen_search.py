# -*- coding: utf-8 -*-
"""把每一份圖解頁依 <h2 id> 切段，抽出純文字，產生 search-index.json。
   鍵為「章節代碼:段落id」，與題庫 DOCS 的 dg 標記一致，條號索引可直接對照。"""
import os, re, json, html, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)          # 上一層即筆記根目錄

qt = open(os.path.join(REPO, '05-互動題庫.html'), encoding='utf-8').read()

# 從題庫 DOCS 取得 章節代碼 → 檔名 / 段落標題
docblk = qt[qt.find('const DOCS'):qt.find('const DGRULES')]
DOCS = {}
for m in re.finditer(r"^\s*(\w): \{ file:'([^']+)',\s*\n\s*name:'([^']+)',\s*\n\s*secs:\{(.*?)\} \},?",
                     docblk, re.S | re.M):
    ch, f, name, body = m.groups()
    DOCS[ch] = {'file': urllib.parse.unquote(f), 'name': name,
                'secs': dict(re.findall(r"(\w+):'([^']+)'", body))}

def plain(x):
    x = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', x, flags=re.S | re.I)
    x = re.sub(r'<!--.*?-->', ' ', x, flags=re.S)
    x = re.sub(r'<[^>]+>', ' ', x)
    x = html.unescape(x)
    x = re.sub(r'[\s\u3000]+', ' ', x)
    return x.strip()

out, stats = {}, []
for ch, d in sorted(DOCS.items()):
    p = os.path.join(REPO, d['file'])
    if not os.path.exists(p):
        print('MISSING', d['file']); continue
    t = open(p, encoding='utf-8').read()
    marks = [(m.group(1), m.start()) for m in re.finditer(r'<h2 id="([\w-]+)"', t)]
    end = t.find('<footer')
    if end < 0: end = len(t)
    n = 0
    for i, (sec, pos) in enumerate(marks):
        stop = marks[i + 1][1] if i + 1 < len(marks) else end
        txt = plain(t[pos:stop])
        if sec in d['secs'] or True:
            out['%s:%s' % (ch, sec)] = txt
            n += 1
    stats.append('%s %-40s %2d 段 %6d 字' % (ch, d['file'][:40], n,
                 sum(len(out[k]) for k in out if k.startswith(ch + ':'))))

dst = os.path.join(REPO, 'search-index.json')
json.dump(out, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('\n'.join(stats))
print('段落數 %d，總字數 %d，檔案 %.0f KB'
      % (len(out), sum(len(v) for v in out.values()), os.path.getsize(dst) / 1024))
