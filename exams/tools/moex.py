# -*- coding: utf-8 -*-
"""考試院「考畢試題查詢」小工具：ASP.NET postback。"""
import re, html, time, urllib.request, urllib.parse, http.cookiejar, sys, os

BASE = 'https://wwwq.moex.gov.tw/exam/'
URL = BASE + 'wFrmExamQandASearch.aspx'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) study-notes-fetcher'

import ssl
# 仍驗證憑證；只關掉 Python 3.13+ 預設的 X509_STRICT（考試院憑證缺 SKI 擴充欄位）
_ctx = ssl.create_default_context()
_ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj),
                                 urllib.request.HTTPSHandler(context=_ctx))
op.addheaders = [('User-Agent', UA)]


def get(url, data=None):
    time.sleep(1.0)  # 禮貌間隔
    if data is not None:
        data = urllib.parse.urlencode(data).encode('utf-8')
    r = op.open(url, data, timeout=60)
    return r.read()


def hidden(t):
    d = {}
    for m in re.finditer(r'<input[^>]*type="hidden"[^>]*>', t):
        n = re.search(r'name="([^"]+)"', m.group(0))
        v = re.search(r'value="([^"]*)"', m.group(0))
        if n:
            d[n.group(1)] = html.unescape(v.group(1)) if v else ''
    return d


def options(t, name):
    s = re.search(r'name="%s"[^>]*>(.*?)</select>' % re.escape(name), t, re.S)
    if not s:
        return []
    return [(v, html.unescape(x).strip())
            for v, x in re.findall(r'<option[^>]*value="([^"]*)"[^>]*>([^<]*)</option>', s.group(1))]


P = 'ctl00$holderContent$'


def exams_for_years(y1, y2):
    t = get(URL).decode('utf-8', 'replace')
    d = hidden(t)
    d[P + 'wUctlExamYearStart$ddlExamYear'] = str(y1)
    d[P + 'wUctlExamYearEnd$ddlExamYear'] = str(y2)
    d[P + 'btnYear'] = '查詢'
    t = get(URL, d).decode('utf-8', 'replace')
    return t, options(t, P + 'ddlExamCode')


def search(t_prev, code, y1, y2):
    d = hidden(t_prev)
    d[P + 'wUctlExamYearStart$ddlExamYear'] = str(y1)
    d[P + 'wUctlExamYearEnd$ddlExamYear'] = str(y2)
    d[P + 'ddlExamCode'] = code
    d[P + 'btnSearch'] = '查詢'
    return get(URL, d).decode('utf-8', 'replace')
