// 3D 消防安全設備動畫共用引擎：每支動畫只要提供 steps（文字）與 build（建模）
// 改寫自 interior-renovation-exam/anim/engine.js；新增 flow（流動粒子）、pulse（閃爍）、cfg.page（對應圖解頁）
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
export { THREE };

const CIRC = ['','①','②','③','④','⑤','⑥','⑦','⑧','⑨','⑩','⑪','⑫'];

/**
 * cfg = {
 *   title: '高架木地板施工順序',
 *   steps: [{t,d,tip}, ...]   // steps[0] 是「施工前」
 *   views: {def:{dir,dist,target}, 6:{...}}  // 各步鏡頭（沒寫就用 def）
 *   cut:   {cat: [THREE.Plane...]}            // 剖面按鈕要切的分類
 *   cutLabel, note, build(kit)
 * }
 */
export function createAnim(cfg) {
  const STEPS = cfg.steps;
  const LAST = STEPS.length - 1;

  /* ---------- 版面 ---------- */
  document.body.innerHTML = `
<div class="top"><a href="../index.html">← 消防設備學習首頁</a><a href="./">3D 系統動畫目錄</a>${cfg.page ? `<a href="../${cfg.page}">📐 對應圖解頁</a>` : ''}<span>${cfg.title}</span></div>
<main class="wrap">
  <section class="stage">
    <div class="titles">
      <div class="kicker">${cfg.kicker || '各類場所消防安全設備設置標準'}</div>
      <div class="sub">${cfg.title}</div>
      <h1 id="title"></h1>
    </div>
    <div id="view"><div class="hint">拖曳旋轉・滾輪／雙指縮放</div><div id="err">3D 載入失敗，請確認網路連線後重新整理。</div></div>
    <div class="prog"><i id="bar"></i></div>
    <p id="desc"></p>
    <div class="ctrl">
      <button class="btn" id="prev">◀ 上一步</button>
      <button class="btn pri" id="play">▶ 播放</button>
      <button class="btn" id="next">下一步 ▶</button>
      ${cfg.cut ? `<button class="btn" id="cut" title="${cfg.cutLabel||'切開外層，看裡面的構造'}">剖面</button>` : ''}
      <button class="btn" id="reset">重看視角</button>
    </div>
  </section>
  <aside class="panel">
    <div class="tip"><b>考點・條文</b><span id="tip"></span></div>
    <h2>${cfg.kind==='notes' ? `${LAST} 項重點（點選跳到該項）` : `${LAST} 步驟（點選跳到該步）`}</h2>
    <ol class="steps" id="list"></ol>
    <div class="foot">鍵盤：← → 切換步驟，空白鍵播放／暫停。${cfg.note || '模型比例有誇大，方便看清楚構造；數字以條文為準。'}</div>
  </aside>
</main>`;
  const $ = id => document.getElementById(id);
  const view = $('view');

  /* ---------- 場景 ---------- */
  let renderer;
  try { renderer = new THREE.WebGLRenderer({antialias:true}); }
  catch (e) { $('err').style.display='flex'; throw e; }
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.localClippingEnabled = true;
  view.prepend(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(cfg.bg || '#eef0f1');
  const camera = new THREE.PerspectiveCamera(30, 1, 0.1, 100);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.minDistance = cfg.minDist ?? 2.5;
  controls.maxDistance = Math.max(22, ...Object.values(cfg.views||{}).map(v=>v.dist*2.2));   // 大場景（儲槽、高樓）要能拉遠   // 小物件（鉸鍊、磚）可拉更近
  controls.maxPolarAngle = Math.PI * (cfg.maxPolar ?? 0.49);   // 天花板類要能從下往上看
  if (cfg.minPolar) controls.minPolarAngle = Math.PI * cfg.minPolar;

  scene.add(new THREE.HemisphereLight(0xffffff, 0xcfc8c0, 1.5));
  const sun = new THREE.DirectionalLight(0xffffff, 2.2);
  sun.position.set(...(cfg.sun || [4, 8, 5]));
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  Object.assign(sun.shadow.camera, {left:-5, right:5, top:5, bottom:-5, near:1, far:25});
  sun.shadow.bias = -0.0004;
  scene.add(sun);
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), new THREE.ShadowMaterial({opacity:.12}));
  ground.rotation.x = -Math.PI/2; ground.position.y = cfg.groundY ?? -0.2; ground.receiveShadow = true;
  scene.add(ground);

  /* ---------- 建模小工具 ---------- */
  const EDGE = new THREE.LineBasicMaterial({color:'#3f3a36', transparent:true, opacity:.35});
  const mat = (color, o={}) => new THREE.MeshStandardMaterial({color, roughness:.8, ...o});
  function box(w, h, d, m, {edges=true, shadow=true}={}) {
    const g = new THREE.BoxGeometry(w, h, d);
    const mesh = new THREE.Mesh(g, m.clone());
    mesh.castShadow = shadow; mesh.receiveShadow = true;
    if (edges) mesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(g), EDGE.clone()));
    return mesh;
  }
  // 用「最小角、最大角」放方塊
  function span(x0,y0,z0,x1,y1,z1,m,opt){
    const mesh = box(x1-x0, y1-y0, z1-z0, m, opt);
    mesh.position.set((x0+x1)/2, (y0+y1)/2, (z0+z1)/2);
    return mesh;
  }
  function pipe(a, b, r, m){
    const A=new THREE.Vector3(...a), B=new THREE.Vector3(...b);
    const mesh=new THREE.Mesh(new THREE.CylinderGeometry(r,r,A.distanceTo(B),16), m.clone());
    mesh.position.copy(A).add(B).multiplyScalar(.5);
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0), B.clone().sub(A).normalize());
    mesh.castShadow=true;
    return mesh;
  }
  function group(...children){ const g=new THREE.Group(); children.forEach(c=>g.add(c)); return g; }
  // 向下（或任意方向）箭頭：from → to
  function arrow(from, to, m){
    const A=new THREE.Vector3(...from), B=new THREE.Vector3(...to);
    const dir=B.clone().sub(A); const len=dir.length(); dir.normalize();
    const g=new THREE.Group();
    const shaft=new THREE.Mesh(new THREE.CylinderGeometry(.018,.018,len-.12,12), m.clone()); shaft.position.y=(len-.12)/2;
    const tip=new THREE.Mesh(new THREE.ConeGeometry(.055,.12,16), m.clone()); tip.position.y=len-.06;
    g.add(shaft,tip); g.position.copy(A);
    g.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0), dir);
    return g;
  }

  // 文字標籤（永遠面向鏡頭），字太長會自動縮小；tone: 'good' 綠、'bad' 紅
  const LABELS=[], _wp=new THREE.Vector3(), _dir=new THREE.Vector3(), _up=new THREE.Vector3();
  const TONES={ note:['#fffbeb','#d97706','#92400e'], good:['#f0fdf4','#16a34a','#166534'], bad:['#fef2f2','#dc2626','#991b1b'] };
  function label(text, x, y, z, w=1.3, tone='note'){
    const [bg,bd,fg]=TONES[tone]||TONES.note;
    const c=document.createElement('canvas'); c.width=512; c.height=128;
    const g=c.getContext('2d');
    g.globalAlpha=.86; g.fillStyle=bg; g.strokeStyle=bd; g.lineWidth=8;
    g.beginPath(); g.roundRect(6,6,500,116,28); g.fill(); g.globalAlpha=1; g.stroke();
    g.fillStyle=fg;
    let fs=54; do { g.font=`bold ${fs}px "Noto Sans TC","Microsoft JhengHei",sans-serif`; fs-=2; } while (g.measureText(text).width>450 && fs>20);
    g.textAlign='center'; g.textBaseline='middle'; g.fillText(text,256,68);
    const tex=new THREE.CanvasTexture(c); tex.colorSpace=THREE.SRGBColorSpace;
    // 每幀依鏡頭距離縮放，維持固定螢幕大小（以 5.5 m 觀看時的寬 w 為準），拉近也不會塞滿畫面
    const s=new THREE.Sprite(new THREE.SpriteMaterial({map:tex, depthTest:false}));
    s.scale.set(w, w/4, 1); s.position.set(x,y,z); s.renderOrder=10;
    s.userData.labelW=w; s.userData.base=s.position.clone(); s.userData.off=0; LABELS.push(s);
    return s;
  }

  /* ---------- 動畫項目 ---------- */
  const items = [];
  const DUR = 0.55;
  function add(step, obj, {delay=0, drop=0.45, until=99, cat='', glow=true}={}) {
    const mats=[];
    obj.traverse(o=>{ if(o.material){ const m=o.material; m.transparent=true; m.userData.base=m.opacity; if(!glow) m.userData.glowable=false; mats.push(m);} });
    items.push({step, obj, delay, drop, until, cat, mats, baseY:obj.position.y, t0:-1, glow:0});
    obj.visible = false;
    scene.add(obj);
    return obj;
  }
  const fixed = obj => { scene.add(obj); return obj; };

  // 注意事項用：在某點畫橘色圈＋指向箭頭，只在該項顯示。face: 'z' 牆面、'y' 地面／天花、'x' 側牆
  const MARK = new THREE.MeshStandardMaterial({color:'#f97316', emissive:'#f97316', emissiveIntensity:.7});
  function mark(step, x, y, z, {r=0.12, face='z', text, tone, tw=1.1, tx, ty, tz}={}){
    const g=new THREE.Group();
    const ring=new THREE.Mesh(new THREE.TorusGeometry(r, Math.max(.008, r*.09), 10, 40), MARK.clone());
    if (face==='y') ring.rotation.x=Math.PI/2; else if (face==='x') ring.rotation.y=Math.PI/2;
    g.add(ring); g.position.set(x,y,z);
    add(step, g, {until:step, drop:0, glow:false});
    if (text) add(step, label(text, tx??x, ty??(y+r+0.18), tz??(z+0.1), tw, tone), {until:step, drop:0, glow:false, delay:.15});
    return g;
  }

  // 沿路徑流動的粒子（水流、煙、藥劑、電訊號）。pts: [[x,y,z],...]；顯示與否跟著所屬 add 的群組
  const FLOWS=[];
  function flow(pts, m, {n=14, r=.035, speed=.35, closed=false}={}){
    const curve=new THREE.CatmullRomCurve3(pts.map(p=>new THREE.Vector3(...p)), closed, 'catmullrom', 0.05);
    const g=new THREE.Group(), geo=new THREE.SphereGeometry(r,10,8);
    for(let i=0;i<n;i++){ const s=new THREE.Mesh(geo, m.clone()); s.userData.u=i/n; g.add(s); }
    FLOWS.push({g, curve, speed:speed/Math.max(.5,curve.getLength())});
    return g;
  }
  // 平面字牌（標識、標示燈面板）：固定在場景中，不會轉向鏡頭。normal: 'z' 面向 +z、'x' 面向 +x、'-x'、'-z'、'y' 朝上、'-y' 朝下
  function plate(text, w, h, {bg='#c81e1e', fg='#ffffff', normal='z', bold=true, glow=0}={}){
    const c=document.createElement('canvas'); const R=256; c.width=Math.round(R*w/h); c.height=R;
    const g=c.getContext('2d'); g.fillStyle=bg; g.fillRect(0,0,c.width,c.height);
    g.fillStyle=fg; let fs=Math.round(R*.62);
    do { g.font=`${bold?'bold ':''}${fs}px "Noto Sans TC","Microsoft JhengHei",sans-serif`; fs-=4; } while (g.measureText(text).width>c.width*.9 && fs>16);
    g.textAlign='center'; g.textBaseline='middle'; g.fillText(text,c.width/2,R*.54);
    const tex=new THREE.CanvasTexture(c); tex.colorSpace=THREE.SRGBColorSpace;
    const m=new THREE.MeshStandardMaterial({map:tex, roughness:.6, emissive: glow? '#ffffff':'#000000', emissiveMap: glow? tex:null, emissiveIntensity:glow||1});
    const mesh=new THREE.Mesh(new THREE.PlaneGeometry(w,h), m);
    const rot={z:[0,0,0],'-z':[0,Math.PI,0],x:[0,Math.PI/2,0],'-x':[0,-Math.PI/2,0],y:[-Math.PI/2,0,0],'-y':[Math.PI/2,0,0]}[normal];
    mesh.rotation.set(...rot);
    return mesh;
  }
  // 尺寸線：a → b 細線＋兩端短橫＋中點標籤
  function dim(a, b, text, {w=1, tone='note', m, off}={}){
    const M=m||new THREE.MeshStandardMaterial({color:'#7c2d12', roughness:.6});
    const g=new THREE.Group(); g.add(pipe(a,b,.012,M));
    [a,b].forEach(p=>{ const s=new THREE.Mesh(new THREE.SphereGeometry(.035,10,8), M.clone()); s.position.set(...p); g.add(s); });
    const mid=a.map((v,i)=>(v+b[i])/2+((off&&off[i])||0));
    if(text) g.add(label(text, mid[0], mid[1], mid[2], w, tone));
    return g;
  }

  // 閃爍（警示燈、表示燈）：材質需有 emissive
  const PULSES=[];
  function pulse(obj, hz=2){ obj.traverse(o=>{ if(o.material&&o.material.emissive) PULSES.push({m:o.material, obj, hz}); }); return obj; }

  cfg.build({THREE, scene, mat, box, span, pipe, group, arrow, label, add, fixed, mark, flow, pulse, plate, dim, EDGE});
  // add() 會 clone 前的材質收進 mats；pulse 要抓實際掛在 mesh 上的材質
  PULSES.forEach(p=>{ p.mats=[]; p.obj.traverse(o=>{ if(o.material&&o.material.emissive) p.mats.push(o.material); }); p.base=p.mats.map(m=>m.emissiveIntensity); });

  /* ---------- 剖面 ---------- */
  let cut=false;
  function applyCut(){
    items.forEach(it=>{
      if(!cfg.cut || !(it.cat in cfg.cut)) return;
      const planes = cut ? cfg.cut[it.cat] : null;
      it.mats.forEach(m=>{ m.clippingPlanes = planes; m.needsUpdate = true; });
    });
    $('cut')?.classList.toggle('on', cut);
  }

  /* ---------- 鏡頭 ---------- */
  const VIEWS = cfg.views || {};
  let fly=null;
  function fitScale(){ const a=camera.aspect; return a<1.2 ? Math.min(1.9, 1.2/a) : 1; }
  function goal(k){
    const v = VIEWS[k] || VIEWS.def;
    const dir = new THREE.Vector3(...v.dir).normalize();
    const tgt = new THREE.Vector3(...v.target);
    return {pos: tgt.clone().add(dir.multiplyScalar(v.dist*fitScale())), tgt};
  }
  function flyTo(k, instant=false){
    const g=goal(k);
    if(instant){ camera.position.copy(g.pos); controls.target.copy(g.tgt); fly=null; controls.update(); return; }
    fly=g;
  }
  controls.addEventListener('start', ()=>{ fly=null; });

  /* ---------- 步驟控制 ---------- */
  let cur=0, playing=false, autoTimer=null;
  const ease=p=>1-Math.pow(1-p,3);
  function setP(it,p){
    const e=ease(p);
    it.obj.position.y = it.baseY + (1-e)*it.drop;
    const o=Math.min(1,p*1.6);
    it.mats.forEach(m=>{
      m.opacity=m.userData.base*o;
      // 不透明材質淡入完成後改回不透明，避免和半透明層（塗裝、PE 布）排序錯亂
      if (m.userData.base>=1 && !m.isSpriteMaterial) { const t = o<1; if (m.transparent!==t) { m.transparent=t; m.needsUpdate=true; } }
    });
  }
  function setGlow(it,g){
    it.mats.forEach(m=>{ if(m.emissive && m.userData.glowable!==false){
      if(m.userData.e0===undefined){ m.userData.e0=m.emissive.clone(); m.userData.ei0=m.emissiveIntensity; }
      if(g>0){ m.emissive.set('#f59e0b'); m.emissiveIntensity=.55*g; }
      else { m.emissive.copy(m.userData.e0); m.emissiveIntensity=m.userData.ei0; }
    }});
  }
  function stepLength(k){
    let m=0; items.forEach(it=>{ if(it.step===k) m=Math.max(m,it.delay); });
    return m+DUR;
  }
  function goTo(k, anim=true){
    cur=Math.max(0,Math.min(LAST,k));
    const now=performance.now()/1000;
    items.forEach(it=>{
      const vis = it.step<=cur && cur<=it.until;
      if(!vis){ it.obj.visible=false; it.t0=-1; it.glow=0; setGlow(it,0); return; }
      if(it.step===cur && anim){ it.obj.visible=true; it.t0=now+it.delay; setP(it,0); }
      else if(!it.obj.visible || it.t0>0){ it.obj.visible=true; it.t0=-1; setP(it,1); }
    });
    updateUI();
    if(anim) flyTo(cur);
    if(playing) schedule();
  }
  function schedule(){
    clearTimeout(autoTimer);
    if(cur>=LAST){ setPlaying(false); return; }
    autoTimer=setTimeout(()=>goTo(cur+1), (stepLength(cur)+2.6)*1000);
  }
  function setPlaying(p){
    playing=p;
    $('play').textContent = p ? '❚❚ 暫停' : (cur>=LAST ? '↻ 重播' : '▶ 播放');
    if(!p) clearTimeout(autoTimer);
  }

  /* ---------- UI ---------- */
  const list=$('list');
  STEPS.slice(1).forEach((s,i)=>{
    const li=document.createElement('li');
    li.innerHTML=`<span class="n">${i+1}</span><span>${s.t}</span>`;
    li.onclick=()=>{ setPlaying(false); goTo(i+1); };
    list.appendChild(li);
  });
  function updateUI(){
    const s=STEPS[cur];
    $('title').innerHTML = cur ? `<span class="no">${cur}</span>${s.t}` : s.t;
    $('desc').textContent=s.d;
    $('tip').textContent=s.tip;
    $('bar').style.width=(cur/LAST*100)+'%';
    $('prev').disabled = cur===0;
    $('next').disabled = cur===LAST;
    [...list.children].forEach((li,i)=>{ li.classList.toggle('cur',i+1===cur); li.classList.toggle('done',i+1<cur); });
    if(!playing) setPlaying(false);
    document.title = (cur?`${CIRC[cur]} ${s.t}｜`:'')+cfg.title+'｜3D 消防設備動畫';
  }
  $('prev').onclick=()=>{ setPlaying(false); goTo(cur-1); };
  $('next').onclick=()=>{ setPlaying(false); goTo(cur+1); };
  $('play').onclick=()=>{
    if(playing){ setPlaying(false); return; }
    setPlaying(true);
    if(cur>=LAST){ goTo(0,false); flyTo(0); schedule(); }
    else goTo(cur+1);
  };
  if($('cut')) $('cut').onclick=()=>{ cut=!cut; applyCut(); };
  $('reset').onclick=()=>flyTo(cur);
  addEventListener('keydown',e=>{
    if(e.key==='ArrowRight'){ setPlaying(false); goTo(cur+1); }
    else if(e.key==='ArrowLeft'){ setPlaying(false); goTo(cur-1); }
    else if(e.key===' '){ e.preventDefault(); $('play').click(); }
  });

  /* ---------- 迴圈 ---------- */
  function resize(){
    const w=view.clientWidth, h=view.clientHeight;
    renderer.setSize(w,h,false);
    camera.aspect=w/h; camera.updateProjectionMatrix();
  }
  new ResizeObserver(resize).observe(view);
  resize();

  renderer.setAnimationLoop(()=>{
    const now=performance.now()/1000;
    for(const it of items){
      if(it.t0>0){
        const p=(now-it.t0)/DUR;
        if(p>=1){ setP(it,1); it.t0=-1; it.glow=now; }
        else setP(it,Math.max(0,p));
      }
      if(it.glow>0){
        const g=1-(now-it.glow)/1.4;
        if(g<=0){ it.glow=0; setGlow(it,0); } else setGlow(it,g);
      }
    }
    if(fly){
      camera.position.lerp(fly.pos,.06);
      controls.target.lerp(fly.tgt,.06);
      if(camera.position.distanceTo(fly.pos)<.01) fly=null;
    }
    controls.update();
    for (const f of FLOWS){ if(!f.g.visible && !(f.g.parent&&f.g.parent.visible)) continue;
      f.g.children.forEach(s=>{ const u=(s.userData.u+now*f.speed)%1; s.position.copy(f.curve.getPointAt(u)); }); }
    for (const p of PULSES){ const k=.5+.5*Math.sin(now*p.hz*Math.PI*2); p.mats.forEach((m,i)=>{ m.emissiveIntensity=p.base[i]*(.15+.85*k); }); }
    // 標籤：依鏡頭距離縮放成固定螢幕大小，再在螢幕上把互相重疊的往上推開
    const vis=[]; const Hpx=renderer.domElement.clientHeight||1, Wpx=renderer.domElement.clientWidth||1, tanF=Math.tan(camera.fov*Math.PI/360);
    for (const s of LABELS){
      let shown=s.visible, p=s.parent; while(shown && p){ shown=p.visible; p=p.parent; }
      if(!shown) continue;
      s.parent.updateWorldMatrix(true,false);
      const wb=s.parent.localToWorld(s.userData.base.clone());
      const d=Math.max(.1, wb.clone().sub(camera.position).dot(camera.getWorldDirection(_dir)));
      const f=Math.min(cfg.labelMax ?? 6, Math.max(0.42, camera.position.distanceTo(wb)/5.5*0.85));
      const k=Hpx/(2*d*tanF);
      let w=s.userData.labelW*f; const maxW=Math.min(Wpx*.94, Math.max(Wpx*.4, 200)); if (w*k > maxW) w=maxW/k;   // 標籤最寬約畫面 40%，避免擋住模型
      const h=w/4; s.scale.set(w, h, 1);
      const ndc=wb.clone().project(camera);
      vis.push({s, d, k, cx:(ndc.x+1)/2*Wpx, cy:(1-ndc.y)/2*Hpx, wp:w*k*.92, hp:h*k*.92});
    }
    vis.sort((a,b)=>b.cy-a.cy);
    const placed=[];
    for (const v of vis){
      let cy;
      const push=(dir)=>{ let y=v.cy, mv=true, g=0;
        while(mv && g++<20){ mv=false;
          for (const q of placed){ if(Math.abs(v.cx-q.cx)<(v.wp+q.wp)/2 && Math.abs(y-q.cy)<(v.hp+q.hp)/2){ y=q.cy+dir*((v.hp+q.hp)/2+3); mv=true; } } }
        return y; };
      cy=push(-1);                                   // 先往上推開
      if (cy-v.hp/2<2) cy=push(1);                   // 推出畫面上緣就改往下
      placed.push({cx:v.cx, cy, wp:v.wp, hp:v.hp});
      const cx=Math.min(Wpx-v.wp/2-2, Math.max(v.wp/2+2, v.cx));       // 左右推回畫面內
      placed[placed.length-1].cx=cx;
      const target=(v.cy-cy)/v.k, tx=(cx-v.cx)/v.k;
      v.s.userData.off += (target-v.s.userData.off)*.25;
      v.s.userData.offX=(v.s.userData.offX||0)+(tx-(v.s.userData.offX||0))*.25;
      _up.set(0,1,0).applyQuaternion(camera.quaternion);
      _dir.set(1,0,0).applyQuaternion(camera.quaternion);
      v.s.position.copy(v.s.userData.base).addScaledVector(_up, v.s.userData.off).addScaledVector(_dir, v.s.userData.offX);
    }
    renderer.render(scene,camera);
  });

  const start = parseInt(new URLSearchParams(location.search).get('step')) || 0;
  flyTo(start, true);
  goTo(start, false);
}
