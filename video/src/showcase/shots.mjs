// The promo shots: frozen presets. Each camera is a pure function of {target, page, stage, scale, progress, seconds}.
// Techniques are written from scratch after reading the named video-shotcraft cards (Apache-2.0); no demo code is reused.
import {clamp, easeInOut} from './geometry.mjs';
import {clampCenter, fitZoom, lerp, maxZoom, minZoom, targetCenter, viewSize} from './promo.mjs';

const PUSH_END = 0.65;      // the push arrives at 65% of the beat
const DRIFT_END = 0.9;      // then a slow drift to 90%; the last 10% is a true still
const DRIFT = 0.015;        // at most 1.5% more zoom

const easeIn = (t) => { const x = clamp(t, 0, 1); return x * x * x; };
const easeOut = (t) => { const x = clamp(t, 0, 1); return 1 - Math.pow(1 - x, 3); };

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

// The view centre at `zoom`: it travels from the target-centred page-width framing (zoom z0) to the target-centred
// framing at `zoom` as `t` goes 0..1, and never loses a target that fits the view.
function moveCenter({target, page, stage, zoom, z0, t}) {
  const c = targetCenter(target);
  const start = clampCenter(page, stage, z0, c);
  const end = clampCenter(page, stage, zoom, c);
  const v = viewSize(page, stage, zoom);
  return {cx: within(lerp(start.cx, end.cx, t), target.x, target.w, v.w, page.w),
    cy: within(lerp(start.cy, end.cy, t), target.y, target.h, v.h, page.h)};
}

// Push from the page-width framing (target in context) to `endZoom`, then drift, then rest.
function push({target, page, stage, scale, progress}, endZoom) {
  const z0 = minZoom(page, stage);
  const cap = maxZoom(page, stage, scale);
  const z1 = clamp(endZoom, z0, cap);
  const p = clamp(progress, 0, 1);
  const pushT = easeInOut(p / PUSH_END);
  const driftT = z1 > z0 ? easeInOut((p - PUSH_END) / (DRIFT_END - PUSH_END)) : 0;     // a target too big to push does not drift
  const zoom = Math.min(cap, z0 * Math.pow(z1 / z0, pushT) * (1 + DRIFT * driftT));    // geometric: steady apparent speed
  return {zoom, ...moveCenter({target, page, stage, zoom, z0, t: pushT})};
}

// The punch: a wide hold with a slow creep, a 6-frame ease-in push that overshoots a little, a 5-frame settle, then still.
// The card's numbers: push 4-8 frames (over 10 it reads as an ordinary push), the target fills 60-75% of the frame,
// the rebound is 3-6%. The card's second variant (a screen shake) is left out on purpose: the camera stays steady.
const CRASH = Object.freeze({pushSeconds: 6 / 30, settleSeconds: 5 / 30, creep: 0.025, overshoot: 0.03, fill: 0.7});

function crash({target, page, stage, scale, progress, seconds}) {
  const z0 = minZoom(page, stage);
  const cap = maxZoom(page, stage, scale);
  const zFinal = clamp(fitZoom(page, stage, target, CRASH.fill), z0, cap / (1 + CRASH.overshoot));
  if (zFinal < z0 * 1.05) return {...moveCenter({target, page, stage, zoom: z0, z0, t: 0}), zoom: z0, dim: 0};   // nothing to punch in on
  const t = clamp(progress, 0, 1) * seconds;
  const tHit = Math.min(Math.max(1, 0.4 * seconds), Math.max(0.5 * seconds, seconds - 2));      // the wide hold, then the punch
  const zA = z0 * (1 + CRASH.creep);
  const zPeak = zFinal * (1 + CRASH.overshoot);
  const q = clamp((t - tHit) / CRASH.pushSeconds, 0, 1);
  const r = clamp((t - tHit - CRASH.pushSeconds) / CRASH.settleSeconds, 0, 1);
  let zoom;
  if (t <= tHit) zoom = z0 * (1 + CRASH.creep * easeInOut(t / tHit));
  else if (r <= 0) zoom = zA * Math.pow(zPeak / zA, easeIn(q));
  else zoom = zPeak * Math.pow(zFinal / zPeak, easeOut(r));
  zoom = Math.min(cap, zoom);
  return {zoom, ...moveCenter({target, page, stage, zoom, z0, t: easeIn(q)}), dim: 0};
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
  // Card studied: crash-zoom-punch.
  'crash-zoom-punch': Object.freeze({
    id: 'crash-zoom-punch', summary: 'A wide hold, then a 6-frame punch onto the target with a small overshoot, then still.',
    minSeconds: 4, maxPerVideo: 1, needsTallPage: false, settle: 0.1,
    camera: (a) => crash(a),
  }),
});

// Plain data for the Python validator (scripts/showcase/manifest.py keeps a copy; a test compares the two).
export const shotMeta = () => Object.fromEntries(Object.values(SHOTS).map((s) =>
  [s.id, {minSeconds: s.minSeconds, maxPerVideo: s.maxPerVideo, needsTallPage: s.needsTallPage}]));
