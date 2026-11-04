import React from 'react';
import {AbsoluteFill, OffthreadVideo, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

export type Cue = {start: number; end: number; en: string; zh: string; speaker?: string};
export type Person = {id: string; name: string; name_zh?: string; title?: string; title_zh?: string; org?: string};

export type Props = {
  headline: string;
  subtitle: string;
  quoteEn: string;
  quoteZh: string;
  speaker: string;
  source: string;
  clip: string | null;
  durationSeconds?: number;
  category?: string;
  cues?: Cue[];
  talkTitle?: string;
  excerptLabel?: string;
  speakerZh?: string;
  role?: string;
  roleZh?: string;
  theme?: string;
  people?: Person[];
  videoFit?: 'cover' | 'contain';
  cropX?: number;
  cropY?: number;
};

export const themes = {
  // Warm ivory / parchment (original look)
  ivory: {paper: '#F4EBDD', card: '#FFF9F0', cardBorder: '#D7C9B5', ink: '#2F251F', accent: '#A64F3D',
    muted: '#68664F', border: '#B8A58B', track: '#E3D6C1', videoBg: '#171717',
    shadow: '0 24px 48px rgba(80,55,30,0.26), 0 4px 12px rgba(80,55,30,0.15)'},
  // Light, soft off-white (default): easy on the eyes
  light: {paper: '#F7F4EE', card: '#FFFFFF', cardBorder: '#E5DED2', ink: '#2B2623', accent: '#B5533C',
    muted: '#6F695E', border: '#D3CABB', track: '#E7E0D4', videoBg: '#1A1714',
    shadow: '0 24px 48px rgba(70,50,30,0.24), 0 4px 12px rgba(70,50,30,0.14)'},
  // Light cool gray-blue
  mist: {paper: '#EDF1F3', card: '#FBFCFD', cardBorder: '#D5DDE1', ink: '#232B2E', accent: '#B0523D',
    muted: '#5E6B70', border: '#BFCBD1', track: '#D9E1E5', videoBg: '#171B1D',
    shadow: '0 24px 48px rgba(30,50,60,0.26), 0 4px 12px rgba(30,50,60,0.15)'},
  // Deep warm ink with cream text and a light terracotta accent
  ink: {paper: '#1D1814', card: '#2A231D', cardBorder: '#42372D', ink: '#F4EADB', accent: '#E8956F',
    muted: '#B9AB95', border: '#54473B', track: '#3A3028', videoBg: '#0E0B09',
    shadow: '0 24px 52px rgba(0,0,0,0.6), 0 4px 14px rgba(0,0,0,0.45)'},
  // Soft sage green
  sage: {paper: '#DDE3D3', card: '#F3F6EC', cardBorder: '#BCC7AB', ink: '#243026', accent: '#9A4A36',
    muted: '#566451', border: '#9FAE8E', track: '#C4CEB4', videoBg: '#141814',
    shadow: '0 24px 48px rgba(40,60,40,0.26), 0 4px 12px rgba(40,60,40,0.15)'},
};
export type Theme = typeof themes.ivory;
export const ThemeCtx = React.createContext<Theme>(themes.light);
export const useTheme = () => React.useContext(ThemeCtx);
export const pickTheme = (name?: string): Theme => (themes as Record<string, Theme>)[name ?? ''] ?? themes.light;
export const SERIF = '"Noto Serif CJK SC", "Songti SC", Georgia, serif';

// Break a long headline after the first Chinese comma only when it would not fit on one line.
export const HeadlineLines: React.FC<{text: string; size: number; width?: number}> = ({text, size, width = 984}) => {
  const i = text.indexOf('，');
  const fits = text.length * (size + 1) <= width;
  const lines = !fits && i > 0 ? [text.slice(0, i + 1), text.slice(i + 1)] : [text];
  return <>{lines.map((l, k) => <div key={k} style={{whiteSpace: 'nowrap'}}>{l}</div>)}</>;
};

const resolve = (p: string) => (/^https?:/.test(p) ? p : staticFile(p));

// Pick the largest font size (capped) at which BOTH languages fit the text area (estimated line
// wrapping), so a caption is never cut off. The card height is sized to the tallest cue.
// Platform safe area (WeChat Channels / Douyin fill tall phones by scaling to the height and
// center-cropping the sides: about 108 px per side at 9:20, 97 px at 9:19.5). Keep ALL content
// inside these margins. Bottom/top also avoid the platform's own buttons and captions.
export const SAFE_X = 114;
export const SAFE_BOTTOM = 330; // the lowest content must end above 1920 - SAFE_BOTTOM = 1590
// The title is anchored at a fixed distance from the top (top-anchored layout), so adding or
// resizing blocks below it never moves the title. TITLE_TOP is the top padding in px; with the
// 22 px label it puts the label's top edge at about y = 259 (the user-approved position).
export const TITLE_TOP = 256;
export const LINE_GAP = 26; // space above and below each divider line
const PANEL_W = 1080 - SAFE_X * 2; // 852
const CARD_TEXT_W = PANEL_W - 6 - 64; // panel inner width minus card padding
const CARD_PAD_Y = 12; // vertical padding inside the card
const MAX_EN = 34;
const needed = (cue: {en: string; zh: string}, en: number) => {
  const zh = en + 2;
  const enLines = Math.ceil((cue.en.length * en * 0.54) / CARD_TEXT_W);
  const zhLines = Math.ceil((cue.zh.length * zh * 1.04) / CARD_TEXT_W);
  return enLines * en * 1.28 + zhLines * zh * 1.38 + 14;
};
const fit = (cue: {en: string; zh: string}) => {
  for (let en = MAX_EN; en >= 26; en -= 2) {
    if (needed(cue, en) <= 400) return {en, zh: en + 2};
  }
  return {en: 26, zh: 28};
};
const HEAD = 42; // headline and English subtitle share this size
const cardHeight = (cues: {en: string; zh: string}[]) =>
  Math.max(64, ...cues.map((q) => needed(q, fit(q).en))) + CARD_PAD_Y * 2 + 4;

export const SpeakerBlock: React.FC<{speaker: string; speakerZh?: string; role?: string; roleZh?: string;
  scale?: number}> = ({speaker, speakerZh, role, roleZh, scale = 1}) => {
  const c = useTheme();
  return (
  <div>
    <div style={{display: 'flex', alignItems: 'baseline', gap: 18 * scale, flexWrap: 'wrap'}}>
      <span style={{fontSize: 38 * scale, lineHeight: 1.2, color: c.accent, fontWeight: 700}}>{speaker}</span>
      {speakerZh ? <span style={{fontFamily: SERIF, fontSize: 38 * scale, color: c.accent, fontWeight: 700}}>{speakerZh}</span> : null}
    </div>
    {role ? <div style={{fontSize: 25 * scale, lineHeight: 1.3, color: c.ink, marginTop: 6 * scale}}>{role}</div> : null}
    {roleZh ? <div style={{fontFamily: SERIF, fontSize: 25 * scale, lineHeight: 1.3, color: c.muted, marginTop: 2 * scale}}>{roleZh}</div> : null}
  </div>
  );
};

// Names for several people on screen: everyone is listed, the current speaker is highlighted.
export const PeopleRow: React.FC<{people: Person[]; activeId?: string; scale?: number}> = ({people, activeId, scale = 1}) => {
  const c = useTheme();
  const cols = Math.min(people.length, 3);
  return (
    <div style={{display: 'grid', gridTemplateColumns: `repeat(${cols}, 1fr)`, gap: `${14 * scale}px ${18 * scale}px`}}>
      {people.map((p) => {
        const on = !activeId || p.id === activeId;
        return (
          <div key={p.id} style={{opacity: on ? 1 : 0.5, borderLeft: `${4 * scale}px solid ${on && activeId ? c.accent : c.border}`,
            paddingLeft: 12 * scale}}>
            <div style={{fontSize: 27 * scale, fontWeight: 700, lineHeight: 1.2, color: c.accent}}>{p.name}</div>
            {p.name_zh ? <div style={{fontFamily: SERIF, fontSize: 25 * scale, fontWeight: 700, color: c.accent}}>{p.name_zh}</div> : null}
            {p.title ? <div style={{fontSize: 20 * scale, lineHeight: 1.25, color: c.ink, marginTop: 4 * scale}}>{p.title}</div> : null}
            {p.title_zh ? <div style={{fontFamily: SERIF, fontSize: 19 * scale, lineHeight: 1.25, color: c.muted}}>{p.title_zh}</div> : null}
            {p.org ? <div style={{fontSize: 19 * scale, lineHeight: 1.25, color: c.muted}}>{p.org}</div> : null}
          </div>
        );
      })}
    </div>
  );
};

// Centered line: bright in the middle, fading out toward both ends.
export const Divider: React.FC = () => {
  const c = useTheme();
  return (
    <div style={{marginTop: LINE_GAP, height: 4, flexShrink: 0, borderRadius: 2,
      background: `linear-gradient(90deg, transparent 0%, ${c.border} 14%, ${c.accent} 40%, ${c.accent} 60%, ${c.border} 86%, transparent 100%)`,
      boxShadow: `0 0 16px ${c.accent}88`}} />
  );
};

export const InspireShort: React.FC<Props> = ({
  headline, subtitle, quoteEn, quoteZh, speaker, source, clip, category,
  cues, talkTitle, excerptLabel, speakerZh, role, roleZh, theme, people, videoFit = 'cover', cropX = 0.5, cropY = 0.5,
}) => {
  const c = pickTheme(theme);
  const frame = useCurrentFrame();
  const {durationInFrames, fps} = useVideoConfig();
  const t = frame / fps;
  const opacity = interpolate(frame, [0, 6, durationInFrames - 10, durationInFrames], [0, 1, 1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  // Synced captions: show the sentence being spoken; hold until the next one starts.
  const synced = cues && cues.length > 0;
  let active: Cue | null = null;
  if (synced) {
    for (const q of cues!) if (t >= q.start - 0.05) active = q;
  }
  const cue = synced ? active : {start: 0, end: 0, en: quoteEn, zh: quoteZh};
  const cueAlpha = !synced ? 1 : active
    ? interpolate(t - active.start, [-0.05, 0.12], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})
    : 0;
  const size = cue ? fit(cue) : {en: 34, zh: 36};
  const cardReserve = synced ? cardHeight(cues!) : 160;
  const videoH = videoFit === 'cover' ? 520 : Math.round((PANEL_W - 6) * 9 / 16);

  return (
    <ThemeCtx.Provider value={c}>
    <AbsoluteFill style={{
      opacity, backgroundColor: c.paper, color: c.ink,
      padding: `${TITLE_TOP}px ${SAFE_X}px 0`, display: 'flex', flexDirection: 'column', justifyContent: 'flex-start', fontFamily: 'Arial, sans-serif', boxSizing: 'border-box',
    }}>
      <div style={{flexShrink: 0, display: 'flex', flexDirection: 'column'}}>
        <div style={{fontSize: 22, letterSpacing: 1.5, color: c.muted, marginBottom: 16}}>
          {category || 'INSPIRATION / 向上生长'}
        </div>
        <div style={{fontFamily: SERIF, fontSize: HEAD, lineHeight: 1.3, fontWeight: 700, letterSpacing: 1}}>
          <HeadlineLines text={headline} size={HEAD} />
        </div>
        <div style={{fontSize: HEAD, lineHeight: 1.25, fontWeight: 600, color: c.muted, marginTop: 8}}>{subtitle}</div>
      </div>

      {/* Joined panel: video with the caption area attached directly below (square seam, no gap).
          The caption area grows/shrinks with its text; the space it may need is reserved so
          nothing else moves between captions. */}
      <Divider />

      <div style={{marginTop: LINE_GAP, height: videoH + 3 + cardReserve, flexShrink: 0}}>
        <div style={{border: `3px solid ${c.border}`, borderRadius: 24, overflow: 'hidden', background: c.card, boxShadow: c.shadow}}>
          <div style={{height: videoH, background: c.videoBg}}>
            {clip
              ? <OffthreadVideo src={resolve(clip)} style={{width: '100%', height: '100%', objectFit: videoFit, objectPosition: `${cropX * 100}% ${cropY * 100}%`}} />
              : <div style={{color: '#fff', fontSize: 28}}>Podcast footage</div>}
          </div>
          <div style={{borderTop: `3px solid ${c.border}`, background: c.card, padding: `${CARD_PAD_Y}px 32px`,
            textAlign: 'center', minHeight: 64, boxSizing: 'content-box'}}>
            {cue && (
              <div style={{opacity: cueAlpha, display: 'flex', flexDirection: 'column', gap: 6}}>
                <div style={{fontSize: size.en, fontWeight: 600, lineHeight: 1.28, overflowWrap: 'break-word', textWrap: 'balance' as any}}>{cue.en}</div>
                <div style={{fontFamily: SERIF, fontSize: size.zh, fontWeight: 500, lineHeight: 1.38,
                  color: c.accent, overflowWrap: 'break-word', textWrap: 'balance' as any}}>{cue.zh}</div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Same divider after the video panel */}
      <Divider />

      {/* Bottom info block */}
      <div style={{marginTop: LINE_GAP, flexShrink: 0, display: 'flex', flexDirection: 'column'}}>
        {people && people.length > 1
          ? <PeopleRow people={people} activeId={active?.speaker} />
          : <SpeakerBlock speaker={speaker} speakerZh={speakerZh} role={role} roleZh={roleZh} scale={1.1} />}
        {talkTitle && (
          <div style={{fontSize: 25, lineHeight: 1.3, color: c.ink, marginTop: 6, fontStyle: 'italic'}}>
            “{talkTitle}”
          </div>
        )}
        <div style={{borderTop: `2px solid ${c.border}`, marginTop: 10, paddingTop: 10, color: c.muted,
          fontSize: 23, lineHeight: 1.35}}>
          {source}{excerptLabel ? ` · ${excerptLabel}` : ''}
        </div>
        <div style={{marginTop: 14, height: 6, flexShrink: 0, borderRadius: 3, background: c.track}}>
          <div style={{height: '100%', borderRadius: 3, background: c.accent,
            width: `${Math.min(100, (frame / durationInFrames) * 100)}%`}} />
        </div>
      </div>
    </AbsoluteFill>
    </ThemeCtx.Provider>
  );
};
