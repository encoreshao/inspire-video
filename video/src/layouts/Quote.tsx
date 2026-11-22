import React from 'react';
import {AbsoluteFill} from 'remotion';
import {SERIF, ThemeCtx, pickTheme, useCaption} from '../Video';
import type {Props, Theme} from '../Video';
import type {CoverProps} from '../Cover';
import {DEFAULT_PROFILE, cardHeight, fit, panelWidth, scaleOf} from '../layout.mjs';
import type {Profile} from '../layout.mjs';
import {CaptionText, Clip, Credit, Headline, Progress, coverBandBottom, coverBandTop, headSize} from './kit';
import type {CreditInfo, Media} from './kit';

const ITALIC = 'Georgia, "Times New Roman", serif';

const Mark: React.FC<{size: number; color: string}> = ({size, color}) => (
  <div style={{fontFamily: ITALIC, fontSize: size, lineHeight: 1, height: size * 0.52, color, fontWeight: 700, marginLeft: -size * 0.06}}>“</div>
);

const Masthead: React.FC<{c: Theme; s: number; W: number; category?: string; headline: string; subtitle: string}> = ({c, s, W, category, headline, subtitle}) => (
  <div style={{flexShrink: 0, borderBottom: `3px solid ${c.ink}`, paddingBottom: Math.round(14 * s)}}>
    <div style={{fontSize: Math.round(21 * s), letterSpacing: 3, color: c.accent, fontWeight: 700}}>{category || 'INSPIRATION / 向上生长'}</div>
    <div style={{fontFamily: SERIF, fontSize: headSize(headline, Math.round(34 * s), W), fontWeight: 700, lineHeight: 1.3, marginTop: Math.round(8 * s)}}>{headline}</div>
    <div style={{fontFamily: ITALIC, fontStyle: 'italic', fontSize: Math.round(24 * s), color: c.muted, marginTop: Math.round(4 * s)}}>{subtitle}</div>
  </div>
);

// Square video thumbnail beside the byline, like the author row of a quote card.
const Byline: React.FC<{media: Media; info: CreditInfo; activeId?: string; s: number; thumb: number; profile: Profile; withTalk?: boolean}> = ({
  media, info, activeId, s, thumb, withTalk = true,
}) => (
  <div style={{display: 'flex', alignItems: 'center', gap: Math.round(30 * s)}}>
    <div style={{width: thumb, height: thumb, flexShrink: 0, borderRadius: 26, overflow: 'hidden', background: '#111',
      boxShadow: '0 18px 40px rgba(40,25,15,0.28)'}}>
      <Clip media={{...media, videoFit: 'cover'}} zoom={1.35} />
    </div>
    <div style={{minWidth: 0}}><Credit info={info} activeId={activeId} scale={s} withTalk={withTalk} /></div>
  </div>
);

// Text-first quote card: a masthead, the caption set very large under a big quotation mark, and the footage
// reduced to a square thumbnail next to the speaker byline.
export const QuoteShort: React.FC<Props> = (props) => {
  const {headline, subtitle, category, cues, quoteEn, quoteZh, quoteZhUnits, theme, profile = DEFAULT_PROFILE} = props;
  const c = pickTheme(theme);
  const {cue, active, alpha, synced, progress} = useCaption(cues, {start: 0, end: 0, en: quoteEn, zh: quoteZh, zhUnits: quoteZhUnits});
  const s = scaleOf(profile);
  const W = panelWidth(profile);
  const limits = {maxH: profile.compact ? 400 : 600, maxEn: 48, minEn: 32, padX: 0, zhOffset: 4};
  const reserve = synced ? cardHeight(cues!, W, limits) : Math.round(300 * s);
  const size = cue ? fit(cue, W, limits) : {en: 44, zh: 48};
  return (
    <ThemeCtx.Provider value={c}>
    <AbsoluteFill style={{background: c.paper, color: c.ink, fontFamily: 'Arial, sans-serif',
      padding: `${profile.titleTop}px ${profile.safeX}px ${profile.safeBottom}px`, boxSizing: 'border-box', display: 'flex', flexDirection: 'column'}}>
      <Masthead c={c} s={s} W={W} category={category} headline={headline} subtitle={subtitle} />
      <div style={{flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', justifyContent: 'center'}}>
        <Mark size={Math.round(240 * s)} color={c.accent} />
        <div style={{height: reserve, marginTop: Math.round(10 * s)}}>
          <CaptionText cue={cue} alpha={alpha} size={size} align="left" gap={Math.round(18 * s)}
            enStyle={{fontFamily: ITALIC, fontStyle: 'italic', fontWeight: 400, lineHeight: 1.3}}
            zhColor={c.accent} zhStyle={{fontWeight: 700, lineHeight: 1.4}} />
        </div>
      </div>
      <div style={{flexShrink: 0}}>
        <Byline media={props} info={props} activeId={active?.speaker} s={s * 0.9} thumb={Math.round((profile.compact ? 200 : 260) * s)} profile={profile} />
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
  const head = headSize(headline, Math.round(100 * s), W);
  return (
    <ThemeCtx.Provider value={c}>
    <AbsoluteFill style={{background: c.paper, color: c.ink, fontFamily: 'Arial, sans-serif',
      padding: `${coverBandTop(profile)}px ${profile.safeX}px ${profile.height - coverBandBottom(profile)}px`, boxSizing: 'border-box',
      display: 'flex', flexDirection: 'column'}}>
      <div style={{fontSize: Math.round(26 * s), letterSpacing: 3, color: c.accent, fontWeight: 700, borderBottom: `3px solid ${c.ink}`,
        paddingBottom: Math.round(14 * s)}}>{category || 'INSPIRATION / 向上生长'}</div>
      <div style={{flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', justifyContent: 'center'}}>
        <Mark size={Math.round(300 * s)} color={c.accent} />
        <Headline text={headline} size={head} width={W} style={{fontWeight: 900, lineHeight: 1.22, letterSpacing: 2, marginTop: Math.round(12 * s)}} />
        <div style={{fontFamily: ITALIC, fontStyle: 'italic', fontSize: Math.round(36 * s), lineHeight: 1.3, color: c.muted, marginTop: Math.round(24 * s)}}>{subtitle}</div>
      </div>
      <Byline media={props} info={{...props, roleZh: '', source: ''}} s={s * 1.05} thumb={Math.round((profile.compact ? 220 : 280) * s)} profile={profile} withTalk={false} />
    </AbsoluteFill>
    </ThemeCtx.Provider>
  );
};
