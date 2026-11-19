# -*- coding: utf-8 -*-
"""寫詳解用的參考資料：對每一題列出題目、官方答案，以及現行法規中最相關的條文（字元雙連詞 TF-IDF）。
用法：python exams/tools/explain_ctx.py <試卷 id> [每題候選條數] > 輸出.txt
    例：python exams/tools/explain_ctx.py 115050-0808 4
"""
import os, re, sys, json, math, collections

HERE = os.path.dirname(os.path.abspath(__file__))
EX = os.path.dirname(HERE); ROOT = os.path.dirname(EX)

docs = []   # (law_key, law_name, n, body)
for a in json.load(open(os.path.join(ROOT, 'tools', 'arts.json'), encoding='utf-8')):
    docs.append(('std', '各類場所消防安全設備設置標準', a['n'], a['body']))
for L in json.load(open(os.path.join(EX, 'meta', 'laws.json'), encoding='utf-8')):
    for a in L['arts']:
        docs.append((L['key'], L['name'], a['n'], a['body']))
kbp = os.path.join(EX, 'meta', 'kb.json')
if os.path.exists(kbp):     # 檢修基準：依段落切成約 500 字一塊
    CNN = '一二三四五六七八九十'
    for c in json.load(open(kbp, encoding='utf-8'))['chapters']:
        paras, buf = [], ''
        for line in c['text'].splitlines():
            if len(buf) > 450 and re.match(r'^\s*[（(]?[一二三四五六七八九十]+[、）)]', line):
                paras.append(buf); buf = ''
            buf += line.strip()
        if buf: paras.append(buf)
        for i, t in enumerate(paras):
            docs.append(('kb', '檢修基準', '第%d章%s-%d' % (c['no'], c['title'], i + 1), t))
docs = [d for d in docs if d[3].strip() not in ('（刪除）', '(刪除)')]


def grams(t):
    t = re.sub(r'[\s，。、；：（）「」\(\)\d０-９A-Za-z.,:;%％-]+', '|', t)
    c = collections.Counter()
    for seg in t.split('|'):
        for i in range(len(seg) - 1):
            c[seg[i:i + 2]] += 1
    return c


G = [grams(d[3]) for d in docs]
df = collections.Counter(g for d in G for g in d)
N = len(G)
idf = {g: math.log(N / (1 + c)) + 1 for g, c in df.items()}
V = []
for d in G:
    v = {g: (1 + math.log(c)) * idf[g] for g, c in d.items()}
    n = math.sqrt(sum(x * x for x in v.values())) or 1
    V.append({g: x / n for g, x in v.items()})


def scope(stem):
    s = stem
    if '公共危險物品' in s or '可燃性高壓氣體' in s: return {'haz', 'std'}
    if '檢修基準' in s: return {'kb'}
    if '設備人員法' in s: return {'staff', 'staff-r'}
    if '檢修及申報' in s: return {'inspect', 'fire', 'fire-r'}
    if '建築技術規則' in s: return {'bldg'}
    if '設置標準' in s: return {'std'}
    if '消防法' in s: return {'fire', 'fire-r'}
    return None


def top(text, keys, k):
    q = grams(text)
    v = {g: (1 + math.log(c)) * idf[g] for g, c in q.items() if g in idf}
    sc = []
    for i, d in enumerate(V):
        if keys and docs[i][0] not in keys: continue
        sc.append((sum(x * d.get(g, 0) for g, x in v.items()), i))
    sc.sort(reverse=True)
    return [i for s, i in sc[:k]]


def main():
    pid = sys.argv[1]; k = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    P = {p['id']: p for p in json.load(open(os.path.join(EX, 'data', 'papers.json'), encoding='utf-8'))}
    p = P[pid]
    print('#', p['year'], p['cat'], p['subject'], '備註：', p['key_note'] or '—')
    for e in p['essays']:
        print('\n[申論 %s] %s' % (e['no'], e['text']))
        for i in top(e['text'], scope(e['text']), k + 1):
            print('  ▸ %s §%s：%s' % (docs[i][1][:12], docs[i][2], docs[i][3][:420].replace('\n', ' ')))
    for q in p['mcq']:
        a = q.get('answer_corrected') or q['answer']
        print('\n[%d] %s' % (q['no'], q['stem']))
        for L in 'ABCD':
            print('  (%s) %s' % (L, q['options'].get(L, '')))
        print('  官方答案：%s%s' % (q['answer'], ('　更正：' + q['answer_corrected']) if q.get('answer_corrected') else ''))
        good = ' '.join(q['options'].get(L, '') for L in a if L in 'ABCD')
        for i in top(q['stem'] + ' ' + good + ' ' + good, scope(q['stem']), k):
            print('  ▸ %s §%s：%s' % (docs[i][1][:12], docs[i][2], docs[i][3][:420].replace('\n', ' ')))


if __name__ == '__main__':
    main()
