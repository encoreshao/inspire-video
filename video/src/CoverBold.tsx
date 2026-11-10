import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {SERIF, pickTheme} from './Video';
import type {CoverProps} from './Cover';

// Feed covers for WeChat Channels and Douyin: a big face, a big title, one small name tag.
// Text stays inside the middle 3:4 band so the profile-grid crop never cuts it.
const MARKS = '，：、；,:;';
const splitTitle = (text: string, maxPerLine: number): string[] => {
  if (text.length <= maxPerLine) return [text];
  const marks = [...text].map((ch, k) => (MARKS.includes(ch) ? k : -1)).filter((k) => k > 0 && k < text.length - 1);
  const mid = text.length / 2;
  const cut = marks.length ? marks.reduce((a, b) => (Math.abs(b + 1 - mid) < Math.abs(a + 1 - mid) ? b : a)) : Math.ceil(mid) - 1;
  const keep = MARKS.includes(text[cut]) ? 0 : 1;
  return [text.slice(0, cut + keep), text.slice(cut + 1)].map((l) => l.trim());
};

export const CoverBold: React.FC<CoverProps & {variant: 'split' | 'blur'}> = ({headline, subtitle, speaker, speakerZh, poster, category, theme, variant, profile}) => {
  const c = pickTheme(theme);
  const H = profile?.height ?? 1920;
  const tall = H > 1600;
  const X = 72, W = 1080 - 2 * X;
  const lines = splitTitle(headline, 8);
  const longest = Math.max(...lines.map((l) => l.length));
  const size = Math.min(tall ? 132 : 112, Math.floor(W / longest) - 2);
  const src = poster ? (/^https?:/.test(poster) ? poster : staticFile(poster)) : null;
  const name = [speaker, speakerZh && speakerZh !== speaker ? speakerZh : ''].filter(Boolean).join('  ');
  const dark = '#17120F', cream = '#FFF6EA';
  const title = (
    <div style={{fontFamily: SERIF, fontWeight: 900, fontSize: size, lineHeight: 1.18, letterSpacing: 2, color: cream}}>
      {lines.map((l, k) => <div key={k} style={{whiteSpace: 'nowrap', color: k === lines.length - 1 && lines.length > 1 ? c.accent : cream}}>{l}</div>)}
    </div>
  );
  const chip = <div style={{display: 'inline-block', fontSize: 28, letterSpacing: 3, color: dark, background: c.accent, borderRadius: 999, padding: '8px 24px', fontWeight: 700}}>{category || 'INSPIRATION / 向上生长'}</div>;
  const tag = name ? <div style={{display: 'inline-block', fontSize: 34, fontWeight: 700, color: cream, background: 'rgba(23,18,15,0.72)', borderRadius: 14, padding: '10px 22px'}}>{name}</div> : null;
  const sub = <div style={{fontSize: 34, lineHeight: 1.3, color: 'rgba(255,246,234,0.78)', marginTop: 26, textWrap: 'balance' as any}}>{subtitle}</div>;

  if (variant === 'split') {
    const photoH = tall ? 1180 : 800;
    return (
      <AbsoluteFill style={{background: dark, fontFamily: 'Arial, sans-serif'}}>
        <div style={{position: 'absolute', left: 0, top: 0, width: 1080, height: photoH, overflow: 'hidden'}}>
          {src && <Img src={src} style={{width: '100%', height: '100%', objectFit: 'cover'}} />}
          <div style={{position: 'absolute', inset: 0, background: `linear-gradient(180deg, rgba(23,18,15,0) 60%, ${dark} 100%)`}} />
          <div style={{position: 'absolute', left: X, bottom: 50}}>{tag}</div>
        </div>
        <div style={{position: 'absolute', left: X, top: photoH + 10, width: W}}>
          <div style={{marginBottom: 26}}>{chip}</div>
          {title}
          {sub}
        </div>
      </AbsoluteFill>
    );
  }
  const photoH = tall ? 900 : 640;
  return (
    <AbsoluteFill style={{background: dark, fontFamily: 'Arial, sans-serif'}}>
      {src && <Img src={src} style={{position: 'absolute', inset: -60, width: 1200, height: H + 120, objectFit: 'cover', filter: 'blur(38px) brightness(0.5) saturate(1.2)'}} />}
      <div style={{position: 'absolute', inset: 0, background: `linear-gradient(180deg, rgba(23,18,15,0.1), rgba(23,18,15,0.55))`}} />
      <div style={{position: 'absolute', left: X, top: tall ? 150 : 80, width: W}}>
        <div style={{position: 'relative', height: photoH, borderRadius: 32, overflow: 'hidden', boxShadow: '0 30px 80px rgba(0,0,0,0.5)', border: '3px solid rgba(255,246,234,0.25)'}}>
          {src && <Img src={src} style={{width: '100%', height: '100%', objectFit: 'cover'}} />}
          <div style={{position: 'absolute', left: 24, bottom: 24}}>{tag}</div>
        </div>
        <div style={{marginTop: 44, marginBottom: 26}}>{chip}</div>
        {title}
        {sub}
      </div>
    </AbsoluteFill>
  );
};
