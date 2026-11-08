import React from 'react';
import {AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {cardHeight, useTheme} from '../Video';
import {CaptionCard} from './Caption';
import {ShowcaseFrame} from './Frame';
import {PageCam} from './PageCam';
import {STAGE_W, stageHeight} from './promo.mjs';
import {XF} from './ShowcaseShort';
import type {ShowcaseBeat, ShowcaseProps} from './ShowcaseShort';

const BeatLayer: React.FC<{beat: ShowcaseBeat; index: number; stageH: number}> = ({beat, index, stageH}) => {
  const c = useTheme();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const lead = index > 0 ? XF : 0;
  const t = Math.max(0, frame - lead) / fps, duration = beat.frames / fps;
  const opacity = index === 0 ? 1 : interpolate(frame, [0, XF], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const textAlpha = interpolate(t, [0, 0.12], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  if (!beat.shot || !beat.box || !beat.page) throw new Error(`beat "${beat.id}" has no shot, box or page: render it with render_showcase.py`);
  return (
    <AbsoluteFill style={{opacity}}>
      <div style={{border: `3px solid ${c.border}`, borderRadius: 24, overflow: 'hidden', background: c.card, boxShadow: c.shadow}}>
        <PageCam src={beat.asset} page={beat.page} scale={beat.imageScale ?? 1} box={beat.box} shot={beat.shot}
          progress={Math.min(1, t / duration)} stage={{w: STAGE_W, h: stageH}} />
        <CaptionCard beat={beat} textAlpha={textAlpha} />
      </div>
    </AbsoluteFill>
  );
};

export const ShowcasePromo: React.FC<ShowcaseProps> = ({headline, subtitle, category, theme, name, nameZh, tagline, taglineZh, sourceLabel, beats}) => {
  const reserve = cardHeight(beats);
  const stageH = stageHeight(reserve);
  return (
    <ShowcaseFrame headline={headline} subtitle={subtitle} category={category} theme={theme} name={name} nameZh={nameZh}
      tagline={tagline} taglineZh={taglineZh} sourceLabel={sourceLabel} zoneHeight={stageH + 3 + reserve}>
      {beats.map((b, i) => (
        <React.Fragment key={b.id}>
          <Sequence from={Math.max(0, b.startFrame - (i > 0 ? XF : 0))} durationInFrames={b.frames + (i > 0 ? XF : 0)}>
            <BeatLayer beat={b} index={i} stageH={stageH} />
          </Sequence>
          {b.audio ? (
            <Sequence from={b.startFrame} durationInFrames={b.frames}><Audio src={staticFile(b.audio)} /></Sequence>
          ) : null}
        </React.Fragment>
      ))}
    </ShowcaseFrame>
  );
};
