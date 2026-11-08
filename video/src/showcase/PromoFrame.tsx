import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {SERIF, ThemeCtx, pickTheme} from '../Video';

// The promo style's own look: a dark cinematic frame with a brand lockup at the top, a large stage, captions straight
// on the background and a row of beat pips at the bottom. It shares only theme tokens and fonts with the editorial
// (speaker and device) layout, never its headline block, panel, caption card or info card.
export const PROMO_X = 100;          // the safe side margin: the stage and the pips start here
export const PROMO_TEXT_X = 106;     // text starts a little inside it: a glyph can overshoot its box by a pixel, and the check is strict
export const PROMO_STAGE_TOP = 250;
export const PROMO_CAPTION_TOP = 1250;
export const PROMO_W = 880;
const PIPS_TOP = 1540;               // everything stays above y = 1590

export type PromoFrameProps = {
  theme?: string; name: string; nameZh?: string; tagline?: string; sourceLabel: string;
  beats: {startFrame: number; frames: number}[];
  children: React.ReactNode;
};

export const PromoFrame: React.FC<PromoFrameProps> = ({theme, name, nameZh, tagline, sourceLabel, beats, children}) => {
  const c = pickTheme(theme);
  const frame = useCurrentFrame();
  const gap = 10;
  const pipW = (PROMO_W - gap * (beats.length - 1)) / Math.max(1, beats.length);
  return (
    <ThemeCtx.Provider value={c}>
      <AbsoluteFill style={{backgroundColor: c.paper, color: c.ink, fontFamily: 'Arial, sans-serif'}}>
        <div style={{position: 'absolute', left: PROMO_TEXT_X, top: 140, width: PROMO_W - 2 * (PROMO_TEXT_X - PROMO_X), display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end'}}>
          <div>
            <div style={{display: 'flex', alignItems: 'baseline', gap: 16}}>
              <span style={{fontSize: 40, fontWeight: 700, letterSpacing: 0.5}}>{name}</span>
              {nameZh && nameZh !== name ? <span style={{fontFamily: SERIF, fontSize: 38, fontWeight: 600, color: c.accent}}>{nameZh}</span> : null}
            </div>
            {tagline ? <div style={{fontSize: 24, color: c.muted, marginTop: 6}}>{tagline}</div> : null}
          </div>
          <div style={{fontSize: 22, color: c.muted, border: `2px solid ${c.border}`, borderRadius: 999, padding: '6px 18px'}}>{sourceLabel}</div>
        </div>
        {children}
        <div style={{position: 'absolute', left: PROMO_X, top: PIPS_TOP, width: PROMO_W, display: 'flex', gap}}>
          {beats.map((b, i) => {
            const done = Math.min(1, Math.max(0, (frame - b.startFrame) / b.frames));
            return (
              <div key={i} style={{width: pipW, height: 6, borderRadius: 3, background: c.track, overflow: 'hidden'}}>
                <div style={{width: `${done * 100}%`, height: '100%', background: c.accent}} />
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    </ThemeCtx.Provider>
  );
};
