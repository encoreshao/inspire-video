import React from 'react';
import {AbsoluteFill} from 'remotion';
import {SERIF, ThemeCtx, pickTheme, useCaption} from '../Video';
import type {Props} from '../Video';
import type {CoverProps} from '../Cover';
import {DEFAULT_PROFILE, cardHeight, fit, panelWidth, scaleOf} from '../layout.mjs';
import {CaptionText, Clip, Credit, Headline, Progress, coverBandBottom, coverBandTop, headSize} from './kit';

const Mark: React.FC<{size: number; color: string}> = ({size, color}) => (
  <div style={{fontFamily: SERIF, fontSize: size, lineHeight: 0.8, height: size * 0.5, color, fontWeight: 700}}>“</div>
);

// Editorial pull quote: a smaller framed video on top, the caption set large below it, a byline at the bottom.
export const QuoteShort: React.FC<Props> = (props) => {
  const {headline, subtitle, category, cues, quoteEn, quoteZh, quoteZhUnits, theme, profile = DEFAULT_PROFILE} = props;
  const c = pickTheme(theme);
  const {cue, active, alpha, synced, progress} = useCaption(cues, {start: 0, end: 0, en: quoteEn, zh: quoteZh, zhUnits: quoteZhUnits});
  const s = scaleOf(profile);
  const W = panelWidth(profile);
  const limits = {maxH: profile.compact ? 230 : 330, maxEn: 36, minEn: 28, padX: 0, zhOffset: 8};
  const reserve = synced ? cardHeight(cues!, W, limits) : Math.round(190 * s);
  const size = cue ? fit(cue, W, limits) : {en: 34, zh: 42};
  const head = headSize(headline, Math.round(40 * s), W);
  return (
    <ThemeCtx.Provider value={c}>
    <AbsoluteFill style={{background: c.paper, color: c.ink, fontFamily: 'Arial, sans-serif',
      padding: `${profile.titleTop}px ${profile.safeX}px ${profile.safeBottom}px`, boxSizing: 'border-box', display: 'flex', flexDirection: 'column'}}>
      <div style={{flexShrink: 0, fontSize: Math.round(21 * s), letterSpacing: 2, color: c.muted, borderBottom: `2px solid ${c.ink}`,
        paddingBottom: Math.round(10 * s)}}>
        {category || 'INSPIRATION / 向上生长'}
      </div>
      <Headline text={headline} size={head} width={W} style={{marginTop: Math.round(18 * s), flexShrink: 0}} />
      <div style={{fontSize: Math.round(28 * s), lineHeight: 1.25, color: c.muted, marginTop: Math.round(4 * s), flexShrink: 0}}>{subtitle}</div>
      <div style={{flex: `0 1 ${Math.round(W * 9 / 16)}px`, minHeight: 0, marginTop: Math.round(26 * s), borderRadius: 20, overflow: 'hidden',
        background: c.videoBg, boxShadow: c.shadow}}>
        <Clip media={props} />
      </div>
      <div style={{flexShrink: 0, marginTop: Math.round(30 * s)}}>
        <Mark size={Math.round(130 * s)} color={c.accent} />
        <div style={{height: reserve, marginTop: Math.round(8 * s)}}>
          <CaptionText cue={cue} alpha={alpha} size={size} align="left" />
        </div>
      </div>
      <div style={{flex: 1}} />
      <div style={{flexShrink: 0}}>
        <div style={{width: 64 * s, height: 4, background: c.accent, marginBottom: Math.round(14 * s)}} />
        <Credit info={props} activeId={active?.speaker} scale={s * 0.9} withTalk />
        <Progress value={progress} scale={s} />
      </div>
    </AbsoluteFill>
    </ThemeCtx.Provider>
  );
};

export const QuoteCover: React.FC<CoverProps> = (props) => {
  const {headline, subtitle, category, theme, profile = DEFAULT_PROFILE} = props;
  const c = pickTheme(theme);
  const s = scaleOf(profile);
  const W = panelWidth(profile);
  const head = headSize(headline, Math.round(80 * s), W);
  return (
    <ThemeCtx.Provider value={c}>
    <AbsoluteFill style={{background: c.paper, color: c.ink, fontFamily: 'Arial, sans-serif',
      padding: `${coverBandTop(profile)}px ${profile.safeX}px ${profile.height - coverBandBottom(profile)}px`, boxSizing: 'border-box', display: 'flex', flexDirection: 'column'}}>
      <div style={{fontSize: Math.round(24 * s), letterSpacing: 2, color: c.muted, borderBottom: `2px solid ${c.ink}`, paddingBottom: 12 * s}}>
        {category || 'INSPIRATION / 向上生长'}
      </div>
      <div style={{flex: 1, minHeight: 0, marginTop: Math.round(36 * s), borderRadius: 24, overflow: 'hidden',
        background: c.videoBg, boxShadow: c.shadow}}>
        <Clip media={props} />
      </div>
      <div style={{marginTop: Math.round(40 * s)}}><Mark size={Math.round(150 * s)} color={c.accent} /></div>
      <Headline text={headline} size={head} width={W} style={{marginTop: 18 * s, lineHeight: 1.2}} />
      <div style={{fontSize: Math.round(32 * s), lineHeight: 1.3, color: c.muted, marginTop: 14 * s}}>{subtitle}</div>
      <div style={{marginTop: Math.round(30 * s)}}><Credit info={{...props, role: '', roleZh: '', source: ''}} scale={s * 1.1} /></div>
    </AbsoluteFill>
    </ThemeCtx.Provider>
  );
};
