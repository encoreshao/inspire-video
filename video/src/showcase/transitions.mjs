// Beat-to-beat transitions for the showcase styles, as pure functions of frames (no React, no DOM) so `node --test`
// can run them. Frames are 30 fps. A beat layer starts `lead` frames before its beat's audio, so the incoming picture
// dissolves during the silence that pads the previous sentence; the beat's own camera starts at its startFrame.
import {easeInOut} from './geometry.mjs';

export const XF_TOPIC = 18;        // 0.6 s: the topic changes (another page or section)
export const XF_SAME = 8;          // 0.27 s: the next beat stays on the same page
export const XF_FIRST = 0;
const OUT_TEXT_SHARE = 0.55;       // the old caption is gone by this share of the transition, the new one starts after it
const IN_TEXT_SECONDS = 0.22;
export const LABEL_DELAY = 0.15;   // seconds after the beat starts
export const LABEL_HOLD = 1.5;     // seconds the topic label stays visible (including its fades)
const LABEL_FADE = 0.25;

const clamp01 = (x) => Math.min(1, Math.max(0, x));
const ease = (x) => easeInOut(clamp01(x));

// A topic change: the topics differ when either beat names one, otherwise the capture (asset) differs. The first beat
// is not a change (there is nothing to change from), though it may still carry a label.
export function topicChanged(prev, beat) {
  if (!prev) return false;
  const a = prev.topic ?? '', b = beat.topic ?? '';
  if (a || b) return a !== b;
  return (prev.asset ?? '') !== (beat.asset ?? '');
}
export const transitionKind = (prev, beat) => (!prev ? 'first' : topicChanged(prev, beat) ? 'topic' : 'same');
// Frames the layer of `beat` starts ahead of its startFrame; never more than the beat's own start allows.
export const transitionLead = (prev, beat) => {
  const k = transitionKind(prev, beat);
  const lead = k === 'topic' ? XF_TOPIC : k === 'same' ? XF_SAME : XF_FIRST;
  return Math.min(lead, Math.max(0, beat.startFrame ?? lead));
};
// Leads for a whole beat list.
export const leadsFor = (beats) => beats.map((b, i) => transitionLead(i ? beats[i - 1] : null, b));

const DRIFT = {topic: {scale: 0.035, dy: 18}, same: {scale: 0.012, dy: 0}, first: {scale: 0, dy: 0}};

// The incoming stage content, `frame` frames into a layer whose transition has `lead` frames. It dissolves in eased and
// settles from a slight offset (scale and rise), arriving at rest exactly when the dissolve ends.
export function incoming(frame, lead, kind) {
  if (lead <= 0) return {opacity: 1, scale: 1, dy: 0};
  const p = ease(frame / lead);
  const d = DRIFT[kind] ?? DRIFT.same;
  return {opacity: p, scale: 1 + d.scale * (1 - p), dy: d.dy * (1 - p)};
}
// The outgoing stage content, `frame` frames into the outgoing transition (`nextLead` long). It stays opaque under the
// incoming layer and drifts the opposite way, so the pair reads as one continuous move.
export function outgoing(frame, nextLead, kind) {
  if (nextLead <= 0) return {scale: 1, dy: 0};
  const g = ease(frame / nextLead);
  const d = DRIFT[kind] ?? DRIFT.same;
  return {scale: 1 + d.scale * 0.6 * g, dy: -d.dy * 0.6 * g};
}

// Caption alpha and rise for the beat. `t` is seconds since the beat's startFrame (negative during its lead);
// `toEnd` is frames until the beat's layer ends (the outgoing transition occupies the last `nextLead` of them).
export function captionAlpha(t, toEnd, nextLead) {
  const inn = ease(t / IN_TEXT_SECONDS);
  const out = nextLead > 0 ? 1 - ease((nextLead - toEnd) / (nextLead * OUT_TEXT_SHARE)) : 1;
  return {opacity: Math.min(inn, out), dy: (1 - inn) * 10};
}

// The topic label: fades in after the dissolve, holds, fades out; `t` is seconds since the beat's startFrame.
export function labelAlpha(t) {
  const x = t - LABEL_DELAY;
  if (x < 0 || x > LABEL_HOLD) return 0;
  return Math.min(ease(x / LABEL_FADE), ease((LABEL_HOLD - x) / LABEL_FADE));
}

// The topic label rule (the manifest validates the same): one string, at most this many width units (a Chinese
// character counts 2, everything else 1), letters, digits, CJK, spaces and the punctuation & / - . , ' and the
// middle dot; no leading or trailing space. A bilingual label is written "Our services · 服务".
export const TOPIC_MAX_UNITS = 28;
export const TOPIC_PATTERN = /^[\p{L}\p{N}][\p{L}\p{N} &/\-.,'·]*[\p{L}\p{N}.]$|^[\p{L}\p{N}]$/u;
export const widthUnits = (s) => [...s].reduce((n, ch) => n + (ch.charCodeAt(0) >= 0x2e80 ? 2 : 1), 0);
export const topicValid = (s) => typeof s === 'string' && TOPIC_PATTERN.test(s) && widthUnits(s) <= TOPIC_MAX_UNITS;

// Progress display. Up to PIPS_MAX beats keep one pip each; more become a continuous bar with a tick at each topic
// change (fractions of the whole video, 0..1).
export const PIPS_MAX = 12;
export function progressLayout(beats) {
  if (beats.length <= PIPS_MAX) return {mode: 'pips', ticks: []};
  const end = beats.reduce((m, b) => Math.max(m, b.startFrame + b.frames), 1);
  const ticks = [];
  for (let i = 1; i < beats.length; i++) if (topicChanged(beats[i - 1], beats[i])) ticks.push(beats[i].startFrame / end);
  return {mode: 'bar', ticks, end};
}
