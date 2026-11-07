import React from 'react';
import {Img, staticFile} from 'remotion';
import {useTheme} from '../Video';
import {calloutPosition, camera, deviceFor, focusRect, ringOpacity, textWidth} from './geometry.mjs';
import type {Focus} from './geometry.mjs';

export type {Focus};
const resolve = (p: string) => (/^https?:/.test(p) ? p : staticFile(p));
const BAR = 38; // browser title bar height

export type DeviceProps = {
  src: string; iw: number; ih: number; focus: Focus;
  progress: number;           // 0..1 through the beat
  t: number; duration: number; // seconds into the beat / beat length
  callout?: string; urlLabel?: string;
  zoneW?: number; zoneH?: number; // size of the device zone (default: the video-window size of the speaker layout)
};

export const DeviceFrame: React.FC<DeviceProps> = ({src, iw, ih, focus, progress, t, duration, callout, urlLabel, zoneW = 846, zoneH = 488}) => {
  const c = useTheme();
  const kind = deviceFor(iw, ih);
  const bodyH = zoneH - 20, bodyW = Math.round(bodyH * 0.52), bezel = 12;
  const screen = kind === 'phone' ? {w: bodyW - bezel * 2, h: bodyH - bezel * 2} : {w: zoneW, h: zoneH - BAR};
  const rect = camera({iw, ih, w: screen.w, h: screen.h, focus, progress});
  const ring = focusRect(rect, focus);
  const op = ringOpacity(t, duration);
  // The pill is sized from the measured text; if the screen is too narrow the font shrinks (never below 13 px) so the label is never cut.
  const PAD = 36, ch = 42;
  const natural = callout ? textWidth(callout, 22) : 0;
  const cw = callout ? Math.min(screen.w - 16, natural + PAD) : 0;
  const fontSize = callout ? Math.max(13, Math.floor(22 * Math.min(1, (cw - PAD) / natural))) : 22;
  const onAccent = c.paper === '#1D1814' ? '#1D1814' : '#fff';   // white on the light-terracotta accent of the ink theme is too faint
  const pill = callout ? calloutPosition(ring, cw, ch, screen.w, screen.h) : {left: 0, top: 0};

  const screenEl = (radius: number) => (
    <div style={{position: 'relative', width: screen.w, height: screen.h, overflow: 'hidden', borderRadius: radius, background: '#fff'}}>
      <Img src={resolve(src)} style={{position: 'absolute', left: rect.left, top: rect.top, width: rect.width, height: rect.height, maxWidth: 'none'}} />
      <div style={{position: 'absolute', left: ring.left - 8, top: ring.top - 8, width: ring.width + 16, height: ring.height + 16,
        border: `5px solid ${c.accent}`, borderRadius: 16, opacity: op, boxShadow: `0 0 22px ${c.accent}99`, boxSizing: 'border-box'}} />
      {callout ? (
        <div style={{position: 'absolute', left: pill.left, top: pill.top, width: cw, height: ch, opacity: op, background: c.accent, color: onAccent,
          borderRadius: 999, fontSize, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center',
          whiteSpace: 'nowrap', overflow: 'hidden', boxShadow: '0 6px 16px rgba(0,0,0,0.25)'}}>{callout}</div>
      ) : null}
    </div>
  );

  if (kind === 'phone') {
    return (
      <div style={{position: 'relative', width: zoneW, height: zoneH, overflow: 'hidden', background: c.videoBg}}>
        <Img src={resolve(src)} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover',
          filter: 'blur(28px) brightness(0.7)', transform: 'scale(1.2)'}} />
        <div style={{position: 'absolute', left: (zoneW - bodyW) / 2, top: 10, width: bodyW, height: bodyH, boxSizing: 'border-box',
          background: '#0f0f10', borderRadius: 40, padding: bezel, boxShadow: '0 18px 40px rgba(0,0,0,0.45)'}}>
          {screenEl(28)}
        </div>
      </div>
    );
  }
  return (
    <div style={{width: zoneW, height: zoneH, background: c.card}}>
      <div style={{height: BAR, background: '#E7E1D6', display: 'flex', alignItems: 'center', gap: 8, padding: '0 16px', boxSizing: 'border-box'}}>
        {['#E5604F', '#F2B94B', '#62C468'].map((k) => <div key={k} style={{width: 12, height: 12, borderRadius: 6, background: k}} />)}
        <div style={{marginLeft: 12, height: 24, flex: 1, maxWidth: zoneW * 0.6, borderRadius: 12, background: '#F8F5EF', color: '#6F695E',
          fontSize: 16, display: 'flex', alignItems: 'center', padding: '0 14px', overflow: 'hidden', whiteSpace: 'nowrap'}}>{urlLabel ?? ''}</div>
      </div>
      {screenEl(0)}
    </div>
  );
};
