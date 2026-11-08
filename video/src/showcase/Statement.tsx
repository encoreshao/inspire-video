import React from 'react';
import {SERIF, useTheme} from '../Video';
import type {Size} from './promo.mjs';
import {statementFontSize, statementReveal} from './shots.mjs';

// A Chinese character counts 2, as in the manifest's width limit.
const widthUnits = (s: string) => [...s].reduce((n, ch) => n + (ch.charCodeAt(0) >= 0x2e80 ? 2 : 1), 0);

export type StatementProps = {
  text: string;
  units: string[];             // the words that arrive one after another, each keeping its trailing space
  stage: Size;
  frame: number;               // frames into the beat; any large value shows the finished statement
};

// The statement shot: large text on the theme's card colour, no capture, no camera.
export const Statement: React.FC<StatementProps> = ({text, units, stage, frame}) => {
  const c = useTheme();
  const size = statementFontSize(widthUnits(text));
  return (
    <div style={{width: stage.w, height: stage.h, background: c.card, display: 'flex', alignItems: 'center',
      justifyContent: 'center', padding: '0 56px', boxSizing: 'border-box'}}>
      <div style={{fontFamily: SERIF, fontSize: size, fontWeight: 700, lineHeight: 1.25, letterSpacing: 1, color: c.ink,
        textAlign: 'center', textWrap: 'balance' as any}}>
        {units.map((u, i) => {
          const r = statementReveal(i, frame);
          const space = u.endsWith(' ');
          return (
            <React.Fragment key={i}>
              <span style={{display: 'inline-block', opacity: r.opacity, transform: `translateY(${r.dy}px)`}}>{space ? u.slice(0, -1) : u}</span>
              {space ? ' ' : null}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
