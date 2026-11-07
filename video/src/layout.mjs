// Pure layout maths shared by the Remotion compositions (no React, no DOM) so `node --test` can check it.
// DEFAULT_PROFILE is the original 9:16 layout; it must equal the `vertical-9x16` block of config/platforms.yaml
// (tests/test_layout_js.py checks that).

export const DEFAULT_PROFILE = {id: 'vertical-9x16', width: 1080, height: 1920, safeX: 114, safeTop: 190, safeBottom: 330, titleTop: 256, compact: false};

export const MIN_VIDEO_H = 320;     // below this the video panel is too small to be worth shipping
export const CARD_PAD_Y = 12;       // vertical padding inside the caption card

export const scaleOf = (p) => (p.compact ? 0.82 : 1);     // fonts and gaps in the compact layout
export const panelWidth = (p) => p.width - p.safeX * 2;   // 852 for the default profile
export const cardLimits = (p) => (p.compact ? {maxH: 300, maxEn: 28, minEn: 22} : {maxH: 400, maxEn: 32, minEn: 26});

// Height in px the caption text needs at English font size `en` (Chinese is en + 2), estimated line wrapping.
export const needed = (cue, en, panelW = 852) => {
  const textW = panelW - 6 - 64; // panel inner width minus card padding
  const zh = en + 2;
  const enLines = Math.ceil((cue.en.length * en * 0.54) / textW);
  const zhLines = Math.ceil((cue.zh.length * zh * 1.04) / textW);
  return enLines * en * 1.28 + zhLines * zh * 1.38 + 14;
};

// Largest English font size (even steps, capped) at which both languages fit the card.
export const fit = (cue, panelW = 852, {maxH = 400, maxEn = 32, minEn = 26} = {}) => {
  for (let en = maxEn; en >= minEn; en -= 2) {
    if (needed(cue, en, panelW) <= maxH) return {en, zh: en + 2};
  }
  return {en: minEn, zh: minEn + 2};
};

// The card is sized to the tallest cue so nothing moves between captions.
export const cardHeight = (cues, panelW = 852, limits = {}) =>
  Math.max(64, ...cues.map((q) => needed(q, fit(q, panelW, limits).en, panelW))) + CARD_PAD_Y * 2 + 4;

// One line when the headline fits the width, otherwise two (mirrors HeadlineLines in Video.tsx).
export const headlineLines = (text, size, width) => (text.length * (size + 1) <= width ? 1 : 2);

export const INFO_H = 255; // estimated height of the bottom info card at scale 1 (speaker, role, talk title, source)

// Height of the video inside the joined panel. The default layout keeps its fixed numbers (so 9:16 output does not
// change); the compact layout gets whatever vertical room is left after the other blocks.
export function panelVideoHeight({profile = DEFAULT_PROFILE, fit: videoFit = 'cover', headlineLines: lines = 2, cardReserve}) {
  const contain = Math.round((panelWidth(profile) - 6) * 9 / 16);
  if (!profile.compact) return videoFit === 'cover' ? 488 : contain;
  const s = scaleOf(profile);
  const header = s * (41 + 54.6 * lines + 60.5);          // label + headline lines + subtitle
  const gaps = 3 * 26 * s + 11;                           // divider/panel gaps, dividers and panel borders
  const fixed = header + gaps + 20 * s + INFO_H * s + 30 * s; // info block margin, info card, progress bar
  const room = Math.floor(profile.height - profile.safeBottom - profile.titleTop - fixed - cardReserve);
  return videoFit === 'cover' ? room : Math.min(room, contain);
}

export const fits = (videoH) => videoH >= MIN_VIDEO_H;
