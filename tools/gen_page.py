# -*- coding: utf-8 -*-
import os, re, json, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)          # 上一層即筆記根目錄
sp = HERE

d = json.load(open(os.path.join(sp, 'index_data.json'), encoding='utf-8'))
rows, FILES = d['rows'], d['files']

# 從題庫抽出章節名稱與各段落顯示名，避免兩邊漂移
qt = open(os.path.join(REPO, '05-互動題庫.html'), encoding='utf-8').read()
cats = dict(re.findall(r"\{k:'(\w)', n:'([^']+)'", qt))
docblk = qt[qt.find('const DOCS'):qt.find('const DGRULES')]
SECS = {}
for m in re.finditer(r"^\s*(\w): \{ file:'([^']+)',\s*\n\s*name:'([^']+)',\s*\n\s*secs:\{(.*?)\} \},?", docblk, re.S | re.M):
    ch, f, name, body = m.group(1), m.group(2), m.group(3), m.group(4)
    SECS[ch] = dict(re.findall(r"(\w+):'([^']+)'", body))

EDITIONS = ['第一編總則', '第二編消防設計', '第三編消防安全設計',
            '第四編公共危險物品等場所消防設計及消防安全設備', '第五編附則']

QUIZ = urllib.parse.quote('05-互動題庫.html')

def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

trs = []
for r in rows:
    n, ch, sec = r['n'], r['c'], r['s']
    f = FILES.get(ch, '')
    if f and sec and SECS.get(ch, {}).get(sec):
        href = urllib.parse.quote(f) + '?s=' + sec + '#' + sec
        link = '<a href="%s">%s</a>' % (href, esc(SECS[ch][sec]))
    else:
        link = '<span class="none">尚無圖解</span>'
    ed = r['g'].split('／')[0]
    rest = '／'.join(r['g'].split('／')[1:])
    law = 'https://law.moj.gov.tw/LawClass/LawSingle.aspx?pcode=D0120029&amp;flno=' + n
    if r['q']:
        qn = ('<a class="qlink" href="' + QUIZ + '?r=' + n + '"'
              ' title="只練 §' + n + ' 的 ' + str(r['q']) + ' 題">' + str(r['q']) + '</a>')
    else:
        qn = '<span class="none">0</span>'
    trs.append(
      '<tr data-ed="%s" data-k="%s" data-dg="%s">'
      '<td class="no"><a class="law" href="%s" target="_blank" rel="noopener">§%s</a></td>'
      '<td class="grp">%s</td><td>%s<span class="via">內文</span></td>'
      '<td class="dg">%s</td><td class="q">%s</td></tr>'
      % (esc(ed), esc(('§' + n + ' ' + r['g'] + ' ' + r['t'] + ' ' + cats.get(ch, '')).lower()),
         (ch + ':' + sec) if (f and sec) else '',
         law, n, esc(rest or '—'), esc(r['t']), link, qn))

TPL = open(os.path.join(sp, 'index_tpl.html'), encoding='utf-8').read()
chips = '\n    '.join(
    '<button class="chip" data-ed="%s">%s</button>' % (esc(e), esc(e.replace('第一編', '第一編 ').replace('第二編', '第二編 ').replace('第三編', '第三編 ').replace('第四編', '第四編 ').replace('第五編', '第五編 ')))
    for e in EDITIONS)
# 段落 id → 連結與標題（含潔淨區等沒有對應條文列的頁面）
secname = {}
for ch, d in SECS.items():
    fp = FILES.get(ch, '')
    if not fp: continue
    for sec, label in d.items():
        secname[ch + ':' + sec] = {'href': urllib.parse.quote(fp) + '?s=' + sec + '#' + sec,
                                   'name': label}
html = TPL.replace('<!--CHIPS-->', chips).replace('<!--ROWS-->', '\n'.join(trs))
html = html.replace('<!--TOTAL-->', str(len(rows)))
html = html.replace('<!--SECNAME-->', json.dumps(secname, ensure_ascii=False, separators=(',', ':')))
open(os.path.join(REPO, '23-條號索引.html'), 'w', encoding='utf-8').write(html)
print('rows', len(trs), 'chars', len(html))
print('無圖解條數', sum(1 for t in trs if '尚無圖解' in t))
