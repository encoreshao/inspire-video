import React from 'react';
import {AbsoluteFill} from 'remotion';
import {HeadlineLines, InfoCard, SAFE_X, SERIF, SpeakerBlock, ThemeCtx, pickTheme} from '../Video';
import {DeviceFrame} from './DeviceFrame';
import {PromoCover} from './PromoCover';
import type {ShowcaseBeat} from './ShowcaseShort';

export type ShowcaseCoverProps = {headline: string; subtitle: string; category?: string; theme?: string; name: string; nameZh?: string;
  tagline?: string; taglineZh?: string; sourceLabel: string; beat: ShowcaseBeat};

// The device style's cover (the editorial layout). A promo project (its beats carry a shot) gets its own cover.
export const ShowcaseCover: React.FC<ShowcaseCoverProps> = ({headline, subtitle, category, theme, name, nameZh, tagline, taglineZh, sourceLabel, beat}) => {
  if (beat.shot) {
    return <PromoCover headline={headline} subtitle={subtitle} category={category} theme={theme} name={name} nameZh={nameZh}
      tagline={tagline} sourceLabel={sourceLabel} beat={beat} />;
  }
  const c = pickTheme(theme);
  return (
    <ThemeCtx.Provider value={c}>
      <AbsoluteFill style={{backgroundColor: c.paper, color: c.ink, padding: `150px ${SAFE_X}px 150px`, fontFamily: 'Arial, sans-serif', boxSizing: 'border-box'}}>
        <div style={{fontSize: 28, letterSpacing: 2, color: c.muted, marginBottom: 28}}>{category || 'SHOWCASE / 项目展示'}</div>
        <div style={{fontFamily: SERIF, fontSize: 84, lineHeight: 1.16, fontWeight: 700, letterSpacing: 2}}>
          <HeadlineLines text={headline} size={84} width={840} />
        </div>
        <div style={{fontSize: 38, lineHeight: 1.3, color: c.muted, marginTop: 24}}>{subtitle}</div>
        <div style={{marginTop: 56, border: `5px solid ${c.border}`, borderRadius: 10, overflow: 'hidden'}}>
          <DeviceFrame src={beat.asset} iw={beat.iw} ih={beat.ih} focus={beat.focus} progress={0} t={0} duration={1}
            urlLabel={sourceLabel} zoneW={842} zoneH={630} />
        </div>
        <div style={{marginTop: 'auto'}}>
          <InfoCard pad={32} radius={28}>
            <SpeakerBlock speaker={name} speakerZh={nameZh} role={tagline} roleZh={taglineZh} scale={1.2} />
            <div style={{borderTop: `3px solid ${c.cardBorder}`, marginTop: 20, paddingTop: 16, fontSize: 28, color: c.muted}}>{sourceLabel}</div>
          </InfoCard>
        </div>
      </AbsoluteFill>
    </ThemeCtx.Provider>
  );
};
