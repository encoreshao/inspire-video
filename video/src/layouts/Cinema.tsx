import React from 'react';
import {AbsoluteFill} from 'remotion';
import {ThemeCtx, onDark, pickTheme, useCaption} from '../Video';
import type {Props} from '../Video';
import type {CoverProps} from '../Cover';
import {DEFAULT_PROFILE, cardHeight, fit, panelWidth, scaleOf} from '../layout.mjs';
import {CaptionText, Clip, Credit, Headline, Progress, coverBandBottom, coverBandTop, headSize} from './kit';

const SHADOW = '0 2px 14px rgba(0,0,0,0.75)';
const Scrims: React.FC<{bottomFrom?: number}> = ({bottomFrom = 58}) => (
  <>
    <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,0.72) 0%, rgba(0,0,0,0.38) 20%, rgba(0,0,0,0) 36%)'}} />
    <AbsoluteFill style={{background: `linear-gradient(0deg, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0.66) 28%, rgba(0,0,0,0) ${bottomFrom}%)`}} />
  </>
);

// The footage fills the screen (cropped around crop_x / crop_y); title on top and captions in the lower third over soft scrims.
export const CinemaShort: React.FC<Props> = (props) => {
  const {headline, subtitle, category, cues, quoteEn, quoteZh, quoteZhUnits, theme, profile = DEFAULT_PROFILE} = props;
  const c = onDark(pickTheme(theme));
  const {cue, active, alpha, synced, progress} = useCaption(cues, {start: 0, end: 0, en: quoteEn, zh: quoteZh, zhUnits: quoteZhUnits});
  const s = scaleOf(profile);
  const W = panelWidth(profile);
  const limits = {maxH: profile.compact ? 220 : 290, maxEn: 36, minEn: 28, padX: 0, zhOffset: 4};
  const reserve = synced ? cardHeight(cues!, W, limits) : Math.round(170 * s);
  const size = cue ? fit(cue, W, limits) : {en: 34, zh: 38};
  const head = headSize(headline, Math.round(50 * s), W);
  return (
    <ThemeCtx.Provider value={c}>
    <AbsoluteFill style={{background: '#000', color: c.ink, fontFamily: 'Arial, sans-serif'}}>
      <AbsoluteFill><Clip media={{...props, videoFit: 'cover'}} /></AbsoluteFill>
      <Scrims />
      <div style={{position: 'absolute', top: profile.titleTop, left: profile.safeX, width: W, textShadow: SHADOW}}>
        <div style={{fontSize: Math.round(22 * s), letterSpacing: 3, color: c.accent, fontWeight: 700, marginBottom: Math.round(14 * s)}}>
          {category || 'INSPIRATION / 向上生长'}
        </div>
        <Headline text={headline} size={head} width={W} />
        <div style={{fontSize: Math.round(30 * s), lineHeight: 1.25, fontWeight: 600, color: c.muted, marginTop: Math.round(8 * s)}}>{subtitle}</div>
      </div>
      <div style={{position: 'absolute', bottom: profile.safeBottom, left: profile.safeX, width: W}}>
        <div style={{height: reserve, display: 'flex', flexDirection: 'column', justifyContent: 'flex-end'}}>
          <CaptionText cue={cue} alpha={alpha} size={size} shadow={SHADOW} />
        </div>
        <div style={{marginTop: Math.round(26 * s), paddingTop: Math.round(18 * s), borderTop: `2px solid ${c.border}`}}>
          <Credit info={{...props, roleZh: ''}} activeId={active?.speaker} scale={s * 0.9} shadow={SHADOW} />
          <Progress value={progress} scale={s} />
        </div>
      </div>
    </AbsoluteFill>
    </ThemeCtx.Provider>
  );
};

export const CinemaCover: React.FC<CoverProps> = (props) => {
  const {headline, subtitle, category, theme, profile = DEFAULT_PROFILE} = props;
  const c = onDark(pickTheme(theme));
  const s = scaleOf(profile);
  const W = panelWidth(profile);
  const head = headSize(headline, Math.round(84 * s), W);
  return (
    <ThemeCtx.Provider value={c}>
    <AbsoluteFill style={{background: '#000', color: c.ink, fontFamily: 'Arial, sans-serif'}}>
      <AbsoluteFill><Clip media={props} /></AbsoluteFill>
      <Scrims bottomFrom={66} />
      <div style={{position: 'absolute', top: coverBandTop(profile), left: profile.safeX, width: W, textShadow: SHADOW}}>
        <div style={{display: 'inline-block', fontSize: Math.round(26 * s), letterSpacing: 3, fontWeight: 700, color: '#17120F',
          background: c.accent, borderRadius: 999, padding: `${8 * s}px ${22 * s}px`, textShadow: 'none'}}>{category || 'INSPIRATION / 向上生长'}</div>
      </div>
      <div style={{position: 'absolute', bottom: profile.height - coverBandBottom(profile), left: profile.safeX, width: W, textShadow: SHADOW}}>
        <Headline text={headline} size={head} width={W} style={{lineHeight: 1.18}} />
        <div style={{fontSize: Math.round(32 * s), lineHeight: 1.3, color: c.muted, marginTop: 16 * s}}>{subtitle}</div>
        <div style={{width: 72 * s, height: 5, background: c.accent, borderRadius: 3, margin: `${28 * s}px 0 ${22 * s}px`}} />
        <Credit info={{...props, role: '', roleZh: '', source: ''}} scale={s * 1.1} />
      </div>
    </AbsoluteFill>
    </ThemeCtx.Provider>
  );
};
