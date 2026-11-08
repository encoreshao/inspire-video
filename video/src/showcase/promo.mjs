// Pure camera maths for the promo style (no React, no DOM), so `node --test` can run it.
// Units: the page is in CSS px, the stage in output px, the capture image has `scale` px per CSS px.
// A camera is {zoom, cx, cy}: the page point (cx, cy) sits at the stage centre. At zoom 1 the page width fills the stage.
import {clamp} from './geometry.mjs';

export const STAGE_W = 846;     // the panel's inner width (852 minus its 3 px borders)
export const ZOOM_CAP = 3.2;

export const baseScale = (page, stage) => stage.w / page.w;
export const viewSize = (page, stage, zoom) => ({w: page.w / zoom, h: stage.h / (baseScale(page, stage) * zoom)});
// A page shorter than the stage view needs a zoom above 1, or the stage would show empty space below it.
export const minZoom = (page, stage) => Math.max(1, stage.h / baseScale(page, stage) / page.h);
// Beyond this the capture is scaled up and text goes soft (0.95 leaves a margin).
export const maxZoom = (page, stage, scale) =>
  Math.max(minZoom(page, stage), Math.min(ZOOM_CAP, (0.95 * scale) / baseScale(page, stage)));

export const clampCenter = (page, stage, zoom, c) => {
  const v = viewSize(page, stage, zoom);
  return {cx: clamp(c.cx, v.w / 2, page.w - v.w / 2), cy: clamp(c.cy, v.h / 2, page.h - v.h / 2)};
};

// The zoom at which the target fills `fill` of the stage's limiting side.
export const fitZoom = (page, stage, box, fill = 0.8) => {
  const v1 = viewSize(page, stage, 1);
  return Math.min(v1.w / box.w, v1.h / box.h) * fill;
};

export const targetCenter = (box) => ({cx: box.x + box.w / 2, cy: box.y + box.h / 2});
export const lerp = (a, b, t) => a + (b - a) * t;

// Where the image sits in the stage for a camera, in stage px.
export function placeImage(page, stage, cam) {
  const s = baseScale(page, stage) * cam.zoom;
  return {s, left: stage.w / 2 - cam.cx * s, top: stage.h / 2 - cam.cy * s, width: page.w * s, height: page.h * s};
}

// A page box in stage px.
export const stageRect = (box, place) => ({
  left: place.left + box.x * place.s,
  top: place.top + box.y * place.s,
  width: box.w * place.s,
  height: box.h * place.s,
});

// The caller passes the shot object (from shots.mjs), so this file never imports the registry.
export const promoCamera = ({shot, target, page, stage, scale, progress}) => shot.camera({target, page, stage, scale, progress});

// The stage fills the room left under the headline, above the caption card and info card. 1575 is the safe line
// (1590) minus a margin; 777 is the measured height of everything else at a zero caption reserve (LoopX: content
// ended at y = 1483 with a 217.76 px reserve and a 488 px stage). That was measured with a one-line subtitle; each
// extra line takes 53 px (42 px type at a line height of 1.25). Never smaller than the device zone.
export const stageHeight = (reserve, subtitleLines = 1) =>
  clamp(Math.floor(1575 - 777 - reserve - 53 * (subtitleLines - 1)), 488, 600);
