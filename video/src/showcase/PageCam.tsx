import React from 'react';
import {Img, staticFile} from 'remotion';
import {placeImage, promoCamera, stageRect} from './promo.mjs';
import type {Box, Size} from './promo.mjs';
import {SHOTS} from './shots.mjs';

const resolve = (p: string) => (/^https?:/.test(p) ? p : staticFile(p));
const SPOT_PAD = 12;          // CSS px of air around the target in the spotlight hole

export type PageCamProps = {
  src: string; page: Size; scale: number; box: Box; shot: string;
  progress: number;            // 0..1 through the beat
  stage: Size;                 // stage size in output px
};

// The 2x page capture under the camera of the beat's shot.
export const PageCam: React.FC<PageCamProps> = ({src, page, scale, box, shot, progress, stage}) => {
  const def = SHOTS[shot];
  if (!def) throw new Error(`unknown shot "${shot}"`);
  const cam = promoCamera({shot: def, target: box, page, stage, scale, progress});
  const place = placeImage(page, stage, cam);
  const hole = stageRect({x: box.x - SPOT_PAD, y: box.y - SPOT_PAD, w: box.w + SPOT_PAD * 2, h: box.h + SPOT_PAD * 2}, place);
  return (
    <div style={{position: 'relative', width: stage.w, height: stage.h, overflow: 'hidden', background: '#fff'}}>
      <Img src={resolve(src)} style={{position: 'absolute', left: place.left, top: place.top, width: place.width, height: place.height, maxWidth: 'none'}} />
      {cam.dim > 0 ? (
        <div style={{position: 'absolute', left: hole.left, top: hole.top, width: hole.width, height: hole.height,
          borderRadius: 14 * place.s, boxShadow: `0 0 0 4000px rgba(0,0,0,${cam.dim})`, pointerEvents: 'none'}} />
      ) : null}
    </div>
  );
};
