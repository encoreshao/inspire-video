// The newer promo shots, each a pure camera function of {target, page, stage, scale, progress, seconds} like those in
// shots.mjs. Techniques are written from scratch after reading the named video-shotcraft cards (Apache-2.0); no demo
// code, copy, colours or UI are reused. Each shot's comment says what was borrowed and what was left out.
import {clamp, easeInOut} from './geometry.mjs';
import {fitZoom, lerp, maxZoom, minZoom, targetCenter, viewSize} from './promo.mjs';
import {moveCenter, pan, push} from './kit.mjs';

const ease01 = (t) => easeInOut(clamp(t, 0, 1));
const outQuart = (t) => 1 - Math.pow(1 - clamp(t, 0, 1), 4);
const outCubic = (t) => 1 - Math.pow(1 - clamp(t, 0, 1), 3);

// The tight framing (the target fills about 75% of the stage's limiting side) and the page-width framing it travels to.
function framings({target, page, stage, scale}) {
  const z0 = minZoom(page, stage);
  const cap = maxZoom(page, stage, scale);
  return {z0, zT: clamp(fitZoom(page, stage, target, 0.75), z0, cap)};
}

// The view centre at `zoom` on the way between the two framings: one progress for the zoom and the centre, so it is one
// camera making one move.
function centreAt(a, zoom, z0, zT) {
  const t = zT > z0 * 1.0001 ? clamp(Math.log(zoom / z0) / Math.log(zT / z0), 0, 1) : 0;
  return moveCenter({target: a.target, page: a.page, stage: a.stage, zoom, z0, t});
}

// Card studied: tension-camera-moves, move B (pull-back-isolation). Borrowed: a pull back from a close-up while the
// surroundings go dark from the nearest outwards, ending still with one element alone in the dark. Not borrowed: the
// glow, the sibling-card grid, the blur and the sinking of each card (the page is one flat picture), and the card's
// closing sentence in screen space.
const ISO = Object.freeze({hold: 0.12, end: 0.78, dim: 0.82});
function isolate(a) {
  const {z0, zT} = framings(a);
  const q = ease01((clamp(a.progress, 0, 1) - ISO.hold) / (ISO.end - ISO.hold));
  const zoom = zT * Math.pow(z0 / zT, q);
  return {zoom, ...centreAt(a, zoom, z0, zT), dim: ISO.dim * ease01((q - 0.15) / 0.6)};
}

// Card studied: crane-rise-reveal. Borrowed: the opposite move to a push, from the detail to the whole: a close-up that
// holds for a breath, then one decelerating rise (the zoom and the centre share one progress) to the page-width
// framing, with everything but the target held down while it is close and lifting as the page fills the frame. Not
// borrowed: the row-by-row light wash, the counting numbers and the status flip (they need a live interface).
const CRANE = Object.freeze({hold: 0.14, end: 0.8, dim: 0.62});
function crane(a) {
  const {z0, zT} = framings(a);
  const p = clamp(a.progress, 0, 1);
  const q = outCubic((p - CRANE.hold) / (CRANE.end - CRANE.hold));
  const zoom = zT * Math.pow(z0 / zT, q);
  const dim = CRANE.dim * ease01(p / 0.08) * (1 - ease01((q - 0.1) / 0.5));       // not dark on the first frame
  return {zoom, ...centreAt(a, zoom, z0, zT), dim};
}

// Card studied: cursor-flyover. Borrowed: the cursor is the hand and the camera the eye: the cursor goes first, on a
// light arc, aims, then clicks (a 16% press and a ring that grows and fades), and the camera arrives behind it. Not
// borrowed: the four-station tour, the interface that answers each click, the motion blur and the 40 px screen-space
// size is kept but its path is one hop to the beat's target. The cursor position is in page px (the stage places it).
const TOUR = Object.freeze({go: [0.1, 0.45], press: [0.5, 0.56], ripple: [0.5, 0.7]});
function tour(a) {
  const {z0} = framings(a);
  const fit = fitZoom(a.page, a.stage, a.target);
  const medium = fit > z0 ? z0 * Math.pow(fit / z0, 0.55) : z0;
  const cam = push(a, medium);
  const p = clamp(a.progress, 0, 1);
  const c = targetCenter(a.target);
  const v = viewSize(a.page, a.stage, medium);
  const from = {x: clamp(c.cx - 0.36 * v.w, 0, a.page.w), y: clamp(c.cy + 0.3 * v.h, 0, a.page.h)};
  const e = ease01((p - TOUR.go[0]) / (TOUR.go[1] - TOUR.go[0]));
  const dx = c.cx - from.x, dy = c.cy - from.y, len = Math.hypot(dx, dy) || 1;
  const arc = Math.sin(Math.PI * e) * 0.06 * len;                       // a light arc, zero at both ends
  const x = clamp(lerp(from.x, c.cx, e) + (-dy / len) * arc, 0, a.page.w);
  const y = clamp(lerp(from.y, c.cy, e) + (dx / len) * arc, 0, a.page.h);
  const press = p >= TOUR.press[0] && p <= TOUR.press[1] ? Math.sin(Math.PI * (p - TOUR.press[0]) / (TOUR.press[1] - TOUR.press[0])) : 0;
  const ripple = p >= TOUR.ripple[0] && p <= TOUR.ripple[1] ? (p - TOUR.ripple[0]) / (TOUR.ripple[1] - TOUR.ripple[0]) : null;
  return {...cam, dim: 0, cursor: {x, y, press, ripple}};
}

// Card studied: scroll-brake-moves. Borrowed: a travel down the page that starts fast and brakes onto the target (the
// slope shrinks to almost nothing at the end) and a reticle that locks on as it stops. Not borrowed: the changelog
// content, the reticle's scan and the screen shake. Like pan-reveal it needs a tall page.
const BRAKE = Object.freeze({end: 0.72, lock: [0.6, 0.74]});
function brake(a) {
  const cam = pan(a, {ease: outQuart, end: BRAKE.end});
  return {...cam, dim: 0, reticle: ease01((clamp(a.progress, 0, 1) - BRAKE.lock[0]) / (BRAKE.lock[1] - BRAKE.lock[0]))};
}

export const MOVES = Object.freeze({isolate, crane, tour, brake});
