import React from 'react';
import {AbsoluteFill} from 'remotion';
import {ThemeCtx, onDark, pickTheme, useCaption} from '../Video';
import type {Props} from '../Video';
import type {CoverProps} from '../Cover';
import {DEFAULT_PROFILE, cardHeight, fit, panelWidth, scaleOf} from '../layout.mjs';
import {CaptionText, Clip, Credit, Headline, Progress, coverBandBottom, coverBandTop, headSize} from './kit';

const BG = '#121011';

// The headline on a full-width band in the theme accent (the part above the footage stays one solid block).
const Band: React.FC<{headline: string; size: number; width: number; padY: number; accent: string; safeX: number}> = ({headline, size, width, padY, accent, safeX}) => (
  <div style={{margin: `0 -${safeX}px`, padding: `${padY}px ${safeX}px`, background: accent, color: '#FFF8EF', textAlign: 'center'}}>
    <Headline text={headline} size={size} width={width} style={{lineHeight: 1.22}} />
  </div>
);

// Three-part Douyin-style frame on near-black: headline band on top, full-width footage in the middle,
// large centered captions underneath.
export const BannerShort: React.FC<Props> = (props) => {
  const {headline, subtitle, category, cues, quoteEn, quoteZh, quoteZhUnits, theme, profile = DEFAULT_PROFILE} = props;
  const base = pickTheme(theme);
  const c = onDark(base);
  const {cue, active, alpha, synced, progress} = useCaption(cues, {start: 0, end: 0, en: quoteEn, zh: quoteZh, zhUnits: quoteZhUnits});
  const s = scaleOf(profile);
  const W = panelWidth(profile);
  const limits = {maxH: profile.compact ? 210 : 280, maxEn: 34, minEn: 26, padX: 0, zhOffset: 6};
  const reserve = synced ? cardHeight(cues!, W, limits) : Math.round(170 * s);
  const size = cue ? fit(cue, W, limits) : {en: 32, zh: 38};
  const head = headSize(headline, Math.round(54 * s), W);
  return (
    <ThemeCtx.Provider value={c}>
    <AbsoluteFill style={{background: BG, color: c.ink, fontFamily: 'Arial, sans-serif',
      padding: `${profile.titleTop}px ${profile.safeX}px ${profile.safeBottom}px`, boxSizing: 'border-box', display: 'flex', flexDirection: 'column'}}>
      <div style={{flexShrink: 0, textAlign: 'center', fontSize: Math.round(22 * s), letterSpacing: 4, color: c.accent, fontWeight: 700,
        marginBottom: Math.round(16 * s)}}>{category || 'INSPIRATION / 向上生长'}</div>
      <div style={{flexShrink: 0}}><Band headline={headline} size={head} width={W} padY={Math.round(18 * s)} accent={base.accent} safeX={profile.safeX} /></div>
      <div style={{flexShrink: 0, textAlign: 'center', fontSize: Math.round(30 * s), lineHeight: 1.25, fontWeight: 600, color: c.muted,
        marginTop: Math.round(16 * s)}}>{subtitle}</div>
      <div style={{flex: `0 1 ${Math.round(profile.width * 9 / 16)}px`, minHeight: 0, margin: `${Math.round(32 * s)}px -${profile.safeX}px 0`, overflow: 'hidden'}}>
        <Clip media={props} />
      </div>
      <div style={{height: reserve, flexShrink: 0, marginTop: Math.round(30 * s)}}>
        <CaptionText cue={cue} alpha={alpha} size={size} />
      </div>
      <div style={{flex: 1}} />
      <div style={{flexShrink: 0}}>
        <Credit info={{...props, roleZh: ''}} activeId={active?.speaker} scale={s * 0.85} align="center" />
        <Progress value={progress} scale={s} />
      </div>
    </AbsoluteFill>
    </ThemeCtx.Provider>
  );
};

export const BannerCover: React.FC<CoverProps> = (props) => {
  const {headline, subtitle, category, theme, profile = DEFAULT_PROFILE} = props;
  const base = pickTheme(theme);
  const c = onDark(base);
  const s = scaleOf(profile);
  const W = panelWidth(profile);
  const head = headSize(headline, Math.round(80 * s), W);
  return (
    <ThemeCtx.Provider value={c}>
    <AbsoluteFill style={{background: BG, color: c.ink, fontFamily: 'Arial, sans-serif',
      padding: `${coverBandTop(profile)}px ${profile.safeX}px ${profile.height - coverBandBottom(profile)}px`, boxSizing: 'border-box', display: 'flex', flexDirection: 'column'}}>
      <div style={{textAlign: 'center', fontSize: Math.round(26 * s), letterSpacing: 4, color: c.accent, fontWeight: 700, marginBottom: 20 * s}}>
        {category || 'INSPIRATION / 向上生长'}
      </div>
      <Band headline={headline} size={head} width={W} padY={Math.round(26 * s)} accent={base.accent} safeX={profile.safeX} />
      <div style={{textAlign: 'center', fontSize: Math.round(32 * s), lineHeight: 1.3, color: c.muted, marginTop: 20 * s}}>{subtitle}</div>
      <div style={{flex: 1, minHeight: 0, margin: `${Math.round(36 * s)}px -${profile.safeX}px 0`, overflow: 'hidden'}}>
        <Clip media={props} />
      </div>
      <div style={{marginTop: Math.round(32 * s)}}><Credit info={{...props, role: '', roleZh: '', source: ''}} scale={s * 1.15} align="center" /></div>
    </AbsoluteFill>
    </ThemeCtx.Provider>
  );
};
