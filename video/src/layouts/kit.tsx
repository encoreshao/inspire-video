import React from 'react';
import {Img, OffthreadVideo, staticFile} from 'remotion';
import {HeadlineLines, SERIF, ZhText, useTheme} from '../Video';
import type {Cue, Person} from '../Video';

export const resolve = (p: string) => (/^https?:/.test(p) ? p : staticFile(p));

// Largest headline size up to `target` at which the headline fits in two lines of `width`.
export const headSize = (text: string, target: number, width: number) =>
  Math.max(30, Math.min(target, Math.floor((2 * width) / Math.max(1, text.length)) - 2));

// Cover text starts inside the middle 3:4 band, which the platforms' profile grid keeps when it crops a 9:16 cover.
export const coverBandTop = (p: {width: number; height: number; titleTop: number}) =>
  Math.max(p.titleTop, Math.round((p.height - (p.width * 4) / 3) / 2) + 60);
export const coverBandBottom = (p: {width: number; height: number; safeBottom: number}) =>
  Math.min(p.height - p.safeBottom, Math.round((p.height + (p.width * 4) / 3) / 2) - 60);

export const Headline:React.FC<{text: string; size: number; width: number; style?: React.CSSProperties}> = ({text, size, width, style}) => (
  <div style={{fontFamily: SERIF, fontSize: size, lineHeight: 1.3, fontWeight: 700, letterSpacing: 1, ...style}}>
    <HeadlineLines text={text} size={size} width={width} />
  </div>
);

// The footage in a video layout, or the poster photo on a cover.
export type Media = {clip?: string | null; poster?: string | null; videoFit?: 'cover' | 'contain'; cropX?: number; cropY?: number};

export const Clip: React.FC<{media: Media; muted?: boolean; style?: React.CSSProperties}> = ({media, muted, style}) => {
  const css: React.CSSProperties = {width: '100%', height: '100%', objectFit: media.videoFit ?? 'cover',
    objectPosition: `${(media.cropX ?? 0.5) * 100}% ${(media.cropY ?? 0.5) * 100}%`, display: 'block', ...style};
  if (media.clip) return <OffthreadVideo src={resolve(media.clip)} muted={muted} style={css} />;
  if (media.poster) return <Img src={resolve(media.poster)} style={{...css, objectFit: 'cover'}} />;
  return <div style={{...css, background: 'linear-gradient(135deg, #2a2420, #121010)'}} />;
};

// English line then Chinese line of the current cue, in the sizes `fit` picked.
export const CaptionText: React.FC<{cue: Cue | null; alpha: number; size: {en: number; zh: number}; align?: 'left' | 'center';
  enColor?: string; zhColor?: string; shadow?: string}> = ({cue, alpha, size, align = 'center', enColor, zhColor, shadow}) => {
  const c = useTheme();
  if (!cue) return null;
  return (
    <div style={{opacity: alpha, display: 'flex', flexDirection: 'column', gap: 8, textAlign: align, textShadow: shadow}}>
      <div style={{fontSize: size.en, fontWeight: 600, lineHeight: 1.28, color: enColor ?? c.ink, overflowWrap: 'break-word', textWrap: 'balance' as any}}>{cue.en}</div>
      <div style={{fontFamily: SERIF, fontSize: size.zh, fontWeight: 600, lineHeight: 1.38, color: zhColor ?? c.accent,
        overflowWrap: 'break-word', textWrap: 'balance' as any}}><ZhText text={cue.zh} units={cue.zhUnits} /></div>
    </div>
  );
};

export type CreditInfo = {speaker: string; speakerZh?: string; role?: string; roleZh?: string; source: string; talkTitle?: string; people?: Person[]};

// Compact speaker credit: name (English and Chinese), role and source. With several people the names are listed
// and the current speaker is highlighted.
export const Credit: React.FC<{info: CreditInfo; activeId?: string; scale: number; align?: 'left' | 'center'; withTalk?: boolean;
  shadow?: string}> = ({info, activeId, scale: s, align = 'left', withTalk = false, shadow}) => {
  const c = useTheme();
  const group: Person[] = info.people && info.people.length > 1 ? info.people : [];
  const row = {display: 'flex', flexWrap: 'wrap' as const, gap: `0 ${16 * s}px`, alignItems: 'baseline',
    justifyContent: align === 'center' ? 'center' : 'flex-start'};
  return (
    <div style={{textAlign: align, textShadow: shadow}}>
      {group.length
        ? <div style={row}>{group.map((p) => {
            const on = !activeId || p.id === activeId;
            return <span key={p.id} style={{fontSize: 27 * s, fontWeight: 700, color: on ? c.accent : c.muted, opacity: on ? 1 : 0.7}}>
              {p.name}{p.name_zh ? <span style={{fontFamily: SERIF, marginLeft: 8 * s}}>{p.name_zh}</span> : null}
            </span>;
          })}</div>
        : <div style={row}>
            <span style={{fontSize: 32 * s, fontWeight: 700, color: c.accent}}>{info.speaker}</span>
            {info.speakerZh ? <span style={{fontFamily: SERIF, fontSize: 32 * s, fontWeight: 700, color: c.accent}}>{info.speakerZh}</span> : null}
          </div>}
      {!group.length && info.role ? <div style={{fontSize: 23 * s, lineHeight: 1.3, color: c.ink, marginTop: 6 * s}}>{info.role}</div> : null}
      {!group.length && info.roleZh ? <div style={{fontFamily: SERIF, fontSize: 22 * s, lineHeight: 1.3, color: c.muted}}>{info.roleZh}</div> : null}
      {withTalk && info.talkTitle
        ? <div style={{fontSize: 22 * s, lineHeight: 1.3, color: c.ink, fontStyle: 'italic', marginTop: 8 * s}}>“{info.talkTitle}”</div> : null}
      {info.source ? <div style={{fontSize: 20 * s, lineHeight: 1.3, color: c.muted, marginTop: 8 * s, letterSpacing: 0.5}}>{info.source}</div> : null}
    </div>
  );
};

export const Progress: React.FC<{value: number; scale: number}> = ({value, scale: s}) => {
  const c = useTheme();
  return (
    <div style={{marginTop: 22 * s, height: 5, flexShrink: 0, borderRadius: 3, background: c.track}}>
      <div style={{height: '100%', borderRadius: 3, background: c.accent, width: `${value * 100}%`}} />
    </div>
  );
};
