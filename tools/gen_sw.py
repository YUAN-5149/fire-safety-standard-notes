# -*- coding: utf-8 -*-
"""產生 sw.js（離線快取）並在每一頁插入註冊程式碼。內容有變動時版本號自動改變。
每次改完網頁、重產資料後執行：python tools/gen_sw.py

快取策略：
  - 網頁（.html）與資料（.json）：先連網取最新版，離線時用快取
  - 其他（js、css、圖示、three.js CDN）：先用快取、背景更新
"""
import os, re, hashlib, json, urllib.parse

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THREE = ['https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js',
         'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js']

files = []
for root, dirs, fs in os.walk(REPO):
    dirs[:] = [d for d in dirs if d not in ('.git', 'raw', 'tools', 'meta', '.claude')]
    for f in fs:
        rel = os.path.relpath(os.path.join(root, f), REPO).replace(os.sep, '/')
        if re.search(r'\.(html|css|js|json|png|ico|webmanifest)$', f) and rel != 'sw.js' \
                and not rel.startswith('exams/data/papers') and not rel.startswith('exams/tools'):
            files.append(rel)
files.sort()

# 3d 頁面引用 engine.js?v=…，預先快取要用同一個網址
ver_q = ''
eng = open(os.path.join(REPO, '3d', 'extinguisher.html'), encoding='utf-8').read() if os.path.exists(os.path.join(REPO, '3d', 'extinguisher.html')) else ''
m = re.search(r"engine\.js(\?v=\w+)", eng)
if m:
    ver_q = m.group(1)

h = hashlib.sha1()
for f in files:
    h.update(f.encode()); h.update(open(os.path.join(REPO, f), 'rb').read())
version = h.hexdigest()[:10]

urls = ['./'] + [urllib.parse.quote(f) + (ver_q if f in ('3d/engine.js', '3d/anim.css') else '') for f in files] + THREE
sw = '''// 由 tools/gen_sw.py 產生，請勿手改
const CACHE = 'fire-notes-%s';
const PRECACHE = %s;

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => Promise.all(PRECACHE.map(u => c.add(u).catch(() => null)))).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith('fire-notes-') && k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  const same = url.origin === location.origin;
  if (!same && url.hostname !== 'cdn.jsdelivr.net') return;          // 考選部 PDF、法規資料庫等外部連結不快取
  const fresh = same && (req.mode === 'navigate' || /\\.(html|json)$/.test(url.pathname) || url.pathname.endsWith('/'));
  if (fresh) {
    e.respondWith(fetch(req).then(r => { if (r.ok) { const cp = r.clone(); caches.open(CACHE).then(c => c.put(req, cp)); } return r; })
      .catch(() => caches.match(req).then(r => r || caches.match(req, {ignoreSearch: true}))));
  } else {
    e.respondWith(caches.match(req).then(hit => {
      const net = fetch(req).then(r => { if (r.ok) { const cp = r.clone(); caches.open(CACHE).then(c => c.put(req, cp)); } return r; }).catch(() => hit);
      return hit || net;
    }));
  }
});
''' % (version, json.dumps(urls, ensure_ascii=False, indent=0))
open(os.path.join(REPO, 'sw.js'), 'w', encoding='utf-8').write(sw)

# 註冊程式碼：根目錄頁面註冊 sw.js；3d/ 頁面由 engine.js 註冊，3d/index.html 用 ../sw.js
TAG = '<!-- sw -->'
def snippet(path):
    return TAG + "<script>if('serviceWorker' in navigator)addEventListener('load',()=>navigator.serviceWorker.register('%s').catch(()=>{}));</script>" % path
n = 0
targets = [f for f in files if f.endswith('.html') and '/' not in f] + ['3d/index.html', 'tools/index_tpl.html']
for f in targets:
    p = os.path.join(REPO, f)
    if not os.path.exists(p):
        continue
    t = open(p, encoding='utf-8').read()
    s = snippet('../sw.js' if f.startswith('3d/') else 'sw.js')
    t2 = re.sub(r'<!-- sw --><script>.*?</script>', s, t, count=1) if TAG in t else t.replace('</body>', s + '\n</body>', 1)
    if t2 != t:
        open(p, 'w', encoding='utf-8').write(t2); n += 1
print('sw.js 版本 %s，預先快取 %d 個檔案；插入註冊碼 %d 頁' % (version, len(urls), n))
