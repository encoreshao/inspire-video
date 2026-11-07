import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {SERIF, HeadlineLines, SpeakerBlock, PeopleRow, InfoCard, ThemeCtx, pickTheme, Person} from './Video';
import {DEFAULT_PROFILE, panelWidth} from './layout.mjs';
import type {Profile} from './layout.mjs';

export type CoverProps = {
  headline: string; subtitle: string; speaker: string; source: string;
  poster: string | null; talkTitle?: string; category?: string;
  speakerZh?: string; role?: string; roleZh?: string; theme?: string; people?: Person[];
  profile?: Profile;
};

export const InspireCover: React.FC<CoverProps> = ({headline, subtitle, speaker, speakerZh, role, roleZh, source, poster, talkTitle, category, theme, people, profile = DEFAULT_PROFILE}) => {
  const c = pickTheme(theme);
  const k = !!profile.compact;           // compact (4:5): smaller type, the poster takes the remaining height
  const pad = k ? 80 : 150;
  const headSize = k ? 64 : 84;
  return (
  <ThemeCtx.Provider value={c}>
  <AbsoluteFill style={{backgroundColor: c.paper, color: c.ink, padding: `${pad}px ${profile.safeX}px ${pad}px`,
    fontFamily: 'Arial, sans-serif', boxSizing: 'border-box', ...(k ? {display: 'flex', flexDirection: 'column'} : {})}}>
    <div style={{fontSize: k ? 24 : 28, letterSpacing: 2, color: c.muted, marginBottom: k ? 20 : 28}}>
      {category || 'INSPIRATION / 向上生长'}
    </div>
    <div style={{fontFamily: SERIF, fontSize: headSize, lineHeight: 1.16, fontWeight: 700, letterSpacing: 2,
      }}><HeadlineLines text={headline} size={headSize} width={k ? panelWidth(profile) : 840} /></div>
    <div style={{fontSize: k ? 30 : 38, lineHeight: 1.3, color: c.muted, marginTop: k ? 16 : 24}}>{subtitle}</div>
    <div style={{marginTop: k ? 32 : 56, ...(k ? {flex: 1, minHeight: 0, marginBottom: 32} : {height: 640}),
      border: `5px solid ${c.border}`, borderRadius: 10, overflow: 'hidden', background: c.videoBg}}>
      {poster && <Img src={/^https?:/.test(poster) ? poster : staticFile(poster)}
        style={{width: '100%', height: '100%', objectFit: 'cover'}} />}
    </div>
    <div style={{marginTop: 'auto'}}>
      <InfoCard pad={k ? 24 : 32} radius={28}>
        {people && people.length > 1
          ? <PeopleRow people={people} scale={k ? 1.2 : 1.5} />
          : <SpeakerBlock speaker={speaker} speakerZh={speakerZh} role={role} roleZh={roleZh} scale={k ? 1 : 1.2} />}
        {talkTitle && <div style={{fontSize: k ? 26 : 32, fontStyle: 'italic', marginTop: 12}}>“{talkTitle}”</div>}
        <div style={{borderTop: `3px solid ${c.cardBorder}`, marginTop: k ? 14 : 20, paddingTop: k ? 12 : 16, fontSize: k ? 22 : 28, color: c.muted}}>
          {source}
        </div>
      </InfoCard>
    </div>
  </AbsoluteFill>
  </ThemeCtx.Provider>
  );
};
