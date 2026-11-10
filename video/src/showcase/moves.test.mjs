import test from 'node:test';
import assert from 'node:assert/strict';
import {PROMO_STAGE_H, STAGE_W, clampCenter, maxZoom, minZoom, promoCamera} from './promo.mjs';
import {SHOTS} from './shots.mjs';

const stage = {w: STAGE_W, h: PROMO_STAGE_H};
const tall = {w: 1440, h: 6000};
const pages = [{w: 1440, h: 1500}, tall, {w: 1440, h: 500}];
const targets = [{x: 100, y: 100, w: 600, h: 80}, {x: 200, y: 3000, w: 500, h: 300}, {x: 0, y: 0, w: 1440, h: 6000}, {x: 700, y: 5900, w: 60, h: 40}];
const NEW = ['pull-back-isolate', 'crane-rise', 'cursor-tour', 'scroll-brake'];
const cam = (id, page, target, progress, seconds = 8) => promoCamera({shot: SHOTS[id], target, page, stage, scale: 2, progress, seconds});
const fits = (page, t) => t.x >= 0 && t.y >= 0 && t.x + t.w <= page.w && t.y + t.h <= page.h;

for (const id of NEW) {
  test(`${id}: a finite camera that stays on the page and under the zoom cap, still at the end`, () => {
    for (const page of pages) for (const t of targets) {
      if (!fits(page, t)) continue;
      const z0 = minZoom(page, stage), cap = maxZoom(page, stage, 2);
      let prev = null;
      for (let i = 0; i <= 300; i++) {
        const c = cam(id, page, t, i / 300);
        for (const v of [c.zoom, c.cx, c.cy, c.dim]) assert.ok(Number.isFinite(v), `${id} ${i}`);
        assert.ok(c.zoom >= z0 - 1e-6 && c.zoom <= cap + 1e-6, `${id} zoom ${c.zoom} outside ${z0}..${cap} at ${i}`);
        const cc = clampCenter(page, stage, c.zoom, {cx: c.cx, cy: c.cy});
        assert.ok(Math.abs(cc.cx - c.cx) < 1e-6 && Math.abs(cc.cy - c.cy) < 1e-6, `${id} centre off the page at ${i}`);
        assert.ok(c.dim >= 0 && c.dim <= 1);
        if (prev) assert.ok(Math.abs(Math.log(c.zoom / prev.zoom)) < 0.08, `${id} zoom jumps at ${i}`);
        prev = c;
      }
      const a = cam(id, page, t, 0.97), b = cam(id, page, t, 1);
      assert.ok(Math.abs(a.zoom - b.zoom) < 1e-3 && Math.abs(a.cx - b.cx) < 0.5 && Math.abs(a.cy - b.cy) < 0.5, `${id} not still at the end`);
    }
  });

  test(`${id}: is registered as a camera shot with its metadata`, () => {
    const s = SHOTS[id];
    assert.ok(s && s.needsTarget && typeof s.camera === 'function' && s.minSeconds >= 5);
  });
}

test('pull-back-isolate starts tight, ends wide, and the surroundings go dark', () => {
  const t = targets[0], page = pages[0];
  const first = cam('pull-back-isolate', page, t, 0), last = cam('pull-back-isolate', page, t, 1);
  assert.ok(first.zoom > last.zoom * 1.3);
  assert.equal(last.zoom, minZoom(page, stage));
  assert.ok(first.dim < 0.05 && last.dim > 0.7);
});

test('crane-rise starts tight on the target, ends on the whole page, and the dim lifts', () => {
  const t = targets[0], page = pages[0];
  const first = cam('crane-rise', page, t, 0), mid = cam('crane-rise', page, t, 0.1), last = cam('crane-rise', page, t, 1);
  assert.ok(first.zoom > last.zoom * 1.3 && last.zoom === minZoom(page, stage));
  assert.ok(first.dim < 0.05 && mid.dim > 0.3 && last.dim < 0.02);
});

test('cursor-tour: the cursor arrives on the target before the click, presses, and a ripple follows', () => {
  const t = targets[0], page = pages[0];
  const centre = {x: t.x + t.w / 2, y: t.y + t.h / 2};
  const early = cam('cursor-tour', page, t, 0.05), clickP = cam('cursor-tour', page, t, 0.52), late = cam('cursor-tour', page, t, 0.9);
  assert.ok(early.cursor && early.cursor.ripple === null);
  assert.ok(Math.hypot(clickP.cursor.x - centre.x, clickP.cursor.y - centre.y) < 12);
  assert.ok(clickP.cursor.press > 0 && clickP.cursor.ripple !== null);
  assert.ok(late.cursor.ripple === null && late.cursor.press === 0);
  for (let i = 0; i <= 100; i++) {
    const c = cam('cursor-tour', page, t, i / 100).cursor;
    assert.ok(c.x >= 0 && c.x <= page.w && c.y >= 0 && c.y <= page.h && c.press >= 0 && c.press <= 1);
  }
});

test('scroll-brake brakes: fast at first, nearly stopped at the end, and the reticle locks on', () => {
  const t = targets[1], page = tall;
  const y = (p) => cam('scroll-brake', page, t, p).cy;
  const early = y(0.1) - y(0.05), late = y(0.7) - y(0.65);
  assert.ok(early > late * 3, `${early} vs ${late}`);
  assert.ok(cam('scroll-brake', page, t, 0).reticle === 0 && cam('scroll-brake', page, t, 1).reticle === 1);
  assert.equal(SHOTS['scroll-brake'].needsTallPage, true);
});
