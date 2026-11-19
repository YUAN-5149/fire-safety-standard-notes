# -*- coding: utf-8 -*-
"""下載內政部消防署「消防安全設備及必要檢修項目檢修基準」完整條文 PDF，抽文字並依章切分 → exams/meta/kb.json
來源：消防法令查詢系統 https://law.nfa.gov.tw/GNFA/FLAW/FLAWDAT01.aspx?LSID=FL094728
（全國法規資料庫沒有收錄這份公告，所以從消防署抓。PDF 約 5 MB，不進版控。）

用法：python exams/tools/fetch_kb.py [已下載的 PDF 路徑]
基準修正時：到上面網址確認新的附件連結（GetFile.aspx?PFID=…），更新 PFID 後重跑。
"""
import os, re, sys, json, subprocess, tempfile
import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), 'meta', 'kb.json')
PFID = '0000382671'          # 114.01.09 修正版附件
SRC = 'https://law.nfa.gov.tw/GNFA/FLAW/FLAWDAT01.aspx?LSID=FL094728'
VERSION = '114.01.09 修正（內授消字第1131606634號）'

CN = '一二三四五六七八九十'
def cn(n):
    if n <= 10: return CN[n - 1] if n < 10 else '十'
    if n < 20: return '十' + CN[n - 11]
    return CN[n // 10 - 1] + '十' + ('' if n % 10 == 0 else CN[n % 10 - 1])


def main():
    if len(sys.argv) > 1:
        pdf = sys.argv[1]
    else:
        pdf = os.path.join(tempfile.mkdtemp(), 'kb.pdf')
        subprocess.run(['curl', '-s', '-L', '-m', '300', 'https://law.nfa.gov.tw/GNFA/GetFile.aspx?PFID=' + PFID, '-o', pdf], check=True)
    doc = fitz.open(pdf)
    pages = [pg.get_text() for pg in doc]
    toc = pages[0]
    titles = re.findall(r'第([一二三四五六七八九十]+)章\s+(\S+(?:\s\S+)?)\s+\d+-1', toc)
    full = '\n'.join(pages[1:])
    # 頁尾的「2-14」這類頁碼拿掉
    full = re.sub(r'\n\s*\d{1,2}-\d{1,3}\s*\n', '\n', full)
    chapters = []
    pos = []
    for i in range(1, 40):
        m = re.search(r'\n\s*第%s章\s' % cn(i), '\n' + full)
        if not m: break
        pos.append((i, m.start()))
    for k, (i, p) in enumerate(pos):
        end = pos[k + 1][1] if k + 1 < len(pos) else len(full) + 1
        body = full[max(0, p - 1):end - 1].strip()
        first = body.split('\n', 1)
        title = re.sub(r'^第[一二三四五六七八九十]+章\s*', '', first[0]).strip()
        text = first[1] if len(first) > 1 else ''
        text = re.sub(r'[ \t]+\n', '\n', text)
        chapters.append({'no': i, 'title': title, 'text': text.strip()})
    json.dump({'name': '消防安全設備及必要檢修項目檢修基準', 'version': VERSION, 'source': SRC,
               'chapters': chapters}, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('共 %d 章、%d 字 → %s' % (len(chapters), sum(len(c['text']) for c in chapters), OUT))
    for c in chapters:
        print(' 第%s章 %s（%d 字）' % (cn(c['no']), c['title'], len(c['text'])))


if __name__ == '__main__':
    main()
