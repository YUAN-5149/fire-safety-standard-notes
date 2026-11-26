// 第四編「公共危險物品場所」逐條 3D 動畫共用建模工具
// 用法：build(k){ const H = hazKit(k); H.S(1, H.bld(...)); H.L(1,'文字',x,y,z); }
// 每一步（=一條條文）的物件只在該步顯示：S(step, obj) 等於 add(step, obj, {until:step})
export function hazKit(k) {
  const { THREE, mat, span, pipe, group, label, add, fixed, plate, dim, flow, pulse } = k;
  const M = {
    ground: mat('#d6d3cc', { roughness: 1 }), conc: mat('#9ca3af', { roughness: 1 }), wall: mat('#e7e2da', { roughness: 1 }),
    glass: mat('#bfdbfe', { transparent: true, opacity: .35, depthWrite: false }), roof: mat('#94a3b8', { metalness: .2 }),
    tank: mat('#e5e7eb', { metalness: .3, roughness: .5 }), red: mat('#dc2626', { metalness: .3, roughness: .45 }),
    dark: mat('#1f2937'), steel: mat('#9ca3af', { metalness: .6, roughness: .35 }), brass: mat('#ca8a04', { metalness: .7, roughness: .3 }),
    drum: mat('#2563eb', { metalness: .3 }), drumY: mat('#eab308', { metalness: .3 }), wood: mat('#a16207'),
    water: mat('#3b82f6', { transparent: true, opacity: .55, depthWrite: false }), drop: mat('#60a5fa', { emissive: '#2563eb', emissiveIntensity: .6 }),
    spray: mat('#93c5fd', { transparent: true, opacity: .4, depthWrite: false }), foam: mat('#ffffff', { roughness: .9 }),
    foamF: mat('#fef3c7', { emissive: '#fde68a', emissiveIntensity: .5 }), gasF: mat('#e0f2fe', { emissive: '#bae6fd', emissiveIntensity: .6 }),
    fire: mat('#f97316', { emissive: '#f97316', emissiveIntensity: 1 }), sand: mat('#d6b370', { roughness: 1 }),
    green: mat('#16a34a'), skin: mat('#f2c9a0'), shirt: mat('#1d4ed8'), sea: mat('#0e7490', { transparent: true, opacity: .55, depthWrite: false }),
    zoneR: mat('#dc2626', { transparent: true, opacity: .16, depthWrite: false }), zoneG: mat('#16a34a', { transparent: true, opacity: .16, depthWrite: false }),
    zoneB: mat('#2563eb', { transparent: true, opacity: .14, depthWrite: false }), zoneY: mat('#f59e0b', { transparent: true, opacity: .2, depthWrite: false }),
    pink: mat('#be185d'), cyl: mat('#16a34a', { metalness: .4 }), cylG: mat('#64748b', { metalness: .4 }),
  };
  const NE = { edges: false, shadow: false };

  // 只在第 step 步顯示的物件
  const S = (step, obj, delay = 0, o = {}) => add(step, obj, { until: o.until ?? step, drop: o.drop ?? .3, delay, glow: o.glow ?? true });
  const L = (step, text, x, y, z, w = 2, tone = 'note', delay = .2, until) => add(step, label(text, x, y, z, w, tone), { until: until ?? step, drop: 0, glow: false, delay });
  const D = (step, a, b, text, w = 1.6, off, delay = .25) => add(step, dim(a, b, text, { w, off }), { until: step, drop: 0, glow: false, delay });

  const H = {
    M, S, L, D,
    ground() { fixed(span(-60, -0.1, -60, 60, 0, 60, M.ground, { edges: false })); },
    // 地面色塊（範圍、區域）
    pad(x0, z0, x1, z1, m = M.zoneY, y = .03) { return span(x0, y, z0, x1, y + .02, z1, m, NE); },
    disc(x, z, r, m = M.zoneG, y = .04) { const c = new THREE.Mesh(new THREE.CircleGeometry(r, 64), m.clone()); c.rotation.x = -Math.PI / 2; c.position.set(x, y, z); return c; },
    ring(x, z, r0, r1, m = M.zoneR, y = .05) { const c = new THREE.Mesh(new THREE.RingGeometry(r0, r1, 64), m.clone()); c.rotation.x = -Math.PI / 2; c.position.set(x, y, z); return c; },
    // 建築物：外牆半透明可看內部；open=true 時正面牆省略
    bld(x, z, w, d, h, { m = M.wall, roof = true, open = false, floors = 1 } = {}) {
      const g = group(), t = .2;
      g.add(span(x - w / 2, 0, z - d / 2, x + w / 2, h, z - d / 2 + t, m));
      g.add(span(x - w / 2, 0, z - d / 2, x - w / 2 + t, h, z + d / 2, m));
      g.add(span(x + w / 2 - t, 0, z - d / 2, x + w / 2, h, z + d / 2, m));
      if (!open) g.add(span(x - w / 2, 0, z + d / 2 - t, x + w / 2, h, z + d / 2, M.glass, NE));
      for (let f = 1; f < floors; f++) g.add(span(x - w / 2, h * f / floors - .1, z - d / 2, x + w / 2, h * f / floors, z + d / 2, M.conc));
      if (roof) g.add(span(x - w / 2 - .2, h, z - d / 2 - .2, x + w / 2 + .2, h + .25, z + d / 2 + .2, roof === 'glass' ? M.glass : M.roof, roof === 'glass' ? NE : undefined));
      return g;
    },
    // 立式圓筒儲槽（固定頂）
    tank(x, z, r = 3, h = 6, { roof = 'cone', m = M.tank } = {}) {
      const g = group();
      const T = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, 40), m.clone()); T.position.set(x, h / 2, z); T.castShadow = true; g.add(T);
      if (roof === 'cone') { const C = new THREE.Mesh(new THREE.ConeGeometry(r + .05, r * .22, 40), M.roof.clone()); C.position.set(x, h + r * .11, z); g.add(C); }
      if (roof === 'float') { const C = new THREE.Mesh(new THREE.CylinderGeometry(r * .94, r * .94, .2, 40), M.roof.clone()); C.position.set(x, h - .6, z); g.add(C); }
      return g;
    },
    // 臥式儲槽（加氣站、LPG）
    hTank(x, z, r = 1, l = 6, y = 1.4) {
      const g = group(); const T = new THREE.Mesh(new THREE.CylinderGeometry(r, r, l, 28), M.tank.clone()); T.rotation.z = Math.PI / 2; T.position.set(x, y, z); g.add(T);
      [-1, 1].forEach(s => { const e = new THREE.Mesh(new THREE.SphereGeometry(r, 24, 16), M.tank.clone()); e.scale.set(.4, 1, 1); e.position.set(x + s * l / 2, y, z); g.add(e); });
      [-l / 3, l / 3].forEach(dx => g.add(span(x + dx - .2, 0, z - r * .7, x + dx + .2, y - r * .6, z + r * .7, M.conc)));
      return g;
    },
    // 球形儲槽
    sphere(x, z, r = 3) {
      const g = group(); const S0 = new THREE.Mesh(new THREE.SphereGeometry(r, 32, 24), M.tank.clone()); S0.position.set(x, r + 1.4, z); S0.castShadow = true; g.add(S0);
      for (let i = 0; i < 6; i++) { const a = i * Math.PI / 3; g.add(pipe([x + Math.cos(a) * r * .85, 0, z + Math.sin(a) * r * .85], [x + Math.cos(a) * r * .85, r + 1.2, z + Math.sin(a) * r * .85], .12, M.steel)); }
      return g;
    },
    // 防液堤
    dike(x, z, w, d, h = 1) {
      const g = group(), t = .3;
      [[x - w / 2, z - d / 2, x + w / 2, z - d / 2 + t], [x - w / 2, z + d / 2 - t, x + w / 2, z + d / 2], [x - w / 2, z - d / 2, x - w / 2 + t, z + d / 2], [x + w / 2 - t, z - d / 2, x + w / 2, z + d / 2]]
        .forEach(([a, b, c, e]) => g.add(span(a, 0, b, c, h, e, M.conc)));
      return g;
    },
    // 滅火器（big=第四種大型輪架式）
    ext(x, z, { big = false, y = 0 } = {}) {
      const g = group(); const r = big ? .32 : .14, h = big ? 1.1 : .5;
      const c = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, 20), M.red.clone()); c.position.set(x, y + h / 2 + (big ? .25 : 0), z); g.add(c);
      g.add(pipe([x, y + h + (big ? .25 : 0), z], [x, y + h + .12 + (big ? .25 : 0), z], r * .35, M.dark));
      if (big) { [-1, 1].forEach(s => { const w = new THREE.Mesh(new THREE.CylinderGeometry(.25, .25, .1, 16), M.dark.clone()); w.rotation.x = Math.PI / 2; w.position.set(x, .25, z + s * .4); g.add(w); }); g.add(pipe([x, .9, z], [x + .6, 1.4, z], .03, M.dark)); }
      return g;
    },
    bucket(x, z) { const b = new THREE.Mesh(new THREE.CylinderGeometry(.18, .14, .3, 16), M.red.clone()); b.position.set(x, .15, z); return b; },
    trough(x, z) { return group(span(x - .5, 0, z - .3, x + .5, .55, z + .3, M.red), span(x - .45, .5, z - .25, x + .45, .52, z + .25, M.water, NE)); },
    sandBox(x, z) { return group(span(x - .45, 0, z - .3, x + .45, .45, z + .3, M.wood), span(x - .4, .42, z - .25, x + .4, .46, z + .25, M.sand, NE), pipe([x + .2, .45, z], [x + .5, 1.1, z], .03, M.dark)); },
    // 室內消防栓箱（牆面，面向 +z）
    hydIn(x, y, z) { const g = group(span(x - .4, y, z - .12, x + .4, y + 1, z + .12, M.red)); const p = plate('消防栓', .7, .25, { bg: '#c81e1e' }); p.position.set(x, y + .8, z + .13); g.add(p); return g; },
    // 室外消防栓
    hydOut(x, z) { return group(pipe([x, 0, z], [x, 1, z], .2, M.red), pipe([x - .32, .75, z], [x + .32, .75, z], .09, M.brass), new THREE.Mesh(new THREE.SphereGeometry(.2, 16, 10), M.red.clone()).translateX(x).translateY(1).translateZ(z)); },
    // 撒水頭（天花板下）
    head(x, y, z) { return group(pipe([x, y, z], [x, y - .18, z], .04, M.steel), (() => { const d = new THREE.Mesh(new THREE.CylinderGeometry(.11, .11, .02, 12), M.brass.clone()); d.position.set(x, y - .2, z); return d; })()); },
    // 油桶堆
    drums(x, z, nx = 3, nz = 2, m = M.drum) { const g = group(); for (let i = 0; i < nx; i++) for (let j = 0; j < nz; j++) { const c = new THREE.Mesh(new THREE.CylinderGeometry(.3, .3, .9, 16), m.clone()); c.position.set(x + i * .7, .45, z + j * .7); g.add(c); } return g; },
    // 人
    person(x, z, m = M.shirt) { return group(pipe([x, 0, z], [x, .9, z], .14, M.dark), pipe([x, .9, z], [x, 1.45, z], .2, m), new THREE.Mesh(new THREE.SphereGeometry(.16, 14, 10), M.skin.clone()).translateX(x).translateY(1.68).translateZ(z)); },
    // 消防車
    truck(x, z, rot = 0) {
      const g = group(span(-1, 0.4, -3, 1, 2.2, 2, M.red), span(-1, 0.4, 2, 1, 2.6, 3.4, mat('#e5e7eb')));
      [[-1, -2], [1, -2], [-1, 2.4], [1, 2.4]].forEach(([a, b]) => { const w = new THREE.Mesh(new THREE.CylinderGeometry(.45, .45, .3, 16), M.dark.clone()); w.rotation.z = Math.PI / 2; w.position.set(a, .45, b); g.add(w); });
      g.position.set(x, 0, z); g.rotation.y = rot; return g;
    },
    // 加油站雨遮＋加油機
    canopy(x, z, w = 8, d = 6, h = 5) {
      const g = group(span(x - w / 2, h, z - d / 2, x + w / 2, h + .5, z + d / 2, M.roof));
      [[-1, -1], [1, -1], [-1, 1], [1, 1]].forEach(([a, b]) => g.add(pipe([x + a * (w / 2 - .5), 0, z + b * (d / 2 - .5)], [x + a * (w / 2 - .5), h, z + b * (d / 2 - .5)], .15, M.steel)));
      return g;
    },
    dispenser(x, z) { const g = group(span(x - .4, 0, z - .3, x + .4, 1.6, z + .3, M.red)); const p = plate('加油機', .7, .2, { bg: '#ffffff', fg: '#991b1b' }); p.position.set(x, 1.2, z + .31); g.add(p); return g; },
    // 火焰
    fire(x, y, z, s = 1) { const c = new THREE.Mesh(new THREE.ConeGeometry(.45 * s, 1.3 * s, 16), M.fire.clone()); c.position.set(x, y + .65 * s, z); return pulse(c, 3); },
    // 字牌（平放於場景）
    board(text, x, y, z, w = 3, h = .7, o = {}) { const p = plate(text, w, h, o); p.position.set(x, y, z); return p; },
    // 幫浦
    pump(x, z) { const g = group(span(x - .6, 0, z - .4, x + .6, .3, z + .4, M.conc)); const b = new THREE.Mesh(new THREE.CylinderGeometry(.3, .3, .7, 16), M.red.clone()); b.rotation.z = Math.PI / 2; b.position.set(x - .1, .65, z); g.add(b); g.add(span(x + .3, .3, z - .25, x + .6, .9, z + .25, mat('#334155'))); return g; },
    // 氣體鋼瓶列（CO2／鹵化烴／乾粉）
    cyls(x, z, n = 4, m = M.cyl, h = 1.5) { const g = group(); for (let i = 0; i < n; i++) { const c = new THREE.Mesh(new THREE.CylinderGeometry(.2, .2, h, 16), m.clone()); c.position.set(x + i * .5, h / 2, z); g.add(c); } return g; },
    flow, pulse, pipe, span, group, plate, mat,
  };
  return H;
}
