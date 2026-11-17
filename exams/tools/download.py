# -*- coding: utf-8 -*-
"""下載 catalog.json 中指定類科的試題(Q)/答案(S)/更正答案(M) PDF。
用法：python exams/tools/download.py exams/raw 消防設備師 消防設備士"""
import json, os, sys, re, time
import moex

HERE = os.path.dirname(os.path.abspath(__file__))
cat = json.load(open(os.path.join(HERE, '..', 'meta', 'catalog.json'), encoding='utf-8'))
out_dir = sys.argv[1]
keys = sys.argv[2:]
os.makedirs(out_dir, exist_ok=True)

manifest = []
for code, ex in sorted(cat.items()):
    for row in ex['rows']:
        if not any(k in row['cat'] for k in keys):
            continue
        for t, href in row['files'].items():
            fn = '%s_c%s_s%s_%s.pdf' % (code, row['c'], row['s'], t)
            p = os.path.join(out_dir, fn)
            ok = os.path.exists(p) and os.path.getsize(p) > 1000
            if not ok:
                try:
                    b = moex.get(moex.BASE + href)
                except Exception as e:
                    print('ERR', fn, e); continue
                if not b.startswith(b'%PDF'):
                    print('NOT PDF', fn, b[:60]); continue
                open(p, 'wb').write(b)
            manifest.append({'code': code, 'year': int(code[:3]), 'cat': row['cat'],
                             'subject': row['subject'], 'c': row['c'], 's': row['s'],
                             'type': t, 'file': fn,
                             'url': moex.BASE + href})
            print(fn, os.path.getsize(p))
json.dump(manifest, open(os.path.join(out_dir, 'manifest.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('共', len(manifest), '檔')
