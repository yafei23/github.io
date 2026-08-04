#!/usr/bin/env node
/*
 * build-globe-data.mjs — 为 globe.html 生成内联地图数据
 *
 * 抓取 Natural Earth 110m 数据，做 Douglas–Peucker 简化、量化到整数栅格、
 * 逐点 delta + zigzag varint + base64 编码，输出可以直接粘进 globe.html 的
 * 字符串常量。
 *
 * 运行时不需要这个脚本 —— globe.html 是自包含的。这里只是保证数据可复现。
 *
 *   node tools/build-globe-data.mjs            # 打印数据块到 stdout
 *   node tools/build-globe-data.mjs --write    # 直接写回 globe.html 的数据区
 */

import { execFileSync } from 'node:child_process';
import { mkdirSync, existsSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const CACHE = join(ROOT, '.cache');

/* 注意：jsdelivr 在部分网络环境下被拦截，这里固定用 raw.githubusercontent.com */
const BASE = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson';

/* 海岸线用于绘制，国界只用于「当前正对哪里」的查询，可以简化得更狠 */
const LAND_TOLERANCE = 0.07;   // 度
const CTRY_TOLERANCE = 0.30;   // 度
const LAND_GRID = 64;          // 1/64 度量化
const CTRY_GRID = 32;
const LAND_MIN_SPAN = 0.16;    // 丢掉比这更小的碎岛（度）
const CTRY_MIN_SPAN = 0.30;

/* ─────────────────────────── 抓取 ─────────────────────────── */

function fetchJSON(name) {
  mkdirSync(CACHE, { recursive: true });
  const path = join(CACHE, `${name}.geojson`);
  if (!existsSync(path)) {
    // 走 curl 而不是 global fetch：curl 会遵守环境里的代理设置
    process.stderr.write(`  下载 ${name} …\n`);
    execFileSync('curl', ['-sSfL', '--max-time', '120', '-o', path, `${BASE}/${name}.geojson`], {
      stdio: ['ignore', 'ignore', 'inherit'],
    });
  }
  return JSON.parse(readFileSync(path, 'utf8'));
}

/* ─────────────────────── 几何：简化与度量 ─────────────────────── */

/** 点到线段距离的平方（经纬度平面近似，够用了） */
function segDist2(p, a, b) {
  let x = a[0], y = a[1];
  const dx = b[0] - x, dy = b[1] - y;
  if (dx || dy) {
    const t = ((p[0] - x) * dx + (p[1] - y) * dy) / (dx * dx + dy * dy);
    if (t > 1) { x = b[0]; y = b[1]; }
    else if (t > 0) { x += dx * t; y += dy * t; }
  }
  const ex = p[0] - x, ey = p[1] - y;
  return ex * ex + ey * ey;
}

/** Douglas–Peucker，迭代实现，避免深递归爆栈 */
function simplify(points, tolerance) {
  const n = points.length;
  if (n <= 3) return points.slice();
  const tol2 = tolerance * tolerance;
  const keep = new Uint8Array(n);
  keep[0] = keep[n - 1] = 1;
  const stack = [[0, n - 1]];
  while (stack.length) {
    const [lo, hi] = stack.pop();
    let maxD = 0, idx = -1;
    for (let i = lo + 1; i < hi; i++) {
      const d = segDist2(points[i], points[lo], points[hi]);
      if (d > maxD) { maxD = d; idx = i; }
    }
    if (idx >= 0 && maxD > tol2) {
      keep[idx] = 1;
      stack.push([lo, idx], [idx, hi]);
    }
  }
  const out = [];
  for (let i = 0; i < n; i++) if (keep[i]) out.push(points[i]);
  return out;
}

function ringSpan(ring) {
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const [x, y] of ring) {
    if (x < x0) x0 = x; if (x > x1) x1 = x;
    if (y < y0) y0 = y; if (y > y1) y1 = y;
  }
  return Math.max(x1 - x0, y1 - y0);
}

function ringArea(ring) {
  let a = 0;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    a += (ring[j][0] - ring[i][0]) * (ring[j][1] + ring[i][1]);
  }
  return Math.abs(a / 2);
}

/** 把 Polygon / MultiPolygon 摊平成环的数组 */
function ringsOf(geom) {
  if (!geom) return [];
  const polys = geom.type === 'MultiPolygon' ? geom.coordinates
    : geom.type === 'Polygon' ? [geom.coordinates] : [];
  const out = [];
  for (const poly of polys) for (const ring of poly) out.push(ring);
  return out;
}

/** 简化一组环：闭合点去重 → DP → 丢弃退化/过小的环 */
function prepRings(rings, tolerance, minSpan) {
  const out = [];
  for (let ring of rings) {
    // GeoJSON 的环首尾重复，去掉尾点，渲染/判定时再闭合
    if (ring.length > 1) {
      const a = ring[0], b = ring[ring.length - 1];
      if (a[0] === b[0] && a[1] === b[1]) ring = ring.slice(0, -1);
    }
    if (ring.length < 3) continue;
    if (ringSpan(ring) < minSpan) continue;
    const s = simplify(ring, tolerance);
    if (s.length < 3) continue;
    out.push(s);
  }
  return out;
}

/* ─────────────────────────── 编码 ─────────────────────────── */

class Writer {
  constructor() { this.bytes = []; }
  /** 无符号 varint */
  u(v) {
    v = v >>> 0;
    while (v >= 0x80) { this.bytes.push((v & 0x7f) | 0x80); v >>>= 7; }
    this.bytes.push(v);
  }
  /** zigzag 有符号 varint */
  s(v) { this.u((v << 1) ^ (v >> 31)); }
  base64() { return Buffer.from(Uint8Array.from(this.bytes)).toString('base64'); }
}

/**
 * 环集合 → base64。
 * 布局：环数 | 每环: [国家索引?] 点数, 首点绝对量化坐标(zigzag), 之后逐点 delta(zigzag)
 */
function encodeRings(rings, grid, withOwner) {
  const w = new Writer();
  w.u(rings.length);
  for (const item of rings) {
    const ring = withOwner ? item.ring : item;
    if (withOwner) w.u(item.owner);
    w.u(ring.length);
    let px = 0, py = 0;
    for (let i = 0; i < ring.length; i++) {
      const qx = Math.round(ring[i][0] * grid);
      const qy = Math.round(ring[i][1] * grid);
      w.s(i === 0 ? qx : qx - px);
      w.s(i === 0 ? qy : qy - py);
      px = qx; py = qy;
    }
  }
  return w.base64();
}

/* ─────────────────────────── 主流程 ─────────────────────────── */

process.stderr.write('构建地球仪数据…\n');

/* 海岸线：按面积降序排列，这样渲染端「只画前 N 环」天然就是一档 LOD */
const landGeo = fetchJSON('ne_110m_land');
let landRings = [];
for (const f of landGeo.features) landRings.push(...ringsOf(f.geometry));
landRings = prepRings(landRings, LAND_TOLERANCE, LAND_MIN_SPAN);
landRings.sort((a, b) => ringArea(b) - ringArea(a));
const LAND = encodeRings(landRings, LAND_GRID, false);
const landPts = landRings.reduce((n, r) => n + r.length, 0);

/* 国界：只做点在多边形内的查询，不绘制 */
const ctryGeo = fetchJSON('ne_110m_admin_0_countries');
const names = [];
const conts = [];
const ctryRings = [];
const CONTINENT_ZH = {
  Asia: '亚洲', Europe: '欧洲', Africa: '非洲', Oceania: '大洋洲',
  'North America': '北美洲', 'South America': '南美洲',
  Antarctica: '南极洲', 'Seven seas (open ocean)': '海域',
};

/* Natural Earth 的 NAME_ZH 用的是正式国名，地球仪上显示得用日常叫法 */
const SHORT_ZH = {
  中华人民共和国: '中国',
  中华民国: '台湾',
  朝鲜民主主义人民共和国: '朝鲜',
  大韩民国: '韩国',
  阿拉伯联合酋长国: '阿联酋',
  刚果民主共和国: '刚果(金)',
  刚果共和国: '刚果(布)',
  中非共和国: '中非',
  波斯尼亚和黑塞哥维那: '波黑',
  特立尼达和多巴哥: '特立尼达',
  北塞浦路斯土耳其共和国: '北塞浦路斯',
  法属南部和南极领地: '法属南部领地',
};

for (const f of ctryGeo.features) {
  const p = f.properties || {};
  const raw = p.NAME_ZH || p.NAME || '未知';
  const zh = SHORT_ZH[raw] || raw;
  const rings = prepRings(ringsOf(f.geometry), CTRY_TOLERANCE, CTRY_MIN_SPAN);
  if (!rings.length) continue;
  const owner = names.length;
  names.push(zh);
  conts.push(CONTINENT_ZH[p.CONTINENT] || p.CONTINENT || '');
  for (const ring of rings) ctryRings.push({ owner, ring });
}
const CTRY = encodeRings(ctryRings, CTRY_GRID, true);
const ctryPts = ctryRings.reduce((n, r) => n + r.ring.length, 0);

/* ─────────────────────────── 报告与输出 ─────────────────────────── */

const kb = (s) => (s.length / 1024).toFixed(1) + ' KB';
process.stderr.write(
  `\n  海岸线  ${String(landRings.length).padStart(4)} 环 ${String(landPts).padStart(6)} 点  →  ${kb(LAND)}\n` +
  `  国界    ${String(ctryRings.length).padStart(4)} 环 ${String(ctryPts).padStart(6)} 点  →  ${kb(CTRY)}   ${names.length} 国\n` +
  `  合计 ${kb(LAND + CTRY)}\n\n`
);

const block =
  `/* 海岸线 · Natural Earth 110m · ${landRings.length} 环 / ${landPts} 点 · 按面积降序 */\n` +
  `const LAND_D = ${JSON.stringify(LAND)};\n` +
  `/* 国界（仅用于位置查询，不绘制） · ${ctryRings.length} 环 / ${ctryPts} 点 */\n` +
  `const CTRY_D = ${JSON.stringify(CTRY)};\n` +
  `const CTRY_NAME = ${JSON.stringify(names)};\n` +
  `const CTRY_CONT = ${JSON.stringify(conts)};\n`;

if (process.argv.includes('--write')) {
  const target = join(ROOT, 'globe.html');
  const src = readFileSync(target, 'utf8');
  const START = '/* ===== GEO-DATA:BEGIN (由 tools/build-globe-data.mjs 生成，勿手改) ===== */';
  const END = '/* ===== GEO-DATA:END ===== */';
  const i = src.indexOf(START), j = src.indexOf(END);
  if (i < 0 || j < 0) {
    process.stderr.write('globe.html 里找不到 GEO-DATA 标记，已放弃写入。\n');
    process.exit(1);
  }
  writeFileSync(target, src.slice(0, i + START.length) + '\n' + block + src.slice(j));
  process.stderr.write(`已写入 ${target}\n`);
} else {
  process.stdout.write(block);
}
