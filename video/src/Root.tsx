import React from 'react';
import {Composition} from 'remotion';
import {InspireShort} from './Video';
import {InspireCover} from './Cover';

const FPS = 30;

export const Root: React.FC = () => (
  <>
  <Composition
    id="InspireShort"
    component={InspireShort}
    durationInFrames={45 * FPS}
    fps={FPS}
    width={1080}
    height={1920}
    // Clip length comes from props (--props=<file>.json); falls back to 45 s.
    calculateMetadata={({props}) => ({
      durationInFrames: Math.max(1, Math.round((props.durationSeconds ?? 45) * FPS)),
    })}
    defaultProps={{
      headline: '先行动，再自信',
      subtitle: 'Act First, Then Feel Confident',
      quoteEn: 'It removes a little bit of the insecurity.',
      quoteZh: '那份不安全感就会减轻一点。',
      speaker: 'SPEAKER NAME',
      source: 'PODCAST · 2025',
      clip: null as string | null,
      durationSeconds: 45,
      category: 'INSPIRATION / 向上生长',
      cues: [] as {start: number; end: number; en: string; zh: string}[],
      talkTitle: '',
      excerptLabel: '',
      theme: 'light',
      people: [] as {id: string; name: string}[],
      videoFit: 'contain' as 'cover' | 'contain',
      cropX: 0.5,
      cropY: 0.5,
      speakerZh: '',
      role: '',
      roleZh: '',
    }}
  />
  <Composition
    id="InspireCover"
    component={InspireCover}
    durationInFrames={1}
    fps={FPS}
    width={1080}
    height={1920}
    defaultProps={{headline: '先行动，再自信', subtitle: 'Act First', speaker: 'SPEAKER', speakerZh: '', role: '', roleZh: '', source: 'SOURCE · 2025',
      poster: null as string | null, theme: 'light', people: [] as {id: string; name: string}[], talkTitle: '', category: 'INSPIRATION / 向上生长'}}
  />
  </>
);
