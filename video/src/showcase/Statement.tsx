import React from 'react';
import {Img, staticFile} from 'remotion';
import {SERIF, useTheme} from '../Video';
import type {Size} from './promo.mjs';
import {STATEMENT_ENTER, statementFontSize, statementReveal} from './shots.mjs';

// A Chinese character counts 2, as in the manifest's width limit.
const widthUnits = (s: string) => [...s].reduce((n, ch) => n + (ch.charCodeAt(0) >= 0x2e80 ? 2 : 1), 0);

export type StatementProps = {
  text: string;
  units: string[];             // the words that arrive one after another, each keeping its trailing space
  stage: Size;
  frame: number;               // frames into the beat; any large value shows the finished statement
  backdrop?: string;           // a capture whose top shows as a peek under the text (a title card)
  facts?: string[];            // up to three short chips under the text
};

const resolve = (p: string) => (/^https?:/.test(p) ? p : staticFile(p));
const PEEK_RISE = 12;          // frames the peek takes to settle; it is on screen from the first frame

// The statement shot: large text on the theme's card colour, no camera. With a backdrop and facts it is a title card: the
// text is readable from the first frame (the first word is already in, the others follow), the facts sit under it, and the top
// of the real page rises into view below, so the opening and closing frames show the product instead of an empty card.
export const Statement: React.FC<StatementProps> = ({text, units, stage, frame, backdrop, facts}) => {
  const c = useTheme();
  const card = Boolean(backdrop || (facts && facts.length));
  const size = Math.min(statementFontSize(widthUnits(text)), card ? 78 : 88);
  const peekH = Math.round(stage.h * 0.36);
  const rise = Math.min(1, Math.max(0, frame / PEEK_RISE));
  return (
    <div style={{width: stage.w, height: stage.h, background: c.card, display: 'flex', flexDirection: 'column', alignItems: 'center',
      justifyContent: card ? 'flex-start' : 'center', padding: '0 56px', boxSizing: 'border-box', position: 'relative', overflow: 'hidden'}}>
      <div style={{flex: card ? 1 : undefined, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        gap: 30, paddingTop: card ? 36 : 0, width: '100%'}}>
        <div style={{fontFamily: SERIF, fontSize: size, fontWeight: 700, lineHeight: 1.25, letterSpacing: 1, color: c.ink,
          textAlign: 'center', textWrap: 'balance' as any}}>
          {units.map((u, i) => {
            const r = statementReveal(i, frame + STATEMENT_ENTER);
            const space = u.endsWith(' ');
            return (
              <React.Fragment key={i}>
                <span style={{display: 'inline-block', opacity: r.opacity, transform: `translateY(${r.dy}px)`}}>{space ? u.slice(0, -1) : u}</span>
                {space ? ' ' : null}
                {/[.!?。！？]\s*$/.test(u) && i < units.length - 1 ? <br /> : null}     {/* a sentence ends its line */}
              </React.Fragment>
            );
          })}
        </div>
        {facts && facts.length ? (
          <div style={{display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: 14}}>
            {facts.map((f, i) => (
              <div key={i} style={{fontSize: 28, fontWeight: 600, color: c.ink, border: `2px solid ${c.accent}`, borderRadius: 999,
                padding: '8px 22px', background: 'rgba(255,255,255,0.05)', whiteSpace: 'nowrap'}}>{f}</div>
            ))}
          </div>
        ) : null}
      </div>
      {backdrop ? (
        <div style={{width: stage.w - 112, height: peekH, marginTop: 28, borderRadius: '28px 28px 0 0', overflow: 'hidden', flexShrink: 0,
          border: `2px solid ${c.border}`, borderBottom: 'none', boxShadow: '0 -8px 30px rgba(0,0,0,0.28)',
          transform: `translateY(${(1 - rise) * 28}px)`}}>
          <Img src={resolve(backdrop)} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'top', display: 'block'}} />
        </div>
      ) : null}
    </div>
  );
};
