import test from 'node:test';
import assert from 'node:assert/strict';
import {
  DEFAULT_PROFILE, MIN_VIDEO_H, cardHeight, cardLimits, fit, fits, headlineLines, needed, panelVideoHeight, panelWidth, scaleOf,
} from './layout.mjs';

// The real registry profiles come from the pytest wrapper (PROFILES_JSON); standalone runs use these copies.
const FALLBACK = {
  'vertical-9x16': {...DEFAULT_PROFILE, supported: true},
  'portrait-4x5': {id: 'portrait-4x5', width: 1080, height: 1350, safeX: 60, safeTop: 90, safeBottom: 150, titleTop: 110, compact: true, supported: true},
  'square-1x1': {id: 'square-1x1', width: 1080, height: 1080, safeX: 60, safeTop: 80, safeBottom: 120, titleTop: 90, compact: true, supported: false},
  'landscape-16x9': {id: 'landscape-16x9', width: 1920, height: 1080, safeX: 120, safeTop: 70, safeBottom: 110, titleTop: 90, compact: false, supported: false},
};
const PROFILES = process.env.PROFILES_JSON ? JSON.parse(process.env.PROFILES_JSON) : FALLBACK;

// The formulas as they were in Video.tsx before profiles existed.
const legacyNeeded = (cue, en) => {
  const textW = 852 - 6 - 64;
  const zh = en + 2;
  return Math.ceil((cue.en.length * en * 0.54) / textW) * en * 1.28 + Math.ceil((cue.zh.length * zh * 1.04) / textW) * zh * 1.38 + 14;
};
const legacyFit = (cue) => {
  for (let en = 32; en >= 26; en -= 2) if (legacyNeeded(cue, en) <= 400) return {en, zh: en + 2};
  return {en: 26, zh: 28};
};
const legacyCardHeight = (cues) => Math.max(64, ...cues.map((q) => legacyNeeded(q, legacyFit(q).en))) + 12 * 2 + 4;

const cue = (en, zh) => ({en: 'e'.repeat(en), zh: '字'.repeat(zh)});

test('the default profile is the old 9:16 layout', () => {
  assert.deepEqual(DEFAULT_PROFILE, {id: 'vertical-9x16', width: 1080, height: 1920, safeX: 114, safeTop: 190, safeBottom: 330, titleTop: 256, compact: false});
  assert.equal(panelWidth(DEFAULT_PROFILE), 852);
  assert.equal(scaleOf(DEFAULT_PROFILE), 1);
});

test('needed, fit and cardHeight give the old numbers by default', () => {
  const cues = [];
  for (let en = 10; en <= 120; en += 10) for (let zh = 4; zh <= 70; zh += 11) cues.push(cue(en, zh));
  for (const q of cues) {
    for (const size of [26, 30, 32, 34]) assert.equal(needed(q, size), legacyNeeded(q, size));
    assert.deepEqual(fit(q), legacyFit(q));
  }
  assert.equal(cardHeight(cues), legacyCardHeight(cues));
  assert.equal(cardHeight([]), 64 + 28);
});

test('the default video height is the old one', () => {
  assert.equal(panelVideoHeight({profile: DEFAULT_PROFILE, fit: 'cover', headlineLines: 2, cardReserve: 999}), 488);
  assert.equal(panelVideoHeight({profile: DEFAULT_PROFILE, fit: 'contain', headlineLines: 1, cardReserve: 1}), Math.round(846 * 9 / 16));
});

test('headlineLines mirrors HeadlineLines', () => {
  assert.equal(headlineLines('先行动，再自信', 42, 984), 1);
  assert.equal(headlineLines('字'.repeat(30), 42, 984), 2);
});

test('compact fonts shrink and the card limits tighten', () => {
  assert.equal(scaleOf(PROFILES['portrait-4x5']), 0.82);
  assert.deepEqual(cardLimits(PROFILES['portrait-4x5']), {maxH: 300, maxEn: 28, minEn: 22});
  assert.deepEqual(cardLimits(DEFAULT_PROFILE), {maxH: 400, maxEn: 32, minEn: 26});
});

test('the longest allowed caption still leaves a usable video in every compact profile that claims support', () => {
  const longest = [cue(100, 50), cue(60, 30)];
  for (const p of Object.values(PROFILES)) {
    if (!p.compact) continue;
    const reserve = cardHeight(longest, panelWidth(p), cardLimits(p));
    const h = panelVideoHeight({profile: p, fit: 'cover', headlineLines: 2, cardReserve: reserve});
    assert.equal(fits(h), p.supported, `${p.id}: video ${h}px (min ${MIN_VIDEO_H}) but supported=${p.supported}`);
  }
});

test('a profile with no layout of its own must be marked unsupported', () => {
  for (const p of Object.values(PROFILES)) assert.ok(p.id === 'vertical-9x16' || p.compact || !p.supported, p.id);
});

test('4:5 at the longest caption has a video panel that is not tiny', () => {
  const p = PROFILES['portrait-4x5'];
  const reserve = cardHeight([cue(100, 50)], panelWidth(p), cardLimits(p));
  assert.ok(panelVideoHeight({profile: p, fit: 'cover', headlineLines: 2, cardReserve: reserve}) >= MIN_VIDEO_H);
});
