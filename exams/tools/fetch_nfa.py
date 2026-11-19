# -*- coding: utf-8 -*-
"""從內政部消防署「消防法令查詢系統」抓行政規則、基準、要點、公告（全國法規資料庫沒收錄的） → exams/meta/nfa.json
每份抓「所有條文」；條文寫「詳如附件」而內容在 PDF 的，自動下載附件抽文字。

用法：python exams/tools/fetch_nfa.py
新增資料：在 DOCS 加一行 (代號, LSID, 名稱)。LSID 在 https://law.nfa.gov.tw/GNFA/FSYS/index.aspx?typecode=A002 等頁面的連結裡。
檢修基準篇幅大，另由 fetch_kb.py 依章切分。
"""
import os, re, json, html as H, subprocess, tempfile, time
import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), 'meta', 'nfa.json')
BASE = 'https://law.nfa.gov.tw/GNFA/'

DOCS = [
    ('pump', 'FL005066', '消防幫浦加壓送水裝置等及配管摩擦損失計算基準'),
    ('co2-sign', 'FL036103', '二氧化碳滅火設備各種標示規格'),
    ('dry-sign', 'FL036102', '乾粉滅火設備各種標示規格'),
    ('evac-fix', 'FL035053', '避難器具支固器具及固定部之結構、強度計算及施工方法'),
    ('review', 'FL019489', '消防機關辦理建築物消防安全設備審查及查驗作業基準'),
    ('review-s', 'FL044067', '消防機關辦理建築物消防安全設備審查及查驗作業基準補充規定'),
    ('mixed', 'FL004523', '複合用途建築物判斷基準'),
    ('fpm-note', 'FL044064', '消防機關辦理防火管理業務注意事項'),
    ('flame-cert', 'FL102631', '防焰性能認證實施辦法'),
    ('flame-test', 'FL102632', '防焰物品或其材料防焰性能試驗標準'),
    ('inspect-op', 'FL045851', '各類場所消防安全設備檢修及申報作業基準'),
    ('insp-agency', 'FL092310', '消防安全設備檢修專業機構管理辦法'),
    ('pump-cert', 'FL068188', '消防幫浦認可基準'),
    ('sign6', 'FL005048', '六類公共危險物品製造儲存及處理場所標示板規格及設置要點'),
    ('sign-gas', 'FL092632', '可燃性高壓氣體場所標示板規格及設置要點'),
    ('firewall', 'FL031551', '防火牆及防火水幕設置基準'),
    ('blastwall', 'FL025320', '可燃性高壓氣體儲存場所防爆牆設置基準'),
    ('lpg-report', 'FL102630', '經營家用液化石油氣零售事業者資料申報作業辦法'),
    ('tank-insp', 'FL102803', '液體公共危險物品儲槽檢查實施辦法'),
    ('fireworks', 'FL027784', '爆竹煙火管理條例'),
    ('fireworks-site', 'FL029109', '爆竹煙火製造儲存販賣場所設置及安全管理辦法'),
]

# 公告（函釋及公告）：(代號, news id, 名稱)。附件 PDF（公告本文、總說明、對照表）全部抽文字
NEWS = [
    ('fpm-scope', '2908', '消防法第十三條第一項一定規模以上之建築物（114.9.16 修正，115.1.1 生效）'),
    ('fpm-scope-113', '2711', '消防法第十三條第一項一定規模以上之建築物（113.3.7 訂定）'),
    ('flame-site', '1780', '應使用附有防焰標示之地毯、窗簾、布幕、展示用廣告板及其他指定防焰物品之場所（108.3.15）'),
    ('insp-scope', '2397', '消防法第九條第一項第二款一定規模以上之場所（111.9.19）'),
    ('biz-use', '2673', '核釋消防法第37條及第40條所定「供營業使用場所」之認定原則'),
    ('lab-scope', '2863', '消防法第二十一條之一第二項一定規模以上之實驗室或倉庫（114.6.1 生效）'),
]


def curl(url, path):
    subprocess.run(['curl', '-s', '-L', '-m', '300', url, '-o', path], check=True)


def main():
    tmp = tempfile.mkdtemp()
    out = []
    for key, lsid, name in DOCS:
        p = os.path.join(tmp, key + '.html')
        curl(BASE + 'FLAW/FLAWDAT02.aspx?LSID=' + lsid, p)
        s = open(p, encoding='utf-8', errors='replace').read()
        m = re.search(r'id="Lawname">.*?</a>\s*\(([^)]*)\)', s, re.S)
        ver = m.group(1).strip() if m else ''
        arts = []
        for no, body in re.findall(r'<div class="col-no"><a [^>]*>([^<]+)</a>.*?<div class="col-data"><pre>(.*?)</pre>', s, re.S):
            t = H.unescape(re.sub(r'<[^>]+>', '', body))
            t = '\n'.join(l.strip() for l in t.split('\n'))
            arts.append({'n': no.strip(), 'body': t.strip()})
        att = ''
        files = re.findall(r'GetFile\.aspx\?PFID=(\d+)', s)
        if files and (not arts or any('附件' in a['body'] and len(a['body']) < 120 for a in arts)):
            pdf = os.path.join(tmp, key + '.pdf')
            curl(BASE + 'GetFile.aspx?PFID=' + files[0], pdf)
            if open(pdf, 'rb').read(4) == b'%PDF':
                att = '\n'.join(pg.get_text() for pg in fitz.open(pdf))
        out.append({'key': key, 'lsid': lsid, 'name': name, 'version': ver,
                    'source': BASE + 'FLAW/FLAWDAT01.aspx?LSID=' + lsid, 'arts': arts, 'attachment': att})
        print('%-10s %s（%s）條文 %d、附件 %d 字' % (key, name, ver, len(arts), len(att)))
        time.sleep(1)
    for key, nid, name in NEWS:
        p = os.path.join(tmp, key + '.html')
        curl(BASE + 'news.aspx?id=' + nid, p)
        s = open(p, encoding='utf-8', errors='replace').read()
        files = []
        for fid, fname in re.findall(r'href="downloadFile\.aspx\?sdMsgId=\d+&FileId=(\d+)"[^>]*>([^<]*)<', s):
            pdf = os.path.join(tmp, key + fid + '.pdf')
            curl(BASE + 'downloadFile.aspx?sdMsgId=%s&FileId=%s' % (nid, fid), pdf)
            NL = chr(10)
            txt = NL.join(pg.get_text() for pg in fitz.open(pdf)) if open(pdf, 'rb').read(4) == b'%PDF' else ''
            files.append({'name': H.unescape(fname).strip(), 'text': txt})
        out.append({'key': key, 'news': nid, 'name': name, 'source': BASE + 'news.aspx?id=' + nid, 'arts': [],
                    'attachment': (NL * 2).join('【%s】%s%s' % (f['name'], NL, f['text']) for f in files)})
        print('%-10s %s：附件 %d 份、%d 字' % (key, name, len(files), sum(len(f['text']) for f in files)))
        time.sleep(1)
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
