import React from 'react';
import {AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {SERIF, ZhText, useTheme} from '../Video';
import {PageCam} from './PageCam';
import {PROMO_CAPTION_TOP, PROMO_STAGE_TOP, PROMO_TEXT_X, PROMO_W, PROMO_X, PromoFrame} from './PromoFrame';
import {PROMO_STAGE_H, STAGE_W} from './promo.mjs';
import type {ShowcaseBeat, ShowcaseProps} from './ShowcaseShort';
import {Statement} from './Statement';
import {captionAlpha, incoming, incomingFx, labelAlpha, leadsFor, outgoing, outgoingFx, topicChanged, transitionKind} from './transitions.mjs';

const RADIUS = 36;
// Caption type shrinks as the sentence grows, so the longest allowed beat (100 English / 45 Chinese characters) still fits.
const captionSizes = (beat: ShowcaseBeat) => ({
  en: beat.en.length <= 60 ? 42 : beat.en.length <= 85 ? 37 : 33,
  zh: beat.zh.length <= 22 ? 40 : 35,
});

// The topic label: a small pill in the stage's top-left corner, inside the safe area.
const TopicLabel: React.FC<{text: string; alpha: number}> = ({text, alpha}) => (
  <div style={{position: 'absolute', left: 28, top: 28, maxWidth: STAGE_W - 56, opacity: alpha, transform: `translateY(${(1 - alpha) * -8}px)`,
    padding: '10px 22px', borderRadius: 999, background: 'rgba(12,12,16,0.72)', color: '#fff', fontSize: 28, fontWeight: 700,
    letterSpacing: 0.5, lineHeight: 1.2, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
    boxShadow: '0 4px 14px rgba(0,0,0,0.25)'}}>{text}</div>
);

// The stage frame (card, border, shadow) is the same in every layer and never moves or fades, so a dissolve cannot show a
// seam; only the picture inside it dissolves, drifts and settles. The caption is separate: the old text leaves before
// the new text arrives.
const BeatLayer: React.FC<{beat: ShowcaseBeat; prev?: ShowcaseBeat; next?: ShowcaseBeat; transition?: string}> = ({beat, prev, next, transition}) => {
  const c = useTheme();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const lead = leadsFor(prev ? [prev, beat] : [beat])[prev ? 1 : 0];
  const nextLead = next ? leadsFor([beat, next])[1] : 0;
  const nextKind = next ? transitionKind(beat, next) : 'first';
  const kind = transitionKind(prev, beat);
  const local = frame - lead;                          // frames since this beat's startFrame (negative in its lead)
  const t = Math.max(0, local) / fps, duration = beat.frames / fps;
  const inn = incoming(frame, lead, kind);
  const outStart = lead + beat.frames - nextLead;
  const out = outgoing(frame - outStart, nextLead, nextKind);
  const fxIn = incomingFx(frame, lead, kind, transition), fxOut = outgoingFx(frame - outStart, nextLead, nextKind, transition);
  const scale = inn.scale * out.scale, dy = inn.dy + out.dy, dx = fxIn.dx + fxOut.dx, blur = Math.max(fxIn.blur, fxOut.blur);
  const text = captionAlpha(local / fps, lead + beat.frames - frame, nextLead);
  const label = beat.topic && (!prev || topicChanged(prev, beat)) ? labelAlpha(local / fps) : 0;
  const stage = {w: STAGE_W, h: PROMO_STAGE_H};
  const size = captionSizes(beat);
  let content: React.ReactNode;
  if (beat.shot === 'statement') {
    const statement = beat.statement ?? '';
    content = <Statement text={statement} units={beat.statementUnits ?? [statement]} stage={stage} frame={Math.max(0, local)}
      backdrop={beat.backdrop} facts={beat.facts} />;
  } else {
    if (!beat.shot || !beat.box || !beat.page) throw new Error(`beat "${beat.id}" has no shot, box or page: render it with render_showcase.py`);
    content = <PageCam src={beat.asset} page={beat.page} scale={beat.imageScale ?? 1} box={beat.box} shot={beat.shot}
      progress={Math.min(1, t / duration)} seconds={duration} stage={stage} />;
  }
  return (
    <AbsoluteFill>
      <div style={{position: 'absolute', left: PROMO_X, top: PROMO_STAGE_TOP, width: STAGE_W, height: PROMO_STAGE_H, borderRadius: RADIUS,
        overflow: 'hidden'}}>
        <div style={{position: 'absolute', inset: 0, opacity: fxIn.opacity ?? inn.opacity, transform: `translate(${dx}px, ${dy}px) scale(${scale})`, transformOrigin: '50% 50%',
          filter: blur > 0.2 ? `blur(${blur}px)` : undefined}}>
          {content}
        </div>
        {fxIn.flash > 0 ? <div style={{position: 'absolute', inset: 0, background: '#fff', opacity: fxIn.flash, pointerEvents: 'none'}} /> : null}
        {label > 0 && beat.topic ? <TopicLabel text={beat.topic} alpha={label} /> : null}
        <div style={{position: 'absolute', inset: 0, borderRadius: RADIUS, border: `2px solid ${c.border}`, pointerEvents: 'none'}} />
      </div>
      <div style={{position: 'absolute', left: PROMO_TEXT_X, top: PROMO_CAPTION_TOP, width: PROMO_W - 2 * (PROMO_TEXT_X - PROMO_X), opacity: text.opacity,
        transform: `translateY(${text.dy}px)`, display: 'flex', flexDirection: 'column', gap: 14}}>
        <div style={{fontSize: size.en, fontWeight: 700, lineHeight: 1.25, overflowWrap: 'break-word', textWrap: 'balance' as any}}>{beat.en}</div>
        <div style={{fontFamily: SERIF, fontSize: size.zh, fontWeight: 500, lineHeight: 1.35, color: c.accent, overflowWrap: 'break-word',
          textWrap: 'balance' as any}}><ZhText text={beat.zh} units={beat.zhUnits} /></div>
      </div>
    </AbsoluteFill>
  );
};

export const ShowcasePromo: React.FC<ShowcaseProps> = ({theme, brand, name, nameZh, tagline, sourceLabel, beats, transition}) => (
  <PromoFrame theme={theme} brand={brand} name={name} nameZh={nameZh} tagline={tagline} sourceLabel={sourceLabel} beats={beats}>
    {beats.map((b, i) => {
      const lead = leadsFor(beats)[i];
      return (
      <React.Fragment key={b.id}>
        <Sequence from={b.startFrame - lead} durationInFrames={b.frames + lead}>
          <BeatLayer beat={b} prev={beats[i - 1]} next={beats[i + 1]} transition={transition} />
        </Sequence>
        {b.audio ? (
          <Sequence from={b.startFrame} durationInFrames={b.frames}><Audio src={staticFile(b.audio)} /></Sequence>
        ) : null}
      </React.Fragment>
      );
    })}
  </PromoFrame>
);
