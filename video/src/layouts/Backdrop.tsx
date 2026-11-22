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
    <Clip media={{...media, videoFit: 'cover'}} muted style={{transform: 'scale(1.3)', filter: 'blur(40px) brightness(0.55) saturate(1.35)'}} />
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 40%, rgba(0,0,0,0) 25%, rgba(0,0,0,0.5) 100%)'}} />
  </AbsoluteFill>
);

const GLASS: React.CSSProperties = {background: 'rgba(255,255,255,0.13)', border: '1.5px solid rgba(255,255,255,0.32)',
  boxShadow: '0 20px 50px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.25)', backdropFilter: 'blur(18px)'};

const Pill: React.FC<{text: string; size: number}> = ({text, size}) => (
  <div style={{...GLASS, display: 'inline-block', borderRadius: 999, fontSize: size, letterSpacing: 3, fontWeight: 700, padding: `${size * 0.4}px ${size}px`}}>{text}</div>
);

const Card: React.FC<{media: Media; children?: React.ReactNode; style?: React.CSSProperties}> = ({media, children, style}) => (
  <div style={{position: 'relative', borderRadius: 32, overflow: 'hidden', border: '2px solid rgba(255,255,255,0.4)',
    boxShadow: '0 40px 90px rgba(0,0,0,0.6)', background: '#111', ...style}}>
    <Clip media={media} />
    {children}
  </div>
);

// Floating glass: the footage as a rounded card over a blurred, glowing copy of itself, captions in a frosted card,
// everything centered.
export const BackdropShort: React.FC<Props> = (props) => {
  const {headline, subtitle, category, cues, quoteEn, quoteZh, quoteZhUnits, theme, profile = DEFAULT_PROFILE} = props;
  const c = onDark(pickTheme(theme));
  const {cue, active, alpha, synced, progress} = useCaption(cues, {start: 0, end: 0, en: quoteEn, zh: quoteZh, zhUnits: quoteZhUnits});
  const s = scaleOf(profile);
  const W = panelWidth(profile);
  const pad = Math.round(26 * s);
  const limits = {maxH: profile.compact ? 210 : 290, maxEn: 32, minEn: 26, padX: pad * 2 + 4, zhOffset: 4};
  const reserve = synced ? cardHeight(cues!, W, limits) : Math.round(170 * s);
  const size = cue ? fit(cue, W, limits) : {en: 30, zh: 34};
  return (
    <ThemeCtx.Provider value={c}>
    <AbsoluteFill style={{background: '#000', color: c.ink, fontFamily: 'Arial, sans-serif'}}>
      <Blurred media={props} />
      <AbsoluteFill style={{padding: `${profile.titleTop}px ${profile.safeX}px ${profile.safeBottom}px`, boxSizing: 'border-box',
        display: 'flex', flexDirection: 'column', textAlign: 'center'}}>
        <div style={{flexShrink: 0}}>
          <Pill text={category || 'INSPIRATION / 向上生长'} size={Math.round(20 * s)} />
          <Headline text={headline} size={headSize(headline, Math.round(46 * s), W)} width={W} style={{marginTop: Math.round(18 * s)}} />
          <div style={{fontSize: Math.round(28 * s), lineHeight: 1.25, color: c.muted, marginTop: Math.round(6 * s)}}>{subtitle}</div>
        </div>
        <div style={{flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', justifyContent: 'center'}}>
          <Card media={props} style={{flex: `0 1 ${Math.round(W * 9 / 16)}px`, minHeight: 0}} />
          <div style={{...GLASS, borderRadius: 28, marginTop: Math.round(24 * s), padding: `${pad}px`, height: reserve, flexShrink: 0}}>
            <CaptionText cue={cue} alpha={alpha} size={size} zhColor={c.accent} />
          </div>
        </div>
        <div style={{flexShrink: 0, marginTop: Math.round(18 * s)}}>
          <Credit info={{...props, roleZh: ''}} activeId={active?.speaker} scale={s * 0.9} align="center" />
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
  return (
    <ThemeCtx.Provider value={c}>
    <AbsoluteFill style={{background: '#000', color: c.ink, fontFamily: 'Arial, sans-serif'}}>
      <Blurred media={props} />
      <AbsoluteFill style={{padding: `${coverBandTop(profile)}px ${profile.safeX}px ${profile.height - coverBandBottom(profile)}px`,
        display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', boxSizing: 'border-box'}}>
        <Pill text={category || 'INSPIRATION / 向上生长'} size={Math.round(24 * s)} />
        <Card media={props} style={{flex: 1, minHeight: 0, width: '100%', marginTop: Math.round(30 * s)}}>
          <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, padding: `${Math.round(90 * s)}px ${Math.round(32 * s)}px ${Math.round(30 * s)}px`,
            background: 'linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(0,0,0,0.75) 100%)'}}>
            <Credit info={{...props, role: '', roleZh: '', source: ''}} scale={s * 1.1} align="center" />
          </div>
        </Card>
        <Headline text={headline} size={headSize(headline, Math.round(76 * s), W)} width={W} style={{marginTop: Math.round(34 * s), lineHeight: 1.2}} />
        <div style={{fontSize: Math.round(30 * s), lineHeight: 1.3, color: c.muted, marginTop: 12 * s}}>{subtitle}</div>
      </AbsoluteFill>
    </AbsoluteFill>
    </ThemeCtx.Provider>
  );
};
