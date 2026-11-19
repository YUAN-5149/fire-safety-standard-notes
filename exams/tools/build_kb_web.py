# -*- coding: utf-8 -*-
"""把 exams/meta/kb.json（檢修基準全文）整理成網頁用 exams/data/kb-web.json：
  - PDF 斷行接回段落，依「一、（一）１、（１）A.(A)a.」標出層級
  - 找出歷屆試題中考檢修基準的題目，依設備名稱對應到各章
用法：python exams/tools/build_kb_web.py   （先跑 fetch_kb.py）
"""
import os, re, json

HERE = os.path.dirname(os.path.abspath(__file__))
EX = os.path.dirname(HERE)

MARK = [
    (1, re.compile(r'^[一二三四五六七八九十]+、')),
    (2, re.compile(r'^[（(][一二三四五六七八九十]+[）)]')),
    (3, re.compile(r'^[１２３４５６７８９０]+、|^\d+、')),
    (4, re.compile(r'^[（(][１２３４５６７８９０\d]+[）)]')),
    (5, re.compile(r'^[A-Z][.．]')),
    (6, re.compile(r'^\([A-Z]\)')),
    (7, re.compile(r'^[a-z][.．]')),
]
NOISE = re.compile(r'^(行政院公報|第\s*卷|內政篇)|^\s*$')


def blocks(text):
    out = []
    for raw in text.split('\n'):
        line = raw.strip()
        if NOISE.search(line):
            continue
        lvl = next((l for l, rx in MARK if rx.match(line)), 0)
        # 「檢查表」整頁表格：之後多半是表格碎片，標成表格開頭
        if re.search(r'檢\s*查\s*表\s*$', line) and len(line) < 40:
            out.append({'l': 9, 't': re.sub(r'\s+', '', line)})
            continue
        if lvl or not out or out[-1]['l'] == 9 and len(out[-1]['t']) > 300:
            out.append({'l': lvl, 't': line})
        else:
            prev = out[-1]['t']
            sep = '' if re.search(r'[一-鿿（）、，。；：]$', prev) and re.match(r'[一-鿿（）]', line) else ' '
            out[-1]['t'] = prev + sep + line
    # 太長的表格碎片切短，避免一大坨
    for b in out:
        if b['l'] == 0 and len(b['t']) > 1500:
            b['t'] = b['t'][:1500] + '…（表格內容請看原文 PDF）'
    return out


def main():
    kb = json.load(open(os.path.join(EX, 'meta', 'kb.json'), encoding='utf-8'))
    papers = json.load(open(os.path.join(EX, 'data', 'papers.json'), encoding='utf-8'))
    chs = []
    for c in kb['chapters']:
        chs.append({'no': c['no'], 'title': c['title'], 'b': blocks(c['text']), 'q': []})
    # 章名關鍵字（去掉「設備」等泛稱，加幾個常見別名）
    alias = {1: ['滅火器'], 2: ['室內消防栓'], 3: ['室外消防栓'], 4: ['自動撒水'], 5: ['水道連結'], 6: ['水霧'], 7: ['泡沫'],
             8: ['乾粉'], 9: ['簡易自動滅火'], 10: ['海龍'], 11: ['惰性氣體'], 12: ['鹵化烴'], 13: ['火警自動警報', '探測器', '受信總機'],
             14: ['緊急廣播'], 15: ['瓦斯漏氣'], 16: ['一一九', '119'], 17: ['標示設備', '出口標示燈', '避難方向指示燈'],
             18: ['避難器具', '緩降機', '救助袋', '避難梯'], 19: ['緊急照明'], 20: ['連結送水管'], 21: ['消防專用蓄水池'],
             22: ['排煙'], 23: ['緊急電源插座'], 24: ['無線電通信', '防災監控'], 25: ['冷卻撒水'], 26: ['射水設備'], 27: ['配線']}
    n = 0
    for p in papers:
        for q in p['mcq']:
            s = q['stem']
            if '檢修基準' not in s and '檢修項目' not in s:
                continue
            text = s + ' ' + ' '.join(q['options'].values())
            best = max(alias, key=lambda k: sum(text.count(a) for a in alias[k]))
            if sum(text.count(a) for a in alias[best]) == 0:
                continue
            chs[best - 1]['q'].append({'id': p['id'], 'y': p['year'], 'cat': p['cat'], 'sub': p['subject'], 'no': q['no'], 's': s[:120]})
            n += 1
    out = {'name': kb['name'], 'version': kb['version'], 'source': kb['source'],
           'pdf': 'https://law.nfa.gov.tw/GNFA/GetFile.aspx?PFID=0000382671', 'chapters': chs}
    json.dump(out, open(os.path.join(EX, 'data', 'kb-web.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('kb-web.json：%d 章、%d 段；對應歷屆試題 %d 題' % (len(chs), sum(len(c['b']) for c in chs), n))
    for c in chs:
        print(' 第%d章 %s：%d 段、考題 %d' % (c['no'], c['title'], len(c['b']), len(c['q'])))


if __name__ == '__main__':
    main()
