// Shared camera building blocks for the promo shots (pure functions, no React): the push, the pan and the centre travel.
import {clamp, easeInOut} from './geometry.mjs';
import {clampCenter, fitZoom, lerp, maxZoom, minZoom, targetCenter, viewSize} from './promo.mjs';

export const PUSH_END = 0.65;      // the push arrives at 65% of the beat; the camera is then dead still (no drift: the card forbids it)

export const easeIn = (t) => { const x = clamp(t, 0, 1); return x * x * x; };
export const easeOut = (t) => { const x = clamp(t, 0, 1); return 1 - Math.pow(1 - x, 3); };

// Clamp one axis of the view centre to the page, and, when the target fits the view, keep the whole target in view:
// the zoom grows faster than a straight centre move, so without this a target near an edge slides out and back.
export function within(c, boxStart, boxSize, viewLen, pageLen) {
  const pageLo = viewLen / 2;
  const pageHi = pageLen - viewLen / 2;
  if (boxSize <= viewLen) {
    const lo = Math.max(pageLo, boxStart + boxSize - viewLen / 2);
    const hi = Math.min(pageHi, boxStart + viewLen / 2);
    if (lo <= hi) return clamp(c, lo, hi);
  }
  return clamp(c, pageLo, pageHi);          // the target cannot be held in view (too big, or not on the page): stay on the page
}

// The view centre at `zoom`: it travels from the target-centred page-width framing (zoom z0) to the target-centred
// framing at `zoom` as `t` goes 0..1, and never loses a target that fits the view.
export function moveCenter({target, page, stage, zoom, z0, t}) {
  const c = targetCenter(target);
  const start = clampCenter(page, stage, z0, c);
  const end = clampCenter(page, stage, zoom, c);
  const v = viewSize(page, stage, zoom);
  return {cx: within(lerp(start.cx, end.cx, t), target.x, target.w, v.w, page.w),
    cy: within(lerp(start.cy, end.cy, t), target.y, target.h, v.h, page.h)};
}

// Push from the page-width framing (target in context) to `endZoom`, then rest.
export function push({target, page, stage, scale, progress}, endZoom) {
  const z0 = minZoom(page, stage);
  const cap = maxZoom(page, stage, scale);
  const z1 = clamp(endZoom, z0, cap);
  const p = clamp(progress, 0, 1);
  const pushT = easeInOut(p / PUSH_END);
  const zoom = Math.min(cap, z0 * Math.pow(z1 / z0, pushT));                            // geometric: steady apparent speed
  return {zoom, ...moveCenter({target, page, stage, zoom, z0, t: pushT})};
}

// The reveal: travel down a tall page from its top to the target, easing in and out over 75% of the beat, then rest.
// The view's top edge only moves down; the zoom eases from the page-width framing to a readable level (never deep:
// the point is the journey through the page, not a close-up).
export const PAN_END = 0.75;
export const PAN_MAX_ZOOM = 1.8;

export function pan({target, page, stage, scale, progress}, {ease = easeInOut, end = PAN_END} = {}) {
  const z0 = minZoom(page, stage);
  const cap = maxZoom(page, stage, scale);
  const zPan = clamp(fitZoom(page, stage, target), z0, Math.max(z0, Math.min(cap, PAN_MAX_ZOOM)));   // never below the page-fitting minimum
  const panT = ease(clamp(progress, 0, 1) / end);
  const zoom = z0 * Math.pow(zPan / z0, panT);
  const c = targetCenter(target);
  const endCenter = clampCenter(page, stage, zPan, c);
  const topEnd = endCenter.cy - viewSize(page, stage, zPan).h / 2;          // the view's top edge when the pan arrives (never above the page)
  const cy = lerp(0, topEnd, panT) + viewSize(page, stage, zoom).h / 2;
  const cx = lerp(clampCenter(page, stage, z0, c).cx, endCenter.cx, panT);
  return {zoom, ...clampCenter(page, stage, zoom, {cx, cy})};
}

