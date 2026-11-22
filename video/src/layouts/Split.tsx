import React from 'react';
import {AbsoluteFill} from 'remotion';
import {ThemeCtx, pickTheme, useCaption} from '../Video';
import type {Props, Theme} from '../Video';
import type {CoverProps} from '../Cover';
import {DEFAULT_PROFILE, cardHeight, fit, panelWidth, scaleOf} from '../layout.mjs';
import {CaptionText, Clip, Credit, Headline, Progress, coverBandBottom, coverBandTop, headSize, readableOn} from './kit';

// The theme recolored for text on the solid accent block: every text color is the one that reads on the accent.
const onBlock = (c: Theme): Theme => {
  const fg = readableOn(c.accent);
  const soft = fg === '#FFF8EF' ? 'rgba(255,248,239,' : 'rgba(29,24,20,';
  return {...c, paper: c.accent, ink: fg, accent: fg, muted: `${soft}0.78)`, border: `${soft}0.4)`, cardBorder: `${soft}0.3)`, track: `${soft}0.25)`};
};

const Tag: React.FC<{text: string; c: Theme; size: number}> = ({text, c, size}) => (
  <div style={{display: 'inline-block', fontSize: size, letterSpacing: 3, fontWeight: 700, color: c.ink, background: c.paper,
    padding: `${size * 0.35}px ${size * 0.8}px`}}>{text}</div>
);

// Two-block poster: the footage fills the top half edge to edge with nothing over it but a tag; the bottom half is a
// solid block in the theme accent that carries the headline, captions and credit.
export const SplitShort: React.FC<Props> = (props) => {
  const {headline, subtitle, category, cues, quoteEn, quoteZh, quoteZhUnits, theme, profile = DEFAULT_PROFILE} = props;
  const c = onBlock(pickTheme(theme));
  const {cue, active, alpha, synced, progress} = useCaption(cues, {start: 0, end: 0, en: quoteEn, zh: quoteZh, zhUnits: quoteZhUnits});
  const s = scaleOf(profile);
  const W = panelWidth(profile);
  const H = Math.round(profile.height * 0.46);
  const limits = {maxH: profile.compact ? 200 : 270, maxEn: 34, minEn: 26, padX: 0, zhOffset: 4};
  const reserve = synced ? cardHeight(cues!, W, limits) : Math.round(160 * s);
  const size = cue ? fit(cue, W, limits) : {en: 32, zh: 36};
  return (
    <ThemeCtx.Provider value={c}>
    <AbsoluteFill style={{background: c.paper, color: c.ink, fontFamily: 'Arial, sans-serif'}}>
      <div style={{position: 'absolute', top: 0, left: 0, width: profile.width, height: H, overflow: 'hidden', background: c.videoBg}}>
        <Clip media={{...props, videoFit: 'cover'}} />
      </div>
      <div style={{position: 'absolute', top: Math.max(profile.titleTop, Math.round(H * 0.18)), left: profile.safeX}}>
        <Tag text={category || 'INSPIRATION / 向上生长'} c={c} size={Math.round(22 * s)} />
      </div>
      <div style={{position: 'absolute', top: H + Math.round(40 * s), bottom: profile.safeBottom, left: profile.safeX, width: W,
        display: 'flex', flexDirection: 'column'}}>
        <Headline text={headline} size={headSize(headline, Math.round(50 * s), W)} width={W} style={{lineHeight: 1.22, flexShrink: 0}} />
        <div style={{fontSize: Math.round(26 * s), lineHeight: 1.3, color: c.muted, marginTop: Math.round(6 * s), flexShrink: 0}}>{subtitle}</div>
        <div style={{height: 2, background: c.border, margin: `${Math.round(24 * s)}px 0`, flexShrink: 0}} />
        <div style={{height: reserve, flexShrink: 0}}>
          <CaptionText cue={cue} alpha={alpha} size={size} align="left" zhStyle={{fontWeight: 700}} />
        </div>
        <div style={{flex: 1}} />
        <div style={{flexShrink: 0}}>
          <Credit info={{...props, roleZh: ''}} activeId={active?.speaker} scale={s * 0.85} />
          <Progress value={progress} scale={s} />
        </div>
      </div>
    </AbsoluteFill>
    </ThemeCtx.Provider>
  );
};

export const SplitCover: React.FC<CoverProps> = (props) => {
  const {headline, subtitle, category, theme, profile = DEFAULT_PROFILE} = props;
  const c = onBlock(pickTheme(theme));
  const s = scaleOf(profile);
  const W = panelWidth(profile);
  const H = Math.round(profile.height * 0.5);
  return (
    <ThemeCtx.Provider value={c}>
    <AbsoluteFill style={{background: c.paper, color: c.ink, fontFamily: 'Arial, sans-serif'}}>
      <div style={{position: 'absolute', top: 0, left: 0, width: profile.width, height: H, overflow: 'hidden', background: c.videoBg}}>
        <Clip media={props} />
      </div>
      <div style={{position: 'absolute', top: Math.max(coverBandTop(profile), Math.round(H * 0.2)), left: profile.safeX}}>
        <Tag text={category || 'INSPIRATION / 向上生长'} c={c} size={Math.round(26 * s)} />
      </div>
      <div style={{position: 'absolute', top: H + Math.round(52 * s), bottom: profile.height - coverBandBottom(profile), left: profile.safeX, width: W,
        display: 'flex', flexDirection: 'column'}}>
        <Headline text={headline} size={headSize(headline, Math.round(84 * s), W)} width={W} style={{lineHeight: 1.16, fontWeight: 900}} />
        <div style={{fontSize: Math.round(32 * s), lineHeight: 1.3, color: c.muted, marginTop: 16 * s}}>{subtitle}</div>
        <div style={{flex: 1}} />
        <Credit info={{...props, role: '', roleZh: '', source: ''}} scale={s * 1.1} />
      </div>
    </AbsoluteFill>
    </ThemeCtx.Provider>
  );
};
