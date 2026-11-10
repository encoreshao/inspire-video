import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {SERIF, HeadlineLines, ThemeCtx, pickTheme, Person} from './Video';
import {DEFAULT_PROFILE, panelWidth} from './layout.mjs';
import type {Profile} from './layout.mjs';
import {CoverBold} from './CoverBold';

export type CoverProps = {
  headline: string; subtitle: string; speaker: string; source: string;
  poster: string | null; talkTitle?: string; category?: string;
  speakerZh?: string; role?: string; roleZh?: string; theme?: string; people?: Person[];
  profile?: Profile; variant?: 'classic' | 'split' | 'blur';
};

export const InspireCover: React.FC<CoverProps> = ({headline, subtitle, speaker, speakerZh, role, roleZh, source, poster, talkTitle, category, theme, people, profile = DEFAULT_PROFILE, variant = 'split'}) => {
  if (variant !== 'classic') return <CoverBold headline={headline} subtitle={subtitle} speaker={speaker} speakerZh={speakerZh} source={source} poster={poster}
    category={category} theme={theme} profile={profile} variant={variant} />;
  const c = pickTheme(theme);
  const k = !!profile.compact;           // compact (4:5, 3:4): smaller type
  const pad = k ? 80 : 150;
  const headSize = k ? 56 : 72;
  const name = [speaker, speakerZh].filter((x, i) => x && (i === 0 || x !== speaker)).join('  ');
  const names = people && people.length > 1 ? people.map((p) => p.name).join(' · ') : name;
  return (
  <ThemeCtx.Provider value={c}>
  <AbsoluteFill style={{backgroundColor: c.paper, color: c.ink, padding: `${pad}px ${profile.safeX}px ${pad}px`,
    fontFamily: 'Arial, sans-serif', boxSizing: 'border-box', display: 'flex', flexDirection: 'column', justifyContent: 'center'}}>
    <div style={{fontSize: k ? 24 : 28, letterSpacing: 2, color: c.muted, marginBottom: k ? 20 : 28}}>
      {category || 'INSPIRATION / 向上生长'}
    </div>
    <div style={{fontFamily: SERIF, fontSize: headSize, lineHeight: 1.16, fontWeight: 700, letterSpacing: 2,
      }}><HeadlineLines text={headline} size={headSize} width={k ? panelWidth(profile) : 840} /></div>
    <div style={{fontSize: k ? 28 : 34, lineHeight: 1.3, color: c.muted, marginTop: k ? 16 : 24}}>{subtitle}</div>
    <div style={{marginTop: k ? 32 : 48, height: k ? 560 : 640, flexShrink: 0,
      border: `5px solid ${c.border}`, borderRadius: 10, overflow: 'hidden', background: c.videoBg}}>
      {poster && <Img src={/^https?:/.test(poster) ? poster : staticFile(poster)}
        style={{width: '100%', height: '100%', objectFit: 'cover'}} />}
    </div>
    {names && <div style={{fontSize: k ? 30 : 36, fontWeight: 700, color: c.accent, marginTop: k ? 24 : 32}}>{names}</div>}
  </AbsoluteFill>
  </ThemeCtx.Provider>
  );
};
