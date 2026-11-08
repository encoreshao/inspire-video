// The promo shots: frozen presets. Each camera is a pure function of {target, page, stage, scale, progress}.
// Techniques are written from scratch after reading the named video-shotcraft cards (Apache-2.0); no demo code is reused.
import {clamp, easeInOut} from './geometry.mjs';
import {clampCenter, fitZoom, lerp, maxZoom, minZoom, targetCenter, viewSize} from './promo.mjs';

const PUSH_END = 0.65;      // the push arrives at 65% of the beat
const DRIFT_END = 0.9;      // then a slow drift to 90%; the last 10% is a true still
const DRIFT = 0.015;        // at most 1.5% more zoom

// Push from the page-width framing (target in context) to `endZoom`, then drift, then rest.
function push({target, page, stage, scale, progress}, endZoom) {
  const z0 = minZoom(page, stage);
  const cap = maxZoom(page, stage, scale);
  const z1 = clamp(endZoom, z0, cap);
  const p = clamp(progress, 0, 1);
  const pushT = easeInOut(p / PUSH_END);
  const driftT = z1 > z0 ? easeInOut((p - PUSH_END) / (DRIFT_END - PUSH_END)) : 0;     // a target too big to push does not drift
  const zoom = Math.min(cap, z0 * Math.pow(z1 / z0, pushT) * (1 + DRIFT * driftT));    // geometric: steady apparent speed
  const c = targetCenter(target);
  const start = clampCenter(page, stage, z0, c);
  const end = clampCenter(page, stage, zoom, c);
  const v = viewSize(page, stage, zoom);
  return {zoom, cx: within(lerp(start.cx, end.cx, pushT), target.x, target.w, v.w, page.w),
    cy: within(lerp(start.cy, end.cy, pushT), target.y, target.h, v.h, page.h)};
}

// Clamp one axis of the view centre to the page, and, when the target fits the view, keep the whole target in view:
// the zoom grows faster than a straight centre move, so without this a target near an edge slides out and back.
function within(c, boxStart, boxSize, viewLen, pageLen) {
  let lo = viewLen / 2;
  let hi = pageLen - viewLen / 2;
  if (boxSize <= viewLen) {
    lo = Math.max(lo, boxStart + boxSize - viewLen / 2);
    hi = Math.min(hi, boxStart + viewLen / 2);
  }
  return clamp(c, lo, Math.max(lo, hi));
}

export const SHOTS = Object.freeze({
  // Card studied: spotlight-hero-card.
  'hero-push': Object.freeze({
    id: 'hero-push', summary: 'Slow push from the page-width framing onto the target, then a hold.',
    minSeconds: 4, maxPerVideo: null, needsTallPage: false, settle: 0.1,
    camera: (a) => ({...push(a, fitZoom(a.page, a.stage, a.target)), dim: 0}),
  }),
  // Card studied: spotlight-hero-card.
  'spotlight-focus': Object.freeze({
    id: 'spotlight-focus', summary: 'A gentler push while everything outside the target dims to 55%.',
    minSeconds: 4, maxPerVideo: null, needsTallPage: false, settle: 0.1,
    camera: (a) => {
      const z0 = minZoom(a.page, a.stage);
      const fit = fitZoom(a.page, a.stage, a.target);
      const medium = fit > z0 ? z0 * Math.pow(fit / z0, 0.6) : z0;                     // 60% of the way in, in log space
      return {...push(a, medium), dim: 0.55 * easeInOut((clamp(a.progress, 0, 1) - 0.2) / 0.25)};
    },
  }),
});

// Plain data for the Python validator (scripts/showcase/manifest.py keeps a copy; a test compares the two).
export const shotMeta = () => Object.fromEntries(Object.values(SHOTS).map((s) =>
  [s.id, {minSeconds: s.minSeconds, maxPerVideo: s.maxPerVideo, needsTallPage: s.needsTallPage}]));
