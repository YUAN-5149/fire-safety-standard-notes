# -*- coding: utf-8 -*-
"""列出各年度考試場次，留下名稱含「消防」或「警察人員」者 → exams/meta/exam_codes.json。
用法：python exams/tools/list_exams.py [起始民國年] [結束民國年]"""
import json, os, sys
import moex

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'meta', 'exam_codes.json')
y1 = int(sys.argv[1]) if len(sys.argv) > 1 else 82
y2 = int(sys.argv[2]) if len(sys.argv) > 2 else 115
codes = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {}
for y in range(y1, y2 + 1):
    _, opts = moex.exams_for_years(y + 1911, y + 1911)
    for v, name in opts:
        if v and ('消防' in name or '警察人員' in name):
            codes[v] = name
    print(y, len(codes))
json.dump(dict(sorted(codes.items())), open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
