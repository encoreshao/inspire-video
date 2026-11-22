import React from 'react';
import {AbsoluteFill} from 'remotion';
import {ThemeCtx, onDark, pickTheme, useCaption} from '../Video';
import type {Props} from '../Video';
import type {CoverProps} from '../Cover';
import {DEFAULT_PROFILE, cardHeight, fit, panelWidth, scaleOf} from '../layout.mjs';
import {CaptionText, Clip, Credit, Headline, Progress, coverBandBottom, coverBandTop, headSize} from './kit';
import type {Media} from './kit';

const Blurred: React.FC<{media: Media}> = ({media}) => (
  <AbsoluteFill style={{overflow: 'hidden'}}>
    <Clip media={{...media, videoFit: 'cover'}} muted style={{transform: 'scale(1.25)', filter: 'blur(46px) brightness(0.42) saturate(1.2)'}} />
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 30%, rgba(0,0,0,0.45) 100%)'}} />
  </AbsoluteFill>
);

// Full-width footage over a blurred, darkened copy of itself; title above, captions below.
export const BackdropShort: React.FC<Props> = (props) => {
  const {headline, subtitle, category, cues, quoteEn, quoteZh, quoteZhUnits, theme, profile = DEFAULT_PROFILE} = props;
  const c = onDark(pickTheme(theme));
  const {cue, active, alpha, synced, progress} = useCaption(cues, {start: 0, end: 0, en: quoteEn, zh: quoteZh, zhUnits: quoteZhUnits});
  const s = scaleOf(profile);
  const W = panelWidth(profile);
  const limits = {maxH: profile.compact ? 220 : 300, maxEn: 34, minEn: 26, padX: 0, zhOffset: 4};
  const reserve = synced ? cardHeight(cues!, W, limits) : Math.round(170 * s);
  const size = cue ? fit(cue, W, limits) : {en: 32, zh: 36};
  const head = headSize(headline, Math.round(48 * s), W);
  return (
    <ThemeCtx.Provider value={c}>
    <AbsoluteFill style={{background: '#000', color: c.ink, fontFamily: 'Arial, sans-serif'}}>
      <Blurred media={props} />
      <AbsoluteFill style={{padding: `${profile.titleTop}px ${profile.safeX}px ${profile.safeBottom}px`, boxSizing: 'border-box',
        display: 'flex', flexDirection: 'column'}}>
        <div style={{flexShrink: 0}}>
          <div style={{fontSize: Math.round(22 * s), letterSpacing: 3, color: c.accent, fontWeight: 700, marginBottom: Math.round(14 * s)}}>
            {category || 'INSPIRATION / 向上生长'}
          </div>
          <Headline text={headline} size={head} width={W} />
          <div style={{fontSize: Math.round(32 * s), lineHeight: 1.25, fontWeight: 600, color: c.muted, marginTop: Math.round(8 * s)}}>{subtitle}</div>
        </div>
        <div style={{flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', justifyContent: 'center'}}>
          <div style={{flex: `0 1 ${Math.round(profile.width * 9 / 16)}px`, minHeight: 0, margin: `0 -${profile.safeX}px`,
            boxShadow: '0 30px 70px rgba(0,0,0,0.55)', overflow: 'hidden'}}>
            <Clip media={props} />
          </div>
          <div style={{height: reserve, flexShrink: 0, marginTop: Math.round(34 * s)}}>
            <CaptionText cue={cue} alpha={alpha} size={size} shadow="0 2px 10px rgba(0,0,0,0.5)" />
          </div>
        </div>
        <div style={{flexShrink: 0, marginTop: Math.round(18 * s)}}>
          <Credit info={props} activeId={active?.speaker} scale={s} align="center" />
          <Progress value={progress} scale={s} />
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
    </ThemeCtx.Provider>
  );
};

export const BackdropCover: React.FC<CoverProps> = (props) => {
  const {headline, subtitle, category, theme, profile = DEFAULT_PROFILE} = props;
  const c = onDark(pickTheme(theme));
  const s = scaleOf(profile);
  const W = panelWidth(profile);
  const head = headSize(headline, Math.round(76 * s), W);
  return (
    <ThemeCtx.Provider value={c}>
    <AbsoluteFill style={{background: '#000', color: c.ink, fontFamily: 'Arial, sans-serif'}}>
      <Blurred media={props} />
      <AbsoluteFill style={{padding: `${coverBandTop(profile)}px ${profile.safeX}px ${profile.height - coverBandBottom(profile)}px`, display: 'flex', flexDirection: 'column', boxSizing: 'border-box'}}>
        <div style={{fontSize: Math.round(26 * s), letterSpacing: 3, color: c.accent, fontWeight: 700}}>{category || 'INSPIRATION / 向上生长'}</div>
        <Headline text={headline} size={head} width={W} style={{marginTop: 18 * s, lineHeight: 1.2}} />
        <div style={{fontSize: Math.round(32 * s), lineHeight: 1.3, color: c.muted, marginTop: 14 * s}}>{subtitle}</div>
        <div style={{flex: 1, minHeight: 0, margin: `${Math.round(44 * s)}px -${profile.safeX}px 0`,
          overflow: 'hidden', boxShadow: '0 30px 70px rgba(0,0,0,0.55)'}}>
          <Clip media={props} />
        </div>
        <div style={{marginTop: Math.round(34 * s)}}><Credit info={{...props, role: '', roleZh: '', source: ''}} scale={s * 1.15} align="center" /></div>
      </AbsoluteFill>
    </AbsoluteFill>
    </ThemeCtx.Provider>
  );
};
