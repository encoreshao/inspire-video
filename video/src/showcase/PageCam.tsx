import React from 'react';
import {Img, staticFile} from 'remotion';
import {placeImage, promoCamera, stageRect} from './promo.mjs';
import type {Box, Cam, Place, Rect, Size} from './promo.mjs';
import {SHOTS} from './shots.mjs';

const resolve = (p: string) => (/^https?:/.test(p) ? p : staticFile(p));
const SPOT_PAD = 12;          // CSS px of air around the target in the spotlight hole

export type PageCamProps = {
  src: string; page: Size; scale: number; box: Box; shot: string;
  progress: number;            // 0..1 through the beat
  seconds: number;             // the beat length (a shot with a fixed-length move needs it)
  stage: Size;                 // stage size in output px
};

// The cursor of cursor-tour: a fixed 40 px arrow whose tip is at the page point, a small press, and a ring that grows and
// fades after the click. Page points are placed with the same image placement as the picture, so they stay on the page.
const CURSOR_H = 40;
const Cursor: React.FC<{place: Place; cursor: NonNullable<Cam['cursor']>}> = ({place, cursor}) => {
  const at = stageRect({x: cursor.x, y: cursor.y, w: 0, h: 0}, place);
  const ring = cursor.ripple === null ? null : 110 * (0.3 + 1.2 * cursor.ripple);
  return (
    <>
      {ring === null ? null : (
        <div style={{position: 'absolute', left: at.left - ring / 2, top: at.top - ring / 2, width: ring, height: ring, borderRadius: '50%',
          border: '5px solid rgba(17,24,39,0.85)', boxShadow: '0 0 0 3px rgba(255,255,255,0.9)', opacity: 1 - 0.8 * (cursor.ripple as number),
          pointerEvents: 'none'}} />
      )}
      <svg width={CURSOR_H * 0.67} height={CURSOR_H} viewBox="0 0 24 36" style={{position: 'absolute', left: at.left, top: at.top,
        transform: `scale(${1 - 0.16 * cursor.press})`, transformOrigin: '0 0', filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.45))', pointerEvents: 'none'}}>
        <path d="M1 1 L1 29 L8 23 L13 34 L19 32 L14 21 L23 21 Z" fill="#fff" stroke="#111" strokeWidth="2" strokeLinejoin="round" />
      </svg>
    </>
  );
};

// The reticle of scroll-brake: four corner brackets around the target that close in as the camera stops.
const Reticle: React.FC<{rect: Rect; lock: number}> = ({rect, lock}) => {
  const grow = (1 - lock) * 28 + 4, len = 34, w = 5;
  const edge = (pos: React.CSSProperties) => ({position: 'absolute' as const, width: len, height: len, ...pos});
  const line = '5px solid #fff';
  return (
    <div style={{position: 'absolute', left: rect.left - grow, top: rect.top - grow, width: rect.width + 2 * grow, height: rect.height + 2 * grow,
      opacity: lock, filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.5))', pointerEvents: 'none'}}>
      <div style={edge({left: 0, top: 0, borderLeft: line, borderTop: line})} />
      <div style={edge({right: 0, top: 0, borderRight: line, borderTop: line})} />
      <div style={edge({left: 0, bottom: 0, borderLeft: line, borderBottom: line})} />
      <div style={edge({right: 0, bottom: 0, borderRight: line, borderBottom: line})} />
    </div>
  );
};

// The 2x page capture under the camera of the beat's shot.
export const PageCam: React.FC<PageCamProps> = ({src, page, scale, box, shot, progress, seconds, stage}) => {
  const def = SHOTS[shot];
  if (!def || !def.needsTarget) throw new Error(`"${shot}" is not a camera shot`);
  const cam = promoCamera({shot: def, target: box, page, stage, scale, progress, seconds});
  const place = placeImage(page, stage, cam);
  const hole = stageRect({x: box.x - SPOT_PAD, y: box.y - SPOT_PAD, w: box.w + SPOT_PAD * 2, h: box.h + SPOT_PAD * 2}, place);
  return (
    <div style={{position: 'relative', width: stage.w, height: stage.h, overflow: 'hidden', background: '#fff'}}>
      <Img src={resolve(src)} style={{position: 'absolute', left: place.left, top: place.top, width: place.width, height: place.height, maxWidth: 'none'}} />
      {cam.reticle ? <Reticle rect={hole} lock={cam.reticle} /> : null}
      {cam.cursor ? <Cursor place={place} cursor={cam.cursor} /> : null}
      {cam.dim > 0 ? (
        <div style={{position: 'absolute', left: hole.left, top: hole.top, width: hole.width, height: hole.height,
          borderRadius: 14 * place.s, boxShadow: `0 0 0 4000px rgba(0,0,0,${cam.dim})`, pointerEvents: 'none'}} />
      ) : null}
    </div>
  );
};
