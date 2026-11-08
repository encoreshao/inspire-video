import React from 'react';
import {AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {SERIF, ZhText, useTheme} from '../Video';
import {PageCam} from './PageCam';
import {PROMO_CAPTION_TOP, PROMO_SHADOW, PROMO_STAGE_TOP, PROMO_TEXT_X, PROMO_W, PROMO_X, PromoFrame} from './PromoFrame';
import {PROMO_STAGE_H, STAGE_W} from './promo.mjs';
import {XF} from './ShowcaseShort';
import type {ShowcaseBeat, ShowcaseProps} from './ShowcaseShort';
import {Statement} from './Statement';

const RADIUS = 36;
// Caption type shrinks as the sentence grows, so the longest allowed beat (100 English / 45 Chinese characters) still fits.
const captionSizes = (beat: ShowcaseBeat) => ({
  en: beat.en.length <= 60 ? 42 : beat.en.length <= 85 ? 37 : 33,
  zh: beat.zh.length <= 22 ? 40 : 35,
});

const BeatLayer: React.FC<{beat: ShowcaseBeat; index: number}> = ({beat, index}) => {
  const c = useTheme();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const lead = index > 0 ? XF : 0;
  const t = Math.max(0, frame - lead) / fps, duration = beat.frames / fps;
  const opacity = index === 0 ? 1 : interpolate(frame, [0, XF], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const textAlpha = interpolate(t, [0, 0.12], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const stage = {w: STAGE_W, h: PROMO_STAGE_H};
  const size = captionSizes(beat);
  let content: React.ReactNode;
  if (beat.shot === 'statement') {
    const text = beat.statement ?? '';
    content = <Statement text={text} units={beat.statementUnits ?? [text]} stage={stage} frame={Math.max(0, frame - lead)} />;
  } else {
    if (!beat.shot || !beat.box || !beat.page) throw new Error(`beat "${beat.id}" has no shot, box or page: render it with render_showcase.py`);
    content = <PageCam src={beat.asset} page={beat.page} scale={beat.imageScale ?? 1} box={beat.box} shot={beat.shot}
      progress={Math.min(1, t / duration)} seconds={duration} stage={stage} />;
  }
  return (
    <AbsoluteFill style={{opacity}}>
      <div style={{position: 'absolute', left: PROMO_X, top: PROMO_STAGE_TOP, width: STAGE_W, height: PROMO_STAGE_H, borderRadius: RADIUS,
        overflow: 'hidden', boxShadow: PROMO_SHADOW, background: c.card}}>
        {content}
        <div style={{position: 'absolute', inset: 0, borderRadius: RADIUS, border: `2px solid ${c.border}`, pointerEvents: 'none'}} />
      </div>
      <div style={{position: 'absolute', left: PROMO_TEXT_X, top: PROMO_CAPTION_TOP, width: PROMO_W - 2 * (PROMO_TEXT_X - PROMO_X), opacity: textAlpha, display: 'flex', flexDirection: 'column', gap: 14}}>
        <div style={{fontSize: size.en, fontWeight: 700, lineHeight: 1.25, overflowWrap: 'break-word', textWrap: 'balance' as any}}>{beat.en}</div>
        <div style={{fontFamily: SERIF, fontSize: size.zh, fontWeight: 500, lineHeight: 1.35, color: c.accent, overflowWrap: 'break-word',
          textWrap: 'balance' as any}}><ZhText text={beat.zh} units={beat.zhUnits} /></div>
      </div>
    </AbsoluteFill>
  );
};

export const ShowcasePromo: React.FC<ShowcaseProps> = ({theme, name, nameZh, tagline, sourceLabel, beats}) => (
  <PromoFrame theme={theme} name={name} nameZh={nameZh} tagline={tagline} sourceLabel={sourceLabel} beats={beats}>
    {beats.map((b, i) => (
      <React.Fragment key={b.id}>
        <Sequence from={Math.max(0, b.startFrame - (i > 0 ? XF : 0))} durationInFrames={b.frames + (i > 0 ? XF : 0)}>
          <BeatLayer beat={b} index={i} />
        </Sequence>
        {b.audio ? (
          <Sequence from={b.startFrame} durationInFrames={b.frames}><Audio src={staticFile(b.audio)} /></Sequence>
        ) : null}
      </React.Fragment>
    ))}
  </PromoFrame>
);
