# -*- coding: utf-8 -*-
"""把 exams/data/papers.json 轉成網頁用的 exams/data/exam.json：
  - 每題標上「主題」（關鍵字分類，連到站內圖解頁）
  - 與設置標準條文做字元雙連詞相似度比對，列出「可能相關條文」（自動比對，僅供參考）
網頁（25-歷屆試題.html、26-考試策略分析.html）都只讀 exam.json。

用法：python exams/tools/build_exam_data.py
"""
import os, re, json, math, collections

HERE = os.path.dirname(os.path.abspath(__file__))
EX = os.path.dirname(HERE)
ROOT = os.path.dirname(EX)

# ── 主題分類：(代碼, 名稱, 關鍵字, 站內頁面) ── 依序比對，命中關鍵字最多者勝
EQUIP = [
    ('ext', '滅火器', ['滅火器', '滅火效能值', '能力單位'], '15-滅火器與室內外消防栓-圖解.html'),
    ('hyd', '室內／室外消防栓', ['消防栓', '瞄子', '水帶', '放水壓力', '加壓送水'], '15-滅火器與室內外消防栓-圖解.html'),
    ('spr', '自動撒水設備', ['撒水', '密閉式', '開放式', '一齊開放閥', '流水檢知', '放水型', '末端查驗'], '16-自動撒水設備-圖解.html'),
    ('mist', '水霧滅火設備', ['水霧'], '09-水霧設備-圖解.html'),
    ('foam', '泡沫滅火設備', ['泡沫', '發泡倍率', '泡沫原液', '混合比'], '04a-泡沫設備-圖解.html'),
    ('co2', '二氧化碳滅火設備', ['二氧化碳', 'CO2', 'CO₂'], '06-二氧化碳設備-圖解.html'),
    ('dry', '乾粉滅火設備', ['乾粉', '加壓用氣體', '蓄壓用氣體'], '07-乾粉設備-圖解.html'),
    ('halo', '鹵化烴／潔淨滅火藥劑', ['鹵化烴', '海龍', 'HFC', 'IG-', 'FK-5', '潔淨滅火', 'Halon', 'halon'], '08-鹵化烴設備-圖解.html'),
    ('simple', '簡易自動滅火設備', ['簡易自動滅火'], '16-自動撒水設備-圖解.html'),
    ('fa', '火警自動警報設備', ['火警', '探測器', '受信總機', '中繼器', '發信機', '偵煙', '定溫', '差動', '火焰式', '警戒區'], '17-火警自動警報設備-圖解.html'),
    ('gas', '瓦斯漏氣火警', ['瓦斯漏氣', '檢知器', '瓦斯'], '18-緊急廣播與瓦斯漏氣-圖解.html'),
    ('pa', '緊急廣播設備', ['緊急廣播', '揚聲器', '擴音機'], '18-緊急廣播與瓦斯漏氣-圖解.html'),
    ('119', '一一九火災通報裝置', ['一一九', '119', '火災通報'], '17-火警自動警報設備-圖解.html'),
    ('sign', '標示設備', ['出口標示燈', '避難方向指示燈', '避難指標', '觀眾席引導燈', '標示燈', '標示設備'], '19-標示設備-圖解.html'),
    ('evac', '避難器具', ['避難器具', '緩降機', '救助袋', '避難梯', '滑台', '避難橋', '滑杆', '避難繩索', '收容人員'], '20-避難器具與收容人員-圖解.html'),
    ('elight', '緊急照明設備', ['緊急照明'], '21-緊急照明設備-圖解.html'),
    ('stand', '連結送水管', ['連結送水管', '送水口', '中繼幫浦'], '10-連結送水管-圖解.html'),
    ('tank', '消防專用蓄水池', ['蓄水池', '採水口', '投入孔'], '11-消防專用蓄水池-圖解.html'),
    ('smoke', '排煙設備', ['排煙', '防煙壁', '排煙口', '特別安全梯', '緊急昇降機間'], '12-排煙設備-圖解.html'),
    ('outlet', '緊急電源插座／無線電／防災監控', ['緊急電源插座', '無線電通信輔助', '防災監控', '洩波同軸'], '13-緊急電源插座與無線電-圖解.html'),
    ('power', '緊急電源與配線', ['緊急電源', '耐燃保護', '耐熱保護', '配線', '蓄電池', '發電機'], '17-火警自動警報設備-圖解.html'),
    ('pump', '加壓送水裝置與水源', ['幫浦', '水源', '呼水', '全揚程', '水箱', '重力水箱', '壓力水箱'], '15-滅火器與室內外消防栓-圖解.html'),
    ('haz', '公共危險物品場所', ['公共危險物品', '可燃性高壓氣體', '管理量', '儲槽', '顯著滅火困難', '一般處理場所', '製造場所', '室內儲存', '室外儲槽', '液化石油氣', '加油站', '硫磺', '滅火困難', '六類物品'], '22-公共危險物品場所-圖解.html'),
    ('clean', '潔淨區', ['潔淨區', '無塵室', '電子工業'], '14a-潔淨區消防安全設備-圖解.html'),
]
LAW = [
    ('law-fire', '消防法與施行細則', ['消防法', '施行細則', '管理權人', '主管機關', '罰鍰', '檢修申報', '消防安全設備檢修', '消防設備師', '消防設備士', '暫行從事'], None),
    ('law-fpm', '防火管理／防護計畫', ['防火管理', '防護計畫', '自衛消防', '共同消防', '防火管理人'], None),
    ('law-flame', '防焰物品', ['防焰'], None),
    ('law-place', '設置標準：場所分類與應設設備', ['甲類', '乙類', '丙類', '丁類', '戊類', '己類', '第十二條', '第12 條', '應設置', '危險工作場所', '有效開口', '無開口樓層', '樓地板面積合計'], '24-第二編-消防設計-圖解.html'),
    ('law-fireworks', '爆竹煙火管理', ['爆竹煙火', '煙火'], None),
    ('law-disaster', '災害防救法', ['災害防救', '災害應變'], None),
    ('law-build', '建築法規（防火區劃等）', ['建築技術規則', '防火區劃', '防火構造', '建築法', '耐燃材料', '耐火'], None),
    ('law-review', '審查查驗與檢修', ['審查', '查驗', '竣工', '檢修', '認可', '基準'], None),
]
FIRE = [
    ('fs-comb', '燃燒理論', ['燃燒', '燃點', '閃火點', '引火點', '發火點', '燃燒範圍', '爆炸界限', '燃燒下限', '限氧濃度', '活化能', '自燃', '燃燒熱', '化學計量', '發火', '氧氣', '惰性', '氧化反應'], None),
    ('fs-class', '火災分類與滅火原理', ['A 類火災', 'B 類火災', 'C 類火災', 'D 類火災', '類火災', '滅火原理', '冷卻', '窒息', '抑制', '隔離', '滅火劑'], None),
    ('fs-heat', '熱傳與火災成長', ['熱傳', '傳導', '對流', '輻射', '熱釋放率', '火災成長', '閃燃', '爆燃', '複燃', '回燃', 't2', '火羽', '天花板噴流', '蒸發', '比熱', '潛熱', '溫度'], None),
    ('fs-smoke', '煙與毒性氣體', ['煙', '一氧化碳', '氰化氫', '毒性', '能見度', '減光', '中性帶', '煙囪效應'], None),
    ('fs-expl', '爆炸', ['爆炸', '粉塵', 'BLEVE', '蒸氣雲', '爆轟', '爆燃'], None),
    ('fs-chem', '危險物品與化學性質', ['危險物品', '氧化性', '易燃', '自燃性', '禁水性', '有機過氧化物', '金屬', '鈉', '鉀', '電石'], None),
    ('fs-build', '建築防火與避難', ['防火區劃', '耐火', '避難', '防火門', '構造', '安全梯', '人員'], None),
    ('fs-elec', '電氣火災與靜電', ['電氣', '靜電', '短路', '漏電', '過負載', '電弧', '積污導電', '感電', '電線'], None),
    ('fs-calc', '計算題型', ['計算', '公式', 'kW', 'MW', 'kJ', '公斤', 'kg'], None),
]


def topic_of(text, subject):
    pool = FIRE if '火災學' in subject else (LAW + EQUIP if '法規' in subject else EQUIP + LAW)
    best, score = None, 0
    for code, name, kws, page in pool:
        s = sum(text.count(k) for k in kws)
        if s > score:
            best, score = code, s
    return best


# ── 條文相似度（字元雙連詞 TF-IDF）──
def grams(t):
    t = re.sub(r'[\s，。、；：（）「」\(\)\d０-９A-Za-z.,:;%％-]+', '|', t)
    out = collections.Counter()
    for seg in t.split('|'):
        for i in range(len(seg) - 1):
            out[seg[i:i + 2]] += 1
    return out


STOP = set('下列 何者 敘述 正確 錯誤 規定 應設 設置 以上 以下 公尺 平方 依據 依各 各類 場所 消防 安全 設備 標準'.split())


def build_index(arts):
    docs = [grams(a['body']) for a in arts]
    df = collections.Counter(g for d in docs for g in d)
    N = len(docs)
    idf = {g: math.log(N / (1 + c)) + 1 for g, c in df.items()}
    vecs = []
    for d in docs:
        v = {g: (1 + math.log(c)) * idf[g] for g, c in d.items() if g not in STOP}
        n = math.sqrt(sum(x * x for x in v.values())) or 1
        vecs.append({g: x / n for g, x in v.items()})
    return idf, vecs


def related(text, arts, idf, vecs, k=3):
    q = grams(text)
    v = {g: (1 + math.log(c)) * idf[g] for g, c in q.items() if g in idf and g not in STOP}
    n = math.sqrt(sum(x * x for x in v.values())) or 1
    sc = []
    for i, d in enumerate(vecs):
        s = sum(x * d.get(g, 0) for g, x in v.items()) / n
        sc.append((s, i))
    sc.sort(reverse=True)
    return [arts[i]['n'] for s, i in sc[:k] if s >= 0.22]


def main():
    papers = json.load(open(os.path.join(EX, 'data', 'papers.json'), encoding='utf-8'))
    arts = json.load(open(os.path.join(ROOT, 'tools', 'arts.json'), encoding='utf-8'))
    arts = [a for a in arts if a['body'].strip() not in ('（刪除）', '(刪除)')]
    idf, vecs = build_index(arts)
    topics = {c: {'name': n, 'page': p} for c, n, _, p in EQUIP + LAW + FIRE}
    out = []
    for p in papers:
        rec = {'id': p['id'], 'y': p['year'], 'cat': p['cat'], 'sub': p['subject'],
               'calc': p['header'].get('calculator', False), 'time': p['header'].get('time', ''),
               'note': p['key_note'], 'src': p['sources'], 'fig': p['figures'], 'es': [], 'mc': []}
        fire = '火災學' in p['subject']
        for e in p['essays']:
            t = e['text']
            rec['es'].append({'no': e['no'], 't': t, 'pt': e['points'], 'tp': topic_of(t, p['subject']),
                              'rel': [] if fire else related(t, arts, idf, vecs)})
        for q in p['mcq']:
            t = q['stem'] + ' ' + ' '.join(q['options'].values())
            r = {'no': q['no'], 's': q['stem'], 'o': [q['options'].get(k, '') for k in 'ABCD'],
                 'a': q['answer'], 'tp': topic_of(t, p['subject']),
                 'rel': [] if fire else related(t, arts, idf, vecs)}
            if q.get('answer_corrected'):
                r['a2'] = q['answer_corrected']
            rec['mc'].append(r)
        out.append(rec)
    data = {'topics': topics, 'papers': out,
            'built': __import__('datetime').date.today().isoformat()}
    json.dump(data, open(os.path.join(EX, 'data', 'exam.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, separators=(',', ':'))
    tc = collections.Counter(q['tp'] for p in out for q in p['mc'])
    nr = sum(1 for p in out for q in p['mc'] if q['rel'])
    print('exam.json：%d 份試卷，選擇題 %d 題（有相關條文 %d），未分類 %d' %
          (len(out), sum(len(p['mc']) for p in out), nr, tc[None]))
    for c, n in tc.most_common():
        print(' ', topics.get(c, {}).get('name', c), n)


if __name__ == '__main__':
    main()
