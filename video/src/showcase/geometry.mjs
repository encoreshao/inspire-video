// Pure geometry for the showcase composition (no React, no DOM): camera moves, highlight ring,
// callout placement and device choice. Kept in plain ESM so `node --test` can run it.

export const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

export const easeInOut = (t) => {
  const x = clamp(t, 0, 1);
  return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
};

// Largest zoom that keeps the focus rectangle comfortably inside the screen, capped at `max`.
export const zoomFor = (focus, max = 2.2) => clamp(0.8 / Math.max(focus.w, focus.h, 0.01), 1, max);

// Pixel rectangle of the image inside a w x h screen: "cover" fit, zoomed by `zoom` about the focus
// centre, and shifted so the screen never shows empty space.
export function imageRect({iw, ih, w, h, focus, zoom = 1}) {
  const base = Math.max(w / iw, h / ih);
  const width = iw * base * zoom;
  const height = ih * base * zoom;
  const cx = focus.x + focus.w / 2;
  const cy = focus.y + focus.h / 2;
  const left = clamp(w / 2 - cx * width, Math.min(0, w - width), 0);
  const top = clamp(h / 2 - cy * height, Math.min(0, h - height), 0);
  return {left, top, width, height};
}

// Camera for one beat: zoom eases from 1 to the focus zoom over the first 80% of the beat.
export function camera({iw, ih, w, h, focus, progress}) {
  const zoom = 1 + (zoomFor(focus) - 1) * easeInOut(progress / 0.8);
  return imageRect({iw, ih, w, h, focus, zoom});
}

// The focus rectangle in screen pixels for a given image rectangle.
export const focusRect = (rect, focus) => ({
  left: rect.left + focus.x * rect.width,
  top: rect.top + focus.y * rect.height,
  width: focus.w * rect.width,
  height: focus.h * rect.height,
});

// Ring opacity: fades in from 0.6 s, fades out over the last 0.5 s of the beat.
export function ringOpacity(t, duration) {
  const fadeIn = easeInOut((t - 0.6) / 0.4);
  const fadeOut = 1 - easeInOut((t - (duration - 0.5)) / 0.4);
  return clamp(Math.min(fadeIn, fadeOut), 0, 1);
}

// Callout pill (cw x ch): above the ring when it fits, else below; always inside the w x h screen.
export function calloutPosition(ring, cw, ch, w, h, gap = 12) {
  const above = ring.top - ch - gap >= 0;
  const top = above ? ring.top - ch - gap : ring.top + ring.height + gap;
  const left = ring.left + ring.width / 2 - cw / 2;
  return {left: clamp(left, 0, Math.max(0, w - cw)), top: clamp(top, 0, Math.max(0, h - ch))};
}

// Tall screenshots get a phone frame, everything else a browser frame.
export const deviceFor = (iw, ih) => (ih / iw >= 1.3 ? 'phone' : 'browser');
