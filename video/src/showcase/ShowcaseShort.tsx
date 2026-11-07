import React from 'react';
import {AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {CARD_PAD_Y, Divider, HeadlineLines, InfoCard, LINE_GAP, PANEL_W, SAFE_X, SERIF, SpeakerBlock, TITLE_TOP, ThemeCtx, cardHeight, fit, pickTheme, useTheme} from '../Video';
import {DeviceFrame} from './DeviceFrame';
import type {Focus} from './DeviceFrame';

export type ShowcaseBeat = {id: string; en: string; zh: string; asset: string; iw: number; ih: number; focus: Focus;
  callout?: string; audio?: string | null; startFrame: number; frames: number};
export type ShowcaseProps = {headline: string; subtitle: string; category?: string; theme?: string; name: string; nameZh?: string;
  tagline?: string; taglineZh?: string; sourceLabel: string; beats: ShowcaseBeat[]; durationSeconds: number};

const XF = 9;          // cross-fade frames between beats
const HEAD = 42;       // headline and subtitle size, as in the speaker layout
const DEV_H = 488;     // device zone height = the speaker layout's video window

const BeatLayer: React.FC<{beat: ShowcaseBeat; index: number; sourceLabel: string}> = ({beat, index, sourceLabel}) => {
  const c = useTheme();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const lead = index > 0 ? XF : 0;
  const local = frame - lead;
  const t = Math.max(0, local) / fps, duration = beat.frames / fps;
  const opacity = index === 0 ? 1 : interpolate(frame, [0, XF], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const textAlpha = interpolate(t, [0, 0.12], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const size = fit(beat);
  return (
    <AbsoluteFill style={{opacity}}>
      <div style={{border: `3px solid ${c.border}`, borderRadius: 24, overflow: 'hidden', background: c.card, boxShadow: c.shadow}}>
        <div style={{height: DEV_H, position: 'relative'}}>
          <DeviceFrame src={beat.asset} iw={beat.iw} ih={beat.ih} focus={beat.focus} progress={Math.min(1, t / duration)} t={t}
            duration={duration} callout={beat.callout} urlLabel={sourceLabel} zoneH={DEV_H} />
        </div>
        <div style={{borderTop: `3px solid ${c.border}`, background: c.card, padding: `${CARD_PAD_Y}px 32px`, textAlign: 'center',
          minHeight: 64, boxSizing: 'content-box'}}>
          <div style={{opacity: textAlpha, display: 'flex', flexDirection: 'column', gap: 6}}>
            <div style={{fontSize: size.en, fontWeight: 600, lineHeight: 1.28, overflowWrap: 'break-word', textWrap: 'balance' as any}}>{beat.en}</div>
            <div style={{fontFamily: SERIF, fontSize: size.zh, fontWeight: 500, lineHeight: 1.38, color: c.accent,
              overflowWrap: 'break-word', textWrap: 'balance' as any}}>{beat.zh}</div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const ShowcaseShort: React.FC<ShowcaseProps> = ({headline, subtitle, category, theme, name, nameZh, tagline, taglineZh, sourceLabel, beats}) => {
  const c = pickTheme(theme);
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const fadeOut = interpolate(frame, [durationInFrames - 10, durationInFrames], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const reserve = cardHeight(beats);
  return (
    <ThemeCtx.Provider value={c}>
      <AbsoluteFill style={{opacity: fadeOut, backgroundColor: c.paper, color: c.ink, padding: `${TITLE_TOP}px ${SAFE_X}px 0`,
        display: 'flex', flexDirection: 'column', justifyContent: 'flex-start', fontFamily: 'Arial, sans-serif', boxSizing: 'border-box'}}>
        <div style={{flexShrink: 0, display: 'flex', flexDirection: 'column'}}>
          <div style={{fontSize: 22, letterSpacing: 1.5, color: c.muted, marginBottom: 16}}>{category || 'SHOWCASE / 项目展示'}</div>
          <div style={{fontFamily: SERIF, fontSize: HEAD, lineHeight: 1.3, fontWeight: 700, letterSpacing: 1}}>
            <HeadlineLines text={headline} size={HEAD} width={PANEL_W} />
          </div>
          <div style={{fontSize: HEAD, lineHeight: 1.25, fontWeight: 600, color: c.muted, marginTop: 8}}>{subtitle}</div>
        </div>
        <Divider />
        <div style={{marginTop: LINE_GAP, height: DEV_H + 3 + reserve, flexShrink: 0, position: 'relative'}}>
          {beats.map((b, i) => (
            <React.Fragment key={b.id}>
              <Sequence from={Math.max(0, b.startFrame - (i > 0 ? XF : 0))} durationInFrames={b.frames + (i > 0 ? XF : 0)}>
                <BeatLayer beat={b} index={i} sourceLabel={sourceLabel} />
              </Sequence>
              {b.audio ? (
                <Sequence from={b.startFrame} durationInFrames={b.frames}><Audio src={staticFile(b.audio)} /></Sequence>
              ) : null}
            </React.Fragment>
          ))}
        </div>
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
