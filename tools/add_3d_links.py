# -*- coding: utf-8 -*-
"""在各圖解頁的頂端導覽列加上「🧊 3D 動畫」按鈕（可重複執行，靠 <!-- 3d --> 標記避免重複插入）。
新增 3D 動畫時，改下面的 MAP 再執行：python tools/add_3d_links.py
"""
import os, re, urllib.parse

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 圖解頁檔名前綴 → [(3d 檔名, 按鈕文字)]
MAP = {
    '04a': [('foam.html', '泡沫')],
    '06': [('co2.html', '二氧化碳放射時序')],
    '07': [('dry-powder.html', '乾粉')],
    '08': [('halon.html', '鹵化烴')],
    '09': [('water-mist.html', '水霧')],
    '10': [('standpipe.html', '連結送水管')],
    '11': [('water-tank.html', '消防專用蓄水池')],
    '12': [('smoke-exhaust.html', '排煙')],
    '13': [('outlet-radio.html', '插座・無線電・防災監控')],
    '15': [('extinguisher.html', '滅火器'), ('indoor-hydrant.html', '室內消防栓'), ('outdoor-hydrant.html', '室外消防栓')],
    '16': [('sprinkler.html', '自動撒水')],
    '17': [('fire-alarm.html', '火警自動警報')],
    '18': [('emergency-pa.html', '緊急廣播'), ('gas-leak.html', '瓦斯漏氣')],
    '19': [('evac-sign.html', '標示設備')],
    '20': [('descender.html', '緩降機')],
    '21': [('evac-sign.html', '緊急照明')],
    '22': [('haz-tank.html', '公危儲槽'), ('haz-scope.html', '①適用與分級'), ('haz-classes.html', '②五種設備與效能值'), ('haz-water.html', '③水系加嚴'), ('haz-foam.html', '④泡沫'), ('haz-gas.html', '⑤氣體乾粉與配置'), ('haz-hpgas.html', '⑥高壓氣體')],
}

n = 0
for f in sorted(os.listdir(REPO)):
    m = re.match(r'^(\d+a?)-.*\.html$', f)
    if not m or m.group(1) not in MAP:
        continue
    p = os.path.join(REPO, f)
    t = open(p, encoding='utf-8').read()
    btns = ''.join('<a class="btn go" href="3d/%s">🧊 3D 動畫：%s</a>' % (urllib.parse.quote(h), name) for h, name in MAP[m.group(1)])
    block = '<!-- 3d -->' + btns + '<!-- /3d -->'
    if '<!-- 3d -->' in t:
        t2 = re.sub(r'<!-- 3d -->.*?<!-- /3d -->', block, t, count=1, flags=re.S)
    else:
        # 插在第一個導覽列的「回學習首頁」按鈕後面
        i = t.find('<div class="navbar"')
        j = t.find('</a>', i) + 4 if i >= 0 else -1
        if j < 4:
            print('找不到導覽列：', f); continue
        t2 = t[:j] + '\n    ' + block + t[j:]
    if t2 != t:
        open(p, 'w', encoding='utf-8').write(t2); n += 1
        print('已更新', f)
print('共更新 %d 頁' % n)
