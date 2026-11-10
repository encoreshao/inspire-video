import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {SERIF, ThemeCtx, pickTheme} from '../Video';
import {PROMO_STAGE_H, STAGE_W, promoBackground, promoShadow} from './promo.mjs';
import {progressLayout} from './transitions.mjs';

// The promo style's own look: a dark cinematic frame with a brand lockup at the top, a large stage, captions straight
// on the background and a row of beat pips at the bottom. It shares only theme tokens and fonts with the editorial
// (speaker and device) layout, and text helpers, never its panel, caption card or info card.
export const PROMO_X = 100;          // the safe side margin: the stage and the pips start here
export const PROMO_TEXT_X = 106;     // text starts a little inside it: a glyph can overshoot its box by a pixel, and the check is strict
export const PROMO_STAGE_TOP = 250;
export const PROMO_CAPTION_TOP = 1250;
export const PROMO_W = 880;
const PIPS_TOP = 1540;              // everything stays above y = 1590

export type PromoFrameProps = {
  theme?: string; brand?: string; name: string; nameZh?: string; tagline?: string; sourceLabel: string;
  beats: {startFrame: number; frames: number; asset?: string; topic?: string}[];
  children: React.ReactNode;
};

export const PromoFrame: React.FC<PromoFrameProps> = ({theme, brand, name, nameZh, tagline, sourceLabel, beats, children}) => {
  const c = pickTheme(theme);
  const frame = useCurrentFrame();
  const gap = 10;
  const layout = progressLayout(beats);
  const total = beats.reduce((m, b) => Math.max(m, b.startFrame + b.frames), 1);
  const overall = Math.min(1, Math.max(0, frame / total));
  const pipW = (PROMO_W - gap * (beats.length - 1)) / Math.max(1, beats.length);
  return (
    <ThemeCtx.Provider value={c}>
      <AbsoluteFill style={{background: promoBackground(c.paper, brand), color: c.ink, fontFamily: 'Arial, sans-serif'}}>
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
        {/* The stage's shadow and card live here, once, so the beat layers that dissolve over each other never stack shadows. */}
        <div style={{position: 'absolute', left: PROMO_X, top: PROMO_STAGE_TOP, width: STAGE_W, height: PROMO_STAGE_H, borderRadius: 36,
          boxShadow: promoShadow(c.paper), background: c.card}} />
        {children}
        {layout.mode === 'bar' ? (
          // A long video: one continuous bar, a small gap at every topic change.
          <div style={{position: 'absolute', left: PROMO_X, top: PIPS_TOP, width: PROMO_W, height: 6, borderRadius: 3, background: c.track, overflow: 'hidden'}}>
            <div style={{width: `${overall * 100}%`, height: '100%', background: c.accent}} />
            {layout.ticks.map((x, i) => (
              <div key={i} style={{position: 'absolute', top: 0, left: `calc(${x * 100}% - 1.5px)`, width: 3, height: '100%', background: c.paper}} />
            ))}
          </div>
        ) : (
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
        )}
      </AbsoluteFill>
    </ThemeCtx.Provider>
  );
};
