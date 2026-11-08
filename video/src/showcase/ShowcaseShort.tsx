import React from 'react';
import {AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {cardHeight, useTheme} from '../Video';
import {CaptionCard} from './Caption';
import {DeviceFrame} from './DeviceFrame';
import type {Focus} from './DeviceFrame';
import {ShowcaseFrame} from './Frame';

export type ShowcaseBeat = {id: string; en: string; zh: string; zhUnits?: string[]; asset: string; iw: number; ih: number; focus: Focus;
  callout?: string; audio?: string | null; startFrame: number; frames: number;
  // promo style only
  shot?: string; box?: {x: number; y: number; w: number; h: number}; page?: {w: number; h: number}; imageScale?: number};
export type ShowcaseProps = {headline: string; subtitle: string; category?: string; theme?: string; name: string; nameZh?: string;
  tagline?: string; taglineZh?: string; sourceLabel: string; beats: ShowcaseBeat[]; durationSeconds: number};

export const XF = 9;          // cross-fade frames between beats
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
  return (
    <AbsoluteFill style={{opacity}}>
      <div style={{border: `3px solid ${c.border}`, borderRadius: 24, overflow: 'hidden', background: c.card, boxShadow: c.shadow}}>
        <div style={{height: DEV_H, position: 'relative'}}>
          <DeviceFrame src={beat.asset} iw={beat.iw} ih={beat.ih} focus={beat.focus} progress={Math.min(1, t / duration)} t={t}
            duration={duration} callout={beat.callout} urlLabel={sourceLabel} zoneH={DEV_H} />
        </div>
        <CaptionCard beat={beat} textAlpha={textAlpha} />
      </div>
    </AbsoluteFill>
  );
};

export const ShowcaseShort: React.FC<ShowcaseProps> = ({headline, subtitle, category, theme, name, nameZh, tagline, taglineZh, sourceLabel, beats}) => {
  const reserve = cardHeight(beats);
  return (
    <ShowcaseFrame headline={headline} subtitle={subtitle} category={category} theme={theme} name={name} nameZh={nameZh}
      tagline={tagline} taglineZh={taglineZh} sourceLabel={sourceLabel} zoneHeight={DEV_H + 3 + reserve}>
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
    </ShowcaseFrame>
  );
};
