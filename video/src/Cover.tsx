import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {SERIF, SAFE_X, HeadlineLines, SpeakerBlock, PeopleRow, InfoCard, ThemeCtx, pickTheme, Person} from './Video';

export type CoverProps = {
  headline: string; subtitle: string; speaker: string; source: string;
  poster: string | null; talkTitle?: string; category?: string;
  speakerZh?: string; role?: string; roleZh?: string; theme?: string; people?: Person[];
};

export const InspireCover: React.FC<CoverProps> = ({headline, subtitle, speaker, speakerZh, role, roleZh, source, poster, talkTitle, category, theme, people}) => {
  const c = pickTheme(theme);
  return (
  <ThemeCtx.Provider value={c}>
  <AbsoluteFill style={{backgroundColor: c.paper, color: c.ink, padding: `150px ${SAFE_X}px 150px`,
    fontFamily: 'Arial, sans-serif', boxSizing: 'border-box'}}>
    <div style={{fontSize: 28, letterSpacing: 2, color: c.muted, marginBottom: 28}}>
      {category || 'INSPIRATION / 向上生长'}
    </div>
    <div style={{fontFamily: SERIF, fontSize: 84, lineHeight: 1.16, fontWeight: 700, letterSpacing: 2,
      }}><HeadlineLines text={headline} size={84} width={840} /></div>
    <div style={{fontSize: 38, lineHeight: 1.3, color: c.muted, marginTop: 24}}>{subtitle}</div>
    <div style={{marginTop: 56, height: 640, border: `5px solid ${c.border}`, borderRadius: 10, overflow: 'hidden',
      background: c.videoBg}}>
      {poster && <Img src={/^https?:/.test(poster) ? poster : staticFile(poster)}
        style={{width: '100%', height: '100%', objectFit: 'cover'}} />}
    </div>
    <div style={{marginTop: 'auto'}}>
      <InfoCard pad={32} radius={28}>
        {people && people.length > 1
          ? <PeopleRow people={people} scale={1.5} />
          : <SpeakerBlock speaker={speaker} speakerZh={speakerZh} role={role} roleZh={roleZh} scale={1.2} />}
        {talkTitle && <div style={{fontSize: 32, fontStyle: 'italic', marginTop: 12}}>“{talkTitle}”</div>}
        <div style={{borderTop: `3px solid ${c.cardBorder}`, marginTop: 20, paddingTop: 16, fontSize: 28, color: c.muted}}>
          {source}
        </div>
      </InfoCard>
    </div>
  </AbsoluteFill>
  </ThemeCtx.Provider>
  );
};
