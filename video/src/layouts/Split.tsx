import React from 'react';
import {AbsoluteFill} from 'remotion';
import {ThemeCtx, onDark, pickTheme, useCaption} from '../Video';
import type {Props} from '../Video';
import type {CoverProps} from '../Cover';
import {DEFAULT_PROFILE, cardHeight, fit, panelWidth, scaleOf} from '../layout.mjs';
import {CaptionText, Clip, Credit, Headline, Progress, coverBandBottom, coverBandTop, headSize} from './kit';

const SHADOW = '0 2px 12px rgba(0,0,0,0.7)';
const TopScrim = () => <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0.3) 32%, rgba(0,0,0,0) 55%)'}} />;

// Poster grid: footage edge to edge in the top half with the title over it, a solid theme block below
// holding left-aligned captions behind an accent rule, the credit and the progress bar.
export const SplitShort: React.FC<Props> = (props) => {
  const {headline, subtitle, category, cues, quoteEn, quoteZh, quoteZhUnits, theme, profile = DEFAULT_PROFILE} = props;
  const c = pickTheme(theme);
  const dark = onDark(c);
  const {cue, active, alpha, synced, progress} = useCaption(cues, {start: 0, end: 0, en: quoteEn, zh: quoteZh, zhUnits: quoteZhUnits});
  const s = scaleOf(profile);
  const W = panelWidth(profile);
  const H = Math.round(profile.height * 0.52);
  const limits = {maxH: profile.compact ? 210 : 290, maxEn: 34, minEn: 26, padX: 30, zhOffset: 4};
  const reserve = synced ? cardHeight(cues!, W, limits) : Math.round(170 * s);
  const size = cue ? fit(cue, W, limits) : {en: 32, zh: 36};
  const head = headSize(headline, Math.round(48 * s), W);
  return (
    <ThemeCtx.Provider value={c}>
    <AbsoluteFill style={{background: c.paper, color: c.ink, fontFamily: 'Arial, sans-serif'}}>
      <div style={{position: 'absolute', top: 0, left: 0, width: profile.width, height: H, overflow: 'hidden', background: c.videoBg}}>
        <Clip media={{...props, videoFit: 'cover'}} />
        <TopScrim />
      </div>
      <div style={{position: 'absolute', top: H, left: 0, width: profile.width, height: 6, background: c.accent}} />
      <div style={{position: 'absolute', top: profile.titleTop, left: profile.safeX, width: W, color: dark.ink, textShadow: SHADOW}}>
        <div style={{fontSize: Math.round(22 * s), letterSpacing: 3, color: dark.accent, fontWeight: 700, marginBottom: Math.round(14 * s)}}>
          {category || 'INSPIRATION / 向上生长'}
        </div>
        <Headline text={headline} size={head} width={W} />
        <div style={{fontSize: Math.round(30 * s), lineHeight: 1.25, fontWeight: 600, color: dark.muted, marginTop: Math.round(8 * s)}}>{subtitle}</div>
      </div>
      <div style={{position: 'absolute', top: H + Math.round(44 * s), bottom: profile.safeBottom, left: profile.safeX, width: W,
        display: 'flex', flexDirection: 'column'}}>
        <div style={{height: reserve, flexShrink: 0, borderLeft: `6px solid ${c.accent}`, paddingLeft: 24}}>
          <CaptionText cue={cue} alpha={alpha} size={size} align="left" zhColor={c.accent} />
        </div>
        <div style={{flex: 1}} />
        <div style={{flexShrink: 0}}>
          <Credit info={props} activeId={active?.speaker} scale={s * 0.9} />
          <Progress value={progress} scale={s} />
        </div>
      </div>
    </AbsoluteFill>
    </ThemeCtx.Provider>
  );
};

export const SplitCover: React.FC<CoverProps> = (props) => {
  const {headline, subtitle, category, theme, profile = DEFAULT_PROFILE} = props;
  const c = pickTheme(theme);
  const s = scaleOf(profile);
  const W = panelWidth(profile);
  const H = Math.round(profile.height * (profile.compact ? 0.5 : 0.54));
  const head = headSize(headline, Math.round(78 * s), W);
  return (
    <ThemeCtx.Provider value={c}>
    <AbsoluteFill style={{background: c.paper, color: c.ink, fontFamily: 'Arial, sans-serif'}}>
      <div style={{position: 'absolute', top: 0, left: 0, width: profile.width, height: H, overflow: 'hidden', background: c.videoBg}}>
        <Clip media={props} />
      </div>
      <div style={{position: 'absolute', top: H, left: 0, width: profile.width, height: 8, background: c.accent}} />
      <div style={{position: 'absolute', top: Math.max(coverBandTop(profile), Math.round(H * 0.16)), left: profile.safeX}}>
        <div style={{display: 'inline-block', fontSize: Math.round(26 * s), letterSpacing: 3, fontWeight: 700, color: '#17120F',
          background: c.bright, borderRadius: 999, padding: `${8 * s}px ${22 * s}px`}}>{category || 'INSPIRATION / 向上生长'}</div>
      </div>
      <div style={{position: 'absolute', top: H + Math.round(48 * s), bottom: profile.height - coverBandBottom(profile), left: profile.safeX, width: W,
        display: 'flex', flexDirection: 'column'}}>
        <Headline text={headline} size={head} width={W} style={{lineHeight: 1.18}} />
        <div style={{fontSize: Math.round(32 * s), lineHeight: 1.3, color: c.muted, marginTop: 14 * s}}>{subtitle}</div>
        <div style={{flex: 1}} />
        <Credit info={{...props, role: '', roleZh: '', source: ''}} scale={s * 1.1} />
      </div>
    </AbsoluteFill>
    </ThemeCtx.Provider>
  );
};
