import React from 'react';
import {ClassicShort} from '../Video';
import type {Props} from '../Video';
import {InspireCover as ClassicCover} from '../Cover';
import type {CoverProps} from '../Cover';
import {BackdropCover, BackdropShort} from './Backdrop';
import {BannerCover, BannerShort} from './Banner';
import {CinemaCover, CinemaShort} from './Cinema';
import {QuoteCover, QuoteShort} from './Quote';
import {SplitCover, SplitShort} from './Split';

// Must match the `layout` enum in schemas/manifest-schema.json and LAYOUTS in scripts/render.py.
export const LAYOUTS = {
  classic: {Short: ClassicShort, Cover: ClassicCover},
  backdrop: {Short: BackdropShort, Cover: BackdropCover},
  cinema: {Short: CinemaShort, Cover: CinemaCover},
  quote: {Short: QuoteShort, Cover: QuoteCover},
  split: {Short: SplitShort, Cover: SplitCover},
  banner: {Short: BannerShort, Cover: BannerCover},
} as const;

const pick = (layout?: string) => (LAYOUTS as Record<string, (typeof LAYOUTS)[keyof typeof LAYOUTS]>)[layout ?? ''] ?? LAYOUTS.classic;

export const InspireShort: React.FC<Props> = (props) => {
  const {Short} = pick(props.layout);
  return <Short {...props} />;
};

export const InspireCover: React.FC<CoverProps> = (props) => {
  const {Cover} = pick(props.layout);
  return <Cover {...props} />;
};
