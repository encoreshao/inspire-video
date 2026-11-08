import React from 'react';
import {AbsoluteFill} from 'remotion';
import {HeadlineLines, SERIF, ThemeCtx, pickTheme} from '../Video';
import {PROMO_SHADOW, PROMO_TEXT_X, PROMO_W, PROMO_X} from './PromoFrame';
import {PageCam} from './PageCam';
import {Statement} from './Statement';
import type {ShowcaseBeat} from './ShowcaseShort';

export type PromoCoverProps = {headline: string; subtitle: string; category?: string; theme?: string; name: string; nameZh?: string;
  tagline?: string; sourceLabel: string; beat: ShowcaseBeat};

const STAGE_H = 760;

// The promo cover: the headline large on the dark frame, the hero framing of the first beat in a big rounded stage,
// and the brand and address below. Nothing here is the editorial info card.
export const PromoCover: React.FC<PromoCoverProps> = ({headline, subtitle, category, theme, name, nameZh, tagline, sourceLabel, beat}) => {
  const c = pickTheme(theme);
  const stage = {w: PROMO_W, h: STAGE_H};
  return (
    <ThemeCtx.Provider value={c}>
      <AbsoluteFill style={{backgroundColor: c.paper, color: c.ink, fontFamily: 'Arial, sans-serif'}}>
        <div style={{position: 'absolute', left: PROMO_TEXT_X, top: 120, width: PROMO_W - 2 * (PROMO_TEXT_X - PROMO_X)}}>
          <div style={{fontSize: 26, letterSpacing: 3, color: c.accent, marginBottom: 22}}>{category || 'PROMO / 产品宣传'}</div>
          <div style={{fontFamily: SERIF, fontSize: 92, lineHeight: 1.14, fontWeight: 700, letterSpacing: 1}}>
            <HeadlineLines text={headline} size={92} width={PROMO_W} />
          </div>
          <div style={{fontSize: 38, lineHeight: 1.3, color: c.muted, marginTop: 22}}>{subtitle}</div>
        </div>
        <div style={{position: 'absolute', left: PROMO_X, top: 640, width: PROMO_W, height: STAGE_H, borderRadius: 36, overflow: 'hidden', boxShadow: PROMO_SHADOW}}>
          {beat.shot === 'statement' ? (
            <Statement text={beat.statement ?? ''} units={beat.statementUnits ?? [beat.statement ?? '']} stage={stage} frame={9999} />
          ) : beat.box && beat.page && beat.shot ? (
            <PageCam src={beat.asset} page={beat.page} scale={beat.imageScale ?? 1} box={beat.box}
              shot={beat.shot === 'spotlight-focus' ? 'hero-push' : beat.shot} progress={1} seconds={beat.frames / 30} stage={stage} />
          ) : null}
          <div style={{position: 'absolute', inset: 0, borderRadius: 36, border: `2px solid ${c.border}`, pointerEvents: 'none'}} />
        </div>
        <div style={{position: 'absolute', left: PROMO_TEXT_X, top: 1450, width: PROMO_W - 2 * (PROMO_TEXT_X - PROMO_X), display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end'}}>
          <div>
            <div style={{display: 'flex', alignItems: 'baseline', gap: 16}}>
              <span style={{fontSize: 44, fontWeight: 700}}>{name}</span>
              {nameZh && nameZh !== name ? <span style={{fontFamily: SERIF, fontSize: 42, fontWeight: 600, color: c.accent}}>{nameZh}</span> : null}
            </div>
            {tagline ? <div style={{fontSize: 26, color: c.muted, marginTop: 6}}>{tagline}</div> : null}
          </div>
          <div style={{fontSize: 24, color: c.muted, border: `2px solid ${c.border}`, borderRadius: 999, padding: '8px 20px'}}>{sourceLabel}</div>
        </div>
      </AbsoluteFill>
    </ThemeCtx.Provider>
  );
};
