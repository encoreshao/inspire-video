import type {Shot} from './promo.mjs';
export const SHOTS: Readonly<Record<string, Readonly<Shot>>>;
export function shotMeta(): Record<string, {minSeconds: number; maxPerVideo: number | null; needsTallPage: boolean; needsTarget: boolean}>;
export const STATEMENT_STAGGER: number;
export const STATEMENT_ENTER: number;
export function statementReveal(index: number, frame: number): {opacity: number; dy: number};
export function statementDoneFrame(count: number): number;
export function statementFontSize(widthUnits: number): number;
