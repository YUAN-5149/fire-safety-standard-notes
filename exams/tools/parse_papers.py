# -*- coding: utf-8 -*-
"""把考選部歷屆試題 PDF（exams/raw）解析成結構化 JSON（exams/data/papers.json）。

試題 PDF 的特殊字元（私用區，經逐年核對 100～115 年一致）：
  E18C–E18F → (A)(B)(C)(D)  選擇題選項
  E129–E132 → ㈠～㈩          注意事項與申論小題
  E0C6–E0CA → ⑴～⑸          申論細項
  ED2C      → 論              早年「申論題」缺字
答案 PDF 是表格，題號與答案要靠座標配對，不能靠文字順序。

用法：python exams/tools/parse_papers.py
"""
import os, re, json, sys
import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
EX = os.path.dirname(HERE)
RAW = os.path.join(EX, 'raw')
OUT = os.path.join(EX, 'data')

PUA = {}
for i, ch in enumerate('ABCD'):
    PUA[0xE18C + i] = '\x00%s\x00' % ch          # 選項標記，之後再轉成結構
for i, ch in enumerate('㈠㈡㈢㈣㈤㈥㈦㈧㈨㈩'):
    PUA[0xE129 + i] = ch
for i, ch in enumerate('⑴⑵⑶⑷⑸'):
    PUA[0xE0C6 + i] = ch
PUA[0xED2C] = '論'
PUA[0xF03D] = ''

CN_NUM = '一二三四五六七八九十'
NOISE = ('不必抄題', '請以黑色', '請以藍', '本科目除專門名詞', '本試題為單一選擇題', '本測驗試題為單一選擇題',
         '須用2B鉛筆', '須用 2B', '於本試題或申論試卷上作答者')


def lines_of(doc):
    """依閱讀順序輸出 (page, y, x, text)；同一行的 span 依 x 串接。"""
    out = []
    for pno, pg in enumerate(doc):
        rows = []
        for b in pg.get_text('rawdict')['blocks']:
            for l in b.get('lines', []):
                t = ''
                for s in l['spans']:
                    for c in s['chars']:
                        o = ord(c['c'])
                        t += PUA.get(o, c['c']) if (0xE000 <= o <= 0xF8FF) else c['c']
                if t.strip():
                    rows.append((round(l['bbox'][1]), l['bbox'][0], t))
        rows.sort(key=lambda r: (r[0], r[1]))
        # 合併 y 幾乎相同的片段
        merged = []
        for y, x, t in rows:
            if merged and abs(merged[-1][0] - y) <= 3:
                py, px, pt = merged[-1]
                merged[-1] = (py, px, pt + t) if x > px else (py, x, t + pt)
            else:
                merged.append((y, x, t))
        for y, x, t in merged:
            out.append((pno, y, x, t.rstrip()))
    return out


def header(lines):
    h = {}
    head = ''.join(t for _, _, _, t in lines[:25]).replace(' ', '').replace('　', '')
    for key, pat in [('level', r'等別：(.+?)類'), ('cat', r'類科：(.+?)科目'),
                     ('subject', r'科目：(.+?)考試時間'), ('time', r'考試時間：(.+?)(?:座號|※)')]:
        m = re.search(pat, head)
        if m:
            h[key] = m.group(1).strip()
    m = re.search(r'代號：\s*(\d+)', head)
    if m:
        h['code'] = m.group(1)
    h['calculator'] = '可以使用電子計算器' in head
    return h


def strip_page_furniture(lines):
    keep = []
    for p, y, x, t in lines:
        s = t.replace(' ', '')
        if re.fullmatch(r'代號：\d+', s) or re.fullmatch(r'頁次：\d+－\d+', s) or s in ('全一頁', '座號：'):
            continue
        if re.fullmatch(r'代號：\d+頁次：\d+－\d+', s):
            continue
        keep.append((p, y, x, t))
    return keep


FURN = re.compile(r'\s*(?:頁次：\s*\d+\s*[-－]\s*\d+|代號：\s*\d+)\s*')


def clean(t):
    """移除跨頁時黏進題目文字的頁首頁尾（代號、頁次）。"""
    return FURN.sub('', t).strip()


def parse_q(path):
    doc = fitz.open(path)
    L = lines_of(doc)
    h = header(L)
    L = strip_page_furniture(L)
    # 跳過表頭：找到第一個「甲、」或第一題「一、」
    start = 0
    for i, (_, _, _, t) in enumerate(L):
        s = t.strip()
        if s.startswith('甲、') or re.match(r'^一、', s):
            start = i
            break
    body = L[start:]

    essays, mcq, mode = [], [], 'essay'
    cur, curq = None, None
    figures = sum(len(pg.get_images()) for pg in doc)

    def flush_q():
        nonlocal curq
        if curq:
            mcq.append(curq)
        curq = None

    for p, y, x, t in body:
        s = t.strip()
        if s.startswith('甲、'):
            continue
        if s.startswith('乙、') or '測驗題部分' in s:
            mode = 'mcq'
            if cur:
                essays.append(cur); cur = None
            continue
        if any(n in s for n in NOISE) or re.match(r'^共\s*\d+\s*題', s) or re.match(r'^代號：\s*\d+$', s):
            continue
        if re.match(r'^[㈠㈡㈢]', s) and any(n in s for n in ('抄題', '鋼筆', '專門名詞')):
            continue
        if mode == 'essay':
            m = re.match(r'^([一二三四五六七八九十]+)、(.*)$', s)
            if m:
                if cur:
                    essays.append(cur)
                cur = {'no': m.group(1), 'text': m.group(2)}
            elif cur:
                cur['text'] += ('\n' if re.match(r'^[㈠㈡㈢㈣㈤㈥㈦㈧㈨㈩⑴⑵⑶⑷⑸]', s) else '') + s
        else:
            # 題號貼在題幹前面（同一列），題幹本身可能以數字開頭（例：「9」＋「119 火災…」），
            # 所以用「預期的下一個題號」比對，而不是抓行首所有數字
            expect = 1 if curq is None else curq['no'] + 1
            if x < 64 and s.startswith(str(expect)) and \
                    not (len(s) > len(str(expect)) and s[len(str(expect))] in '.．'):
                flush_q()
                curq = {'no': expect, 'stem': '', 'options': {}, '_last': 'stem'}
                t = s[len(str(expect)):]
                if not t.strip():
                    continue
            if curq is None:
                continue
            parts = re.split(r'\x00([ABCD])\x00', t)
            head_txt = parts[0].strip()
            if head_txt:
                if curq['_last'] == 'stem':
                    curq['stem'] += head_txt
                else:
                    curq['options'][curq['_last']] += head_txt
            for k in range(1, len(parts), 2):
                letter, txt = parts[k], parts[k + 1].strip()
                curq['options'][letter] = txt
                curq['_last'] = letter
    if cur:
        essays.append(cur)
    flush_q()
    for q in mcq:
        q.pop('_last', None)
        q['stem'] = clean(q['stem'])
        for k in q['options']:
            q['options'][k] = clean(q['options'][k])
    for e in essays:
        e['text'] = clean(e['text'])
        m = re.findall(r'[（(]\s*(\d+)\s*分\s*[）)]', e['text'])
        e['points'] = sum(int(v) for v in m) if m else None
    return h, essays, mcq, figures


def parse_key(path):
    """題號與答案用座標配對：答案在題號正下方（同一欄）。"""
    doc = fitz.open(path)
    ans, note = {}, ''
    for pg in doc:
        words = pg.get_text('words')
        labels = [(w[0], w[1], w[2], w[3], int(re.match(r'第(\d+)題', w[4]).group(1)))
                  for w in words if re.fullmatch(r'第\d+題', w[4])]
        if not labels:
            # 100～102 年格式：「題號」列放 01、02…，下一列「答案」
            rows = [w[1] for w in words if w[4] == '題號']
            labels = [(w[0], w[1], w[2], w[3], int(w[4])) for w in words
                      if re.fullmatch(r'\d{1,3}', w[4]) and w[0] > 70
                      and any(abs(w[1] - ry) < 4 for ry in rows)]
        vals = [w for w in words if re.fullmatch(r'[A-D#]{1,4}|[ＡＢＣＤ]', w[4])]
        for (x0, y0, x1, y1, n) in labels:
            cx = (x0 + x1) / 2
            best = None
            for w in vals:
                wx = (w[0] + w[2]) / 2
                if w[1] > y1 - 1 and abs(wx - cx) < max(14, (x1 - x0) / 2 + 4) and w[1] - y1 < 40:
                    if best is None or w[1] < best[1]:
                        best = w
            if best:
                ans[n] = best[4]
        txt = pg.get_text()
        m = re.search(r'備\s*註：(.*?)(?:標準答案：|$)', txt, re.S)
        if m and '給分' in m.group(1):
            note += m.group(1).strip()
    return ans, re.sub(r'\s+', ' ', note).strip()


def main():
    manifest = json.load(open(os.path.join(RAW, 'manifest.json'), encoding='utf-8'))
    groups = {}
    for m in manifest:
        k = (m['code'], m['c'], m['s'])
        groups.setdefault(k, {'meta': m, 'files': {}})['files'][m['type']] = m
    papers, warn = [], []
    for (code, c, s), g in sorted(groups.items()):
        meta = g['meta']
        if 'Q' not in g['files']:
            continue
        h, essays, mcq, figs = parse_q(os.path.join(RAW, g['files']['Q']['file']))
        key, key2, note = {}, {}, ''
        if 'S' in g['files']:
            key, note = parse_key(os.path.join(RAW, g['files']['S']['file']))
        if 'M' in g['files']:
            key2, note2 = parse_key(os.path.join(RAW, g['files']['M']['file']))
            note = note2 or note
        for q in mcq:
            q['answer'] = key.get(q['no'])
            if key2.get(q['no']) and key2[q['no']] != key.get(q['no']):
                q['answer_corrected'] = key2[q['no']]
            if len(q['options']) != 4:
                warn.append('%s %s 第%d題 選項數=%d' % (code, meta['subject'], q['no'], len(q['options'])))
            if mcq and key and q['answer'] is None:
                warn.append('%s %s 第%d題 缺答案' % (code, meta['subject'], q['no']))
        nos = [q['no'] for q in mcq]
        if mcq and nos != list(range(1, len(nos) + 1)):
            warn.append('%s %s 題號不連續 %s' % (code, meta['subject'], nos[:5]))
        cat = '消防設備師' if '設備師' in meta['cat'] else '消防設備士'
        papers.append({
            'id': '%s-%s' % (code, s), 'code': code, 'year': meta['year'],
            'cat': cat, 'subject': meta['subject'], 'c': c, 's': s,
            'header': h, 'figures': figs,
            'essays': essays, 'mcq': mcq, 'key_note': note,
            'sources': {t: g['files'][t]['url'] for t in g['files']},
        })
    os.makedirs(OUT, exist_ok=True)
    json.dump(papers, open(os.path.join(OUT, 'papers.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    ne = sum(len(p['essays']) for p in papers)
    nm = sum(len(p['mcq']) for p in papers)
    na = sum(1 for p in papers for q in p['mcq'] if q.get('answer'))
    print('試卷 %d 份｜申論 %d 題｜選擇 %d 題（有答案 %d）' % (len(papers), ne, nm, na))
    print('警告 %d 則' % len(warn))
    open(os.path.join(OUT, 'parse_warnings.txt'), 'w', encoding='utf-8').write('\n'.join(warn))


if __name__ == '__main__':
    main()
