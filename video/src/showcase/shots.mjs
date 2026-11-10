// The promo shots: frozen presets. Each camera is a pure function of {target, page, stage, scale, progress, seconds}.
// Techniques are written from scratch after reading the named video-shotcraft cards (Apache-2.0); no demo code is reused.
import {clamp, easeInOut} from './geometry.mjs';
import META from './shots.json' with {type: 'json'};
import {fitZoom, maxZoom, minZoom} from './promo.mjs';
import {easeIn, easeOut, moveCenter, pan, push} from './kit.mjs';
import {MOVES} from './moves.mjs';

// The punch: a wide hold with a slow creep, a 6-frame ease-in push that overshoots a little, a 5-frame settle, then still.
// The card's numbers: push 4-8 frames (over 10 it reads as an ordinary push), the target fills 60-75% of the frame,
// the rebound is 3-6%. Left out on purpose: the card's screen-shake variant, its motion blur, its pre-pull-back (the
// camera never moves backwards) and its second punch per video (the manifest allows one).
const CRASH = Object.freeze({pushSeconds: 6 / 30, settleSeconds: 5 / 30, creep: 0.025, overshoot: 0.03, fill: 0.7});

function crash({target, page, stage, scale, progress, seconds: beatSeconds}) {
  const seconds = beatSeconds > 0 && Number.isFinite(beatSeconds) ? beatSeconds : 10;     // a bad length falls back to the default
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
  // Card studied: spotlight-hero-card (opening). Borrowed: a single hero target, and a hold that is dead still (the card
  // forbids tail drift). Not borrowed: its action arc, dark theatre, light beam, hover and outline light.
  'hero-push': Object.freeze({
    id: 'hero-push', ...META['hero-push'], summary: 'Slow push from the page-width framing onto the target, then a hold.',
    settle: 0.1,
    camera: (a) => ({...push(a, fitZoom(a.page, a.stage, a.target)), dim: 0}),
  }),
  // Card studied: spotlight-hero-card (opening). Borrowed: only the target is lit, by a card-shaped soft hole and not a
  // circle (the card's pitfall), the camera still at the end. Not borrowed: the theatre, beam, hover and outline light.
  'spotlight-focus': Object.freeze({
    id: 'spotlight-focus', ...META['spotlight-focus'], summary: 'A gentler push while everything outside the target dims to 55%.',
    settle: 0.1,
    camera: (a) => {
      const z0 = minZoom(a.page, a.stage);
      const fit = fitZoom(a.page, a.stage, a.target);
      const medium = fit > z0 ? z0 * Math.pow(fit / z0, 0.6) : z0;                     // 60% of the way in, in log space
      return {...push(a, medium), dim: 0.55 * easeInOut((clamp(a.progress, 0, 1) - 0.2) / 0.25)};
    },
  }),
  // Card studied: crash-zoom-punch.
  'crash-zoom-punch': Object.freeze({
    id: 'crash-zoom-punch', ...META['crash-zoom-punch'], summary: 'A wide hold, then a 6-frame punch onto the target with a small overshoot, then still.',
    settle: 0.1,
    camera: (a) => crash(a),
  }),
  // No card: a plain vertical travel, written for pages taller than one screen.
  'pan-reveal': Object.freeze({
    id: 'pan-reveal', ...META['pan-reveal'], summary: 'Travel down a tall page from its top to the target, then rest.',
    settle: 0.25, reveals: true,
    camera: (a) => ({...pan(a), dim: 0}),
  }),
  // Cards studied: tension-camera-moves (B), crane-rise-reveal, cursor-flyover, scroll-brake-moves; see moves.mjs.
  'pull-back-isolate': Object.freeze({
    id: 'pull-back-isolate', ...META['pull-back-isolate'], summary: 'Tight on the target, then a pull back while everything around it goes dark.',
    settle: 0.1, camera: (a) => MOVES.isolate(a),
  }),
  'crane-rise': Object.freeze({
    id: 'crane-rise', ...META['crane-rise'], summary: 'From a close-up of the target, one decelerating rise to the whole page.',
    settle: 0.1, camera: (a) => MOVES.crane(a),
  }),
  'cursor-tour': Object.freeze({
    id: 'cursor-tour', ...META['cursor-tour'], summary: 'A cursor glides to the target and clicks with a ripple; the camera arrives behind it.',
    settle: 0.1, camera: (a) => MOVES.tour(a),
  }),
  'scroll-brake': Object.freeze({
    id: 'scroll-brake', ...META['scroll-brake'], summary: 'A fast travel down a tall page that brakes onto the target, a reticle locking on.',
    settle: 0.25, reveals: true, camera: (a) => MOVES.brake(a),
  }),
  // No card: a plain staggered fade and rise. No capture and no camera: large text on the theme background, for the
  // hook and the call to action.
  'statement': Object.freeze({
    id: 'statement', ...META['statement'], summary: 'The statement text large on the theme background, words arriving 4 frames apart, then a hold.',
    settle: 0, camera: null,
  }),
});

// The statement's entrance, as pure functions of frames so node can test them.
export const STATEMENT_STAGGER = 4;      // frames between one word and the next
export const STATEMENT_ENTER = 8;        // frames each word takes to arrive
export function statementReveal(index, frame) {
  const t = clamp((frame - index * STATEMENT_STAGGER) / STATEMENT_ENTER, 0, 1);
  const e = 1 - Math.pow(1 - t, 3);
  return {opacity: e, dy: (1 - e) * 20};
}
export const statementDoneFrame = (count) => (count - 1) * STATEMENT_STAGGER + STATEMENT_ENTER;
// Type size in px for a statement of `widthUnits` (a Chinese character counts 2): bigger when there is less to say.
export const statementFontSize = (widthUnits) => (widthUnits <= 14 ? 88 : widthUnits <= 20 ? 76 : 66);   // longer lines wrap onto two or three

// Plain data for the Python validator: the same table scripts/showcase/manifest.py loads.
export const shotMeta = () => JSON.parse(JSON.stringify(META));
