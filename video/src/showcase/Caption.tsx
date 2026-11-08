import React from 'react';
import {CARD_PAD_Y, SERIF, ZhText, fit, useTheme} from '../Video';

export type CaptionBeat = {en: string; zh: string; zhUnits?: string[]};

// The bilingual caption card under the stage; `textAlpha` fades the text in at the start of a beat.
export const CaptionCard: React.FC<{beat: CaptionBeat; textAlpha: number}> = ({beat, textAlpha}) => {
  const c = useTheme();
  const size = fit(beat);
  return (
    <div style={{borderTop: `3px solid ${c.border}`, background: c.card, padding: `${CARD_PAD_Y}px 32px`, textAlign: 'center',
      minHeight: 64, boxSizing: 'content-box'}}>
      <div style={{opacity: textAlpha, display: 'flex', flexDirection: 'column', gap: 6}}>
        <div style={{fontSize: size.en, fontWeight: 600, lineHeight: 1.28, overflowWrap: 'break-word', textWrap: 'balance' as any}}>{beat.en}</div>
        <div style={{fontFamily: SERIF, fontSize: size.zh, fontWeight: 500, lineHeight: 1.38, color: c.accent,
          overflowWrap: 'break-word', textWrap: 'balance' as any}}><ZhText text={beat.zh} units={beat.zhUnits} /></div>
      </div>
    </div>
  );
};
