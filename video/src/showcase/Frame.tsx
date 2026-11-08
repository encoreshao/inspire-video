import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {Divider, HeadlineLines, InfoCard, LINE_GAP, PANEL_W, SAFE_X, SERIF, SpeakerBlock, TITLE_TOP, ThemeCtx, pickTheme} from '../Video';

export const HEAD = 42;       // headline and subtitle size, as in the speaker layout

export type FrameProps = {
  headline: string; subtitle: string; category?: string; theme?: string; name: string; nameZh?: string;
  tagline?: string; taglineZh?: string; sourceLabel: string;
  zoneHeight: number;          // height of the zone between the two dividers (the stage, its borders and the caption card)
  children: React.ReactNode;
};

// The headline, the zone for the beats, the info card and the progress bar: everything around the beats.
export const ShowcaseFrame: React.FC<FrameProps> = ({headline, subtitle, category, theme, name, nameZh, tagline, taglineZh, sourceLabel, zoneHeight, children}) => {
  const c = pickTheme(theme);
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  return (
    <ThemeCtx.Provider value={c}>
      <AbsoluteFill style={{backgroundColor: c.paper, color: c.ink, padding: `${TITLE_TOP}px ${SAFE_X}px 0`,
        display: 'flex', flexDirection: 'column', justifyContent: 'flex-start', fontFamily: 'Arial, sans-serif', boxSizing: 'border-box'}}>
        <div style={{flexShrink: 0, display: 'flex', flexDirection: 'column'}}>
          <div style={{fontSize: 22, letterSpacing: 1.5, color: c.muted, marginBottom: 16}}>{category || 'SHOWCASE / 项目展示'}</div>
          <div style={{fontFamily: SERIF, fontSize: HEAD, lineHeight: 1.3, fontWeight: 700, letterSpacing: 1}}>
            <HeadlineLines text={headline} size={HEAD} width={PANEL_W} />
          </div>
          <div style={{fontSize: HEAD, lineHeight: 1.25, fontWeight: 600, color: c.muted, marginTop: 8}}>{subtitle}</div>
        </div>
        <Divider />
        <div style={{marginTop: LINE_GAP, height: zoneHeight, flexShrink: 0, position: 'relative'}}>{children}</div>
        <Divider />
        <div style={{marginTop: 20, flexShrink: 0, display: 'flex', flexDirection: 'column'}}>
          <InfoCard pad={14}>
            <SpeakerBlock speaker={name} speakerZh={nameZh} role={tagline} roleZh={taglineZh} scale={1.0} />
            <div style={{borderTop: `2px solid ${c.cardBorder}`, marginTop: 12, paddingTop: 10, color: c.muted, fontSize: 22, lineHeight: 1.3}}>
              {sourceLabel}
            </div>
          </InfoCard>
          <div style={{marginTop: 24, height: 6, flexShrink: 0, borderRadius: 3, background: c.track}}>
            <div style={{height: '100%', borderRadius: 3, background: c.accent, width: `${Math.min(100, (frame / durationInFrames) * 100)}%`}} />
          </div>
        </div>
      </AbsoluteFill>
    </ThemeCtx.Provider>
  );
};
