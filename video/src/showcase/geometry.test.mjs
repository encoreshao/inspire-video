import test from 'node:test';
import assert from 'node:assert/strict';
import {
  calloutPosition, camera, clamp, deviceFor, easeInOut, focusRect, imageRect, ringOpacity, zoomFor,
} from './geometry.mjs';

const near = (a, b, eps = 1e-6) => assert.ok(Math.abs(a - b) <= eps, `${a} vs ${b}`);
const FULL = {x: 0, y: 0, w: 1, h: 1};

test('easing is clamped and hits both ends', () => {
  assert.equal(easeInOut(-1), 0);
  assert.equal(easeInOut(0), 0);
  near(easeInOut(0.5), 0.5);
  assert.equal(easeInOut(1), 1);
  assert.equal(easeInOut(5), 1);
});

test('zoomFor: a whole-image focus does not zoom, a tiny one is capped', () => {
  assert.equal(zoomFor(FULL), 1);
  assert.equal(zoomFor({x: 0.4, y: 0.4, w: 0.01, h: 0.01}), 2.2);
  const z = zoomFor({x: 0.2, y: 0.2, w: 0.5, h: 0.4});
  assert.ok(z > 1 && z < 2.2);
});

test('imageRect never leaves empty space, for any focus and shape', () => {
  const screens = [[846, 450], [220, 444]];
  const images = [[1440, 900], [390, 844], [1000, 1000], [3000, 400], [400, 3000], [320, 320]];
  const focuses = [FULL, {x: 0, y: 0, w: 0.1, h: 0.1}, {x: 0.9, y: 0.9, w: 0.1, h: 0.1}, {x: 0.45, y: 0.45, w: 0.1, h: 0.1}];
  for (const [w, h] of screens) for (const [iw, ih] of images) for (const focus of focuses) {
    for (const zoom of [1, 1.5, 2.2]) {
      const r = imageRect({iw, ih, w, h, focus, zoom});
      assert.ok(r.left <= 1e-9 && r.left + r.width >= w - 1e-6, `x gap ${w}x${h} img ${iw}x${ih}`);
      assert.ok(r.top <= 1e-9 && r.top + r.height >= h - 1e-6, `y gap ${w}x${h} img ${iw}x${ih}`);
      near(r.width / r.height, iw / ih, 1e-6);                   // never stretched
    }
  }
});

test('a centred focus ends up in the middle of the screen', () => {
  const focus = {x: 0.4, y: 0.4, w: 0.2, h: 0.2};
  const r = imageRect({iw: 1440, ih: 900, w: 846, h: 450, focus, zoom: 2});
  const f = focusRect(r, focus);
  near(f.left + f.width / 2, 423, 1e-6);
  near(f.top + f.height / 2, 225, 1e-6);
});

test('camera starts unzoomed and reaches the focus zoom at 80% of the beat', () => {
  const focus = {x: 0.3, y: 0.3, w: 0.3, h: 0.3};
  const a = camera({iw: 1440, ih: 900, w: 846, h: 450, focus, progress: 0});
  const b = camera({iw: 1440, ih: 900, w: 846, h: 450, focus, progress: 0.8});
  const c = camera({iw: 1440, ih: 900, w: 846, h: 450, focus, progress: 1});
  near(a.width, imageRect({iw: 1440, ih: 900, w: 846, h: 450, focus, zoom: 1}).width);
  near(b.width / a.width, zoomFor(focus));
  near(c.width, b.width);
});

test('the ring fades in after 0.6 s and out before the end of the beat', () => {
  assert.equal(ringOpacity(0, 6), 0);
  assert.equal(ringOpacity(0.6, 6), 0);
  assert.equal(ringOpacity(3, 6), 1);
  assert.equal(ringOpacity(6, 6), 0);
  const mid = ringOpacity(0.8, 6);
  assert.ok(mid > 0 && mid < 1);
});

test('the callout sits above the ring when it fits, below otherwise, always inside the screen', () => {
  const w = 846, h = 450, cw = 300, ch = 42;
  const high = calloutPosition({left: 100, top: 200, width: 200, height: 100}, cw, ch, w, h);
  assert.ok(high.top < 200 && high.top >= 0);
  const low = calloutPosition({left: 100, top: 10, width: 200, height: 100}, cw, ch, w, h);
  assert.ok(low.top >= 110);
  for (const ring of [{left: 0, top: 0, width: 20, height: 20}, {left: 800, top: 430, width: 40, height: 20}]) {
    const p = calloutPosition(ring, cw, ch, w, h);
    assert.ok(p.left >= 0 && p.left + cw <= w && p.top >= 0 && p.top + ch <= h, JSON.stringify(p));
  }
});

test('deviceFor: tall screenshots get a phone, everything else a browser', () => {
  assert.equal(deviceFor(390, 844), 'phone');
  assert.equal(deviceFor(1440, 900), 'browser');
  assert.equal(deviceFor(1000, 1000), 'browser');
  assert.equal(deviceFor(3000, 400), 'browser');
  assert.equal(deviceFor(1000, 1300), 'phone');
});

test('clamp', () => {
  assert.equal(clamp(5, 0, 1), 1);
  assert.equal(clamp(-5, 0, 1), 0);
  assert.equal(clamp(0.5, 0, 1), 0.5);
});
