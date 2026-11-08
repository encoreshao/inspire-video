import test from 'node:test';
import assert from 'node:assert/strict';
import {
  STAGE_W, baseScale, clampCenter, fitZoom, maxZoom, minZoom, placeImage, promoCamera, stageHeight, stageRect, viewSize,
} from './promo.mjs';
import {SHOTS, shotMeta} from './shots.mjs';

const near = (a, b, eps = 1e-6) => assert.ok(Math.abs(a - b) <= eps, `${a} vs ${b}`);
const EPS = 1e-6;
const stage = {w: STAGE_W, h: 560};
const tall = {w: 1440, h: 6000};
const short = {w: 1440, h: 500};
const IDS = Object.keys(SHOTS);
const STEPS = Array.from({length: 61}, (_, i) => i / 60);
const TARGETS = {
  interior: {x: 520, y: 1000, w: 400, h: 120},
  leftEdge: {x: 0, y: 100, w: 300, h: 80},
  bottom: {x: 600, y: 5880, w: 300, h: 120},
  wide: {x: 0, y: 0, w: 1440, h: 400},
  tiny: {x: 700, y: 900, w: 20, h: 10},
  nearRight: {x: 900, y: 3000, w: 480, h: 60},   // the review's case: the target slid out of frame mid-push
};
const CASES = [...Object.values(TARGETS).map((t) => [tall, t]), [short, {x: 520, y: 100, w: 400, h: 120}]];
const run = (id, target, progress, page = tall, scale = 2) =>
  promoCamera({shot: SHOTS[id], target, page, stage, scale, progress});

test('the registry is frozen and every shot has its metadata', () => {
  assert.ok(Object.isFrozen(SHOTS));
  for (const s of Object.values(SHOTS)) {
    assert.ok(Object.isFrozen(s));
    assert.equal(typeof s.camera, 'function');
    assert.ok(s.minSeconds > 0 && s.settle > 0);
  }
  assert.deepEqual(shotMeta(), {
    'hero-push': {minSeconds: 4, maxPerVideo: null, needsTallPage: false},
    'spotlight-focus': {minSeconds: 4, maxPerVideo: null, needsTallPage: false},
  });
});

test('the view never leaves the page, for every shot, target and page shape', () => {
  for (const id of IDS) for (const [page, target] of CASES) for (const p of STEPS) {
    const cam = run(id, target, p, page);
    const v = viewSize(page, stage, cam.zoom);
    assert.ok(cam.cx - v.w / 2 >= -EPS && cam.cx + v.w / 2 <= page.w + EPS, `${id} x at ${p}`);
    assert.ok(cam.cy - v.h / 2 >= -EPS && cam.cy + v.h / 2 <= page.h + EPS, `${id} y at ${p}`);
  }
});

test('zoom never decreases during a beat', () => {
  for (const id of IDS) for (const [page, target] of CASES) {
    let last = 0;
    for (const p of STEPS) {
      const z = run(id, target, p, page).zoom;
      assert.ok(z >= last - EPS, `${id} at ${p}`);
      last = z;
    }
  }
});

test('every shot starts at the page-width framing', () => {
  for (const id of IDS) for (const [page, target] of CASES) near(run(id, target, 0, page).zoom, minZoom(page, stage));
});

test('the last 10% of a beat is a true still', () => {
  for (const id of IDS) for (const [page, target] of CASES) {
    const at90 = run(id, target, 0.9, page);
    for (const p of [0.9, 0.93, 0.97, 1]) assert.deepEqual(run(id, target, p, page), at90, `${id} at ${p}`);
  }
});

test('the final framing keeps an interior target 8% clear of every side, and never crops an edge target', () => {
  for (const id of IDS) {
    const place = placeImage(tall, stage, run(id, TARGETS.interior, 1));
    const r = stageRect(TARGETS.interior, place);
    assert.ok(r.left >= 0.08 * stage.w - EPS && stage.w - (r.left + r.width) >= 0.08 * stage.w - EPS, `${id} sides`);
    assert.ok(r.top >= 0.08 * stage.h - EPS && stage.h - (r.top + r.height) >= 0.08 * stage.h - EPS, `${id} top and bottom`);
    for (const t of [TARGETS.leftEdge, TARGETS.bottom]) {
      const e = stageRect(t, placeImage(tall, stage, run(id, t, 1)));
      assert.ok(e.left >= -EPS && e.left + e.width <= stage.w + EPS && e.top >= -EPS && e.top + e.height <= stage.h + EPS, `${id} edge`);
    }
  }
});

test('the target stays in view for the whole beat whenever it fits the view', () => {
  const inView = (id, page, target, p) => {
    const cam = run(id, target, p, page);
    const v = viewSize(page, stage, cam.zoom);
    if (target.w <= v.w) assert.ok(target.x >= cam.cx - v.w / 2 - EPS && target.x + target.w <= cam.cx + v.w / 2 + EPS, `${id} x at ${p} for ${JSON.stringify(target)}`);
    if (target.h <= v.h) assert.ok(target.y >= cam.cy - v.h / 2 - EPS && target.y + target.h <= cam.cy + v.h / 2 + EPS, `${id} y at ${p} for ${JSON.stringify(target)}`);
  };
  for (const id of IDS) for (const [page, target] of CASES) for (const p of STEPS) inView(id, page, target, p);
  for (const id of IDS) for (const x of [0, 300, 600, 900, 1100]) for (const y of [0, 1500, 3000, 5800]) for (const [w, h] of [[100, 60], [340, 200], [480, 60]]) {
    if (x + w > tall.w || y + h > tall.h) continue;
    for (const p of STEPS) inView(id, tall, {x, y, w, h}, p);
  }
});

test('zoom stays within the sharpness of the capture, even for a tiny target', () => {
  for (const scale of [1, 2]) for (const id of IDS) for (const p of STEPS) {
    const z = run(id, TARGETS.tiny, p, tall, scale).zoom;
    assert.ok((z * baseScale(tall, stage)) / scale <= 1 + EPS, `${id} scale ${scale} at ${p}`);
    assert.ok(z <= 3.2 + EPS);
  }
});

test('a page shorter than the stage view gets a minimum zoom so no empty space shows', () => {
  assert.ok(minZoom(short, stage) > 1);
  assert.equal(minZoom(tall, stage), 1);
  const v = viewSize(short, stage, minZoom(short, stage));
  assert.ok(v.h <= short.h + EPS);
});

test('a target wider than the fit does not push or drift', () => {
  for (const id of IDS) for (const p of STEPS) near(run(id, TARGETS.wide, p).zoom, minZoom(tall, stage));
});

test('the camera is a pure function', () => {
  for (const id of IDS) assert.deepEqual(run(id, TARGETS.interior, 0.37), run(id, TARGETS.interior, 0.37));
});

test('spotlight dims the surround gradually and never beyond 0.55; hero-push never dims', () => {
  let last = 0;
  for (const p of STEPS) {
    const d = run('spotlight-focus', TARGETS.interior, p).dim;
    assert.ok(d >= last - EPS && d <= 0.55 + EPS);
    last = d;
  }
  assert.equal(run('spotlight-focus', TARGETS.interior, 0.1).dim, 0);
  near(run('spotlight-focus', TARGETS.interior, 0.6).dim, 0.55);
  for (const p of STEPS) assert.equal(run('hero-push', TARGETS.interior, p).dim, 0);
});

test('placeImage and stageRect put an interior target at the stage centre when the push ends', () => {
  const place = placeImage(tall, stage, run('hero-push', TARGETS.interior, 1));
  const r = stageRect(TARGETS.interior, place);
  near(r.left + r.width / 2, stage.w / 2, 1);
  near(r.top + r.height / 2, stage.h / 2, 1);
  near(place.width / tall.w, place.s, 1e-9);
});

test('the stage grows into the room the caption card leaves, between 488 and 600 px', () => {
  assert.equal(stageHeight(217.76), 580);   // the LoopX caption reserve
  assert.equal(stageHeight(0), 600);
  assert.equal(stageHeight(400), 488);
  // a two-line subtitle takes another 53 px (42 px type at a line height of 1.25) out of the room
  assert.equal(stageHeight(217.76, 2), 527);
  assert.equal(stageHeight(0, 2), 600);
  assert.equal(stageHeight(400, 2), 488);
  assert.equal(stageHeight(217.76, 1), stageHeight(217.76));
});

test('framing helpers: fit, limits and centre clamping', () => {
  near((TARGETS.interior.w * fitZoom(tall, stage, TARGETS.interior)) / tall.w, 0.8, 1e-9);
  assert.equal(maxZoom(tall, stage, 2), 3.2);
  assert.ok(maxZoom(tall, stage, 1) < 1.7);
  const c = clampCenter(tall, stage, 2, {cx: 0, cy: 0});
  near(c.cx, viewSize(tall, stage, 2).w / 2);
  near(c.cy, viewSize(tall, stage, 2).h / 2);
});
