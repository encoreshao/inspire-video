import type {Shot} from './promo.mjs';
export const SHOTS: Readonly<Record<string, Readonly<Shot>>>;
export function shotMeta(): Record<string, {minSeconds: number; maxPerVideo: number | null; needsTallPage: boolean}>;
