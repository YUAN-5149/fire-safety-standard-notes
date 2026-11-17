# -*- coding: utf-8 -*-
"""逐場次抓結果表，只留「消防」相關類科，輸出 catalog.json。"""
import json, re, html, os, sys
import moex

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'meta')
codes = json.load(open(os.path.join(OUT, 'exam_codes.json'), encoding='utf-8'))

LINK = re.compile(r'<a[^>]*href="(wHandExamQandA_File\.ashx\?[^"]+)"[^>]*>(.*?)</a>', re.S)


def parse(t):
    rows, cat = [], None
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', t, re.S):
        links = [(html.unescape(h), re.sub(r'<[^>]+>', '', x).strip()) for h, x in LINK.findall(tr)]
        text = re.sub(r'<[^>]+>', ' ', LINK.sub(' ', tr))
        text = re.sub(r'\s+', ' ', html.unescape(text)).strip()
        if not links:
            if '_' in text and len(text) < 80:
                cat = text
            continue
        files = {}
        for h, label in links:
            q = dict(x.split('=', 1) for x in h.split('?', 1)[1].split('&'))
            files.setdefault(q['t'], h)
            c, s = q.get('c'), q.get('s')
        rows.append({'cat': cat, 'subject': text.replace('試題', '').replace('更正答案', '')
                     .replace('答案', '').strip(), 'c': c, 's': s, 'files': files})
    return rows


cat_all = {}
for y in sorted({k[:3] for k in codes}):
    yr = int(y) + 1911
    t0, _ = moex.exams_for_years(yr, yr)
    for code in sorted(k for k in codes if k[:3] == y):
        try:
            r = moex.search(t0, code, yr, yr)
        except Exception as e:
            print(code, 'ERR', e); continue
        rows = [x for x in parse(r) if x['cat'] and '消防' in x['cat']]
        cat_all[code] = {'name': codes[code], 'rows': rows}
        print(code, len(rows), sorted({x['cat'] for x in rows})[:4])
json.dump(cat_all, open(os.path.join(OUT, 'catalog.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
