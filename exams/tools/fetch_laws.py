# -*- coding: utf-8 -*-
"""從全國法規資料庫抓詳解要引用的現行法規全文 → exams/meta/laws.json
（設置標準本身已在 tools/arts.json，這裡抓其他常考法規）

用法：python exams/tools/fetch_laws.py   （需可連網、需有 curl；法規資料庫的憑證 Python urllib 不接受，所以用 curl）
法規修正後重跑一次，再重寫受影響題目的詳解。
"""
import os, re, json, html as H, subprocess, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), 'meta', 'laws.json')

LAWS = [
    ('fire', '消防法', 'D0120001'),
    ('fire-r', '消防法施行細則', 'D0120002'),
    ('staff', '消防設備人員法', 'D0120068'),
    ('staff-r', '消防設備人員法施行細則', 'D0120070'),
    ('haz', '公共危險物品及可燃性高壓氣體製造儲存處理場所設置標準暨安全管理辦法', 'D0120025'),
    ('inspect', '消防安全設備檢修及申報辦法', 'D0120054'),
    ('bldg', '建築技術規則建築設計施工編', 'D0070115'),
    ('fpm-train', '防火管理人訓練與專業機構登錄及管理辦法', 'D0120079'),
    ('haz-train', '保安監督人與保安檢查員訓練專業機構登錄及管理辦法', 'D0120093'),
    ('duty-train', '服勤人員訓練與專業機構登錄及管理辦法', 'D0120089'),
    ('work', '消防安全設備設計監造測試及檢修作業辦法', 'D0120075'),
    ('bldg-fix', '原有合法建築物公共安全改善辦法', 'D0070150'),
    ('bldg-act', '建築法', 'D0070109'),
]


def parse(h):
    date = re.search(r'(?:修正|公發布)日期：</th>\s*<td>(.*?)</td>', h, re.S)
    body = h[h.find('law-reg-content'):]
    arts, ch = [], ''
    for m in re.finditer(r'<div class="h3 char-(\d)">(.*?)</div>|<div class="row"><div class="col-no">.*?name="([^"]+)">(第 [^<]+ 條)</a></div>'
                         r'<div class="col-data"><div class="law-article">(.*?)</div>\s*</div></div>', body, re.S):
        if m.group(1):
            if int(m.group(1)) <= 2:
                ch = re.sub(r'\s+', ' ', H.unescape(m.group(2))).strip()
            continue
        no = m.group(4).replace('第 ', '').replace(' 條', '').strip()
        txt = H.unescape(re.sub(r'<[^>]+>', '\n', m.group(5)))
        txt = '\n'.join(l.strip() for l in txt.split('\n') if l.strip())
        arts.append({'n': no, 'ch': ch, 'body': txt})
    d = re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', '', date.group(1)))).strip() if date else ''
    return d, arts


def main():
    out = []
    tmp = tempfile.mkdtemp()
    for key, name, pcode in LAWS:
        p = os.path.join(tmp, key + '.html')
        subprocess.run(['curl', '-s', 'https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=' + pcode, '-o', p], check=True)
        d, arts = parse(open(p, encoding='utf-8').read())
        print(name, d, len(arts), '條')
        out.append({'key': key, 'name': name, 'pcode': pcode, 'date': d, 'arts': arts})
        time.sleep(1)
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
