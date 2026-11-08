import test from 'node:test';
import assert from 'node:assert/strict';
import {
  PIPS_MAX, TOPIC_MAX_UNITS, XF_SAME, XF_TOPIC, captionAlpha, incoming, labelAlpha, leadsFor, outgoing, progressLayout,
  topicChanged, topicValid, transitionKind, transitionLead, widthUnits,
} from './transitions.mjs';

const beats = (specs) => specs.reduce((acc, [asset, topic], i) => {
  const startFrame = i ? acc[i - 1].startFrame + acc[i - 1].frames : 0;
  acc.push({asset, topic, startFrame, frames: 240});
  return acc;
}, []);

test('a topic change is the topic when either beat names one, else the capture', () => {
  assert.equal(topicChanged(null, {asset: 'a'}), false);
  assert.equal(topicChanged({asset: 'a', topic: 'X'}, {asset: 'b', topic: 'X'}), false);   // same label across captures
  assert.equal(topicChanged({asset: 'a', topic: 'X'}, {asset: 'a', topic: 'Y'}), true);
  assert.equal(topicChanged({asset: 'a'}, {asset: 'a', topic: 'Y'}), true);
  assert.equal(topicChanged({asset: 'a'}, {asset: 'a'}), false);
  assert.equal(topicChanged({asset: 'a'}, {asset: 'b'}), true);
  assert.equal(topicChanged({asset: ''}, {asset: ''}), false);                             // two statements
});

test('leads: none for the first beat, short within a topic, longer on a change, never beyond the start', () => {
  const b = beats([['a'], ['a'], ['b'], ['b']]);
  assert.deepEqual(leadsFor(b), [0, XF_SAME, XF_TOPIC, XF_SAME]);
  assert.ok(XF_TOPIC > XF_SAME);
  assert.equal(transitionLead({asset: 'a'}, {asset: 'b', startFrame: 5}), 5);
  assert.equal(transitionKind(null, b[0]), 'first');
});

test('the incoming picture dissolves eased, arrives at rest, and the outgoing one drifts without a jump', () => {
  for (const kind of ['topic', 'same']) {
    const lead = kind === 'topic' ? XF_TOPIC : XF_SAME;
    assert.deepEqual(incoming(0, lead, kind).opacity, 0);
    const end = incoming(lead, lead, kind);
    assert.deepEqual(end, {opacity: 1, scale: 1, dy: 0});
    let prev = -1;
    for (let f = 0; f <= lead; f++) {
      const o = incoming(f, lead, kind).opacity;
      assert.ok(o >= prev && o >= 0 && o <= 1);
      prev = o;
    }
    assert.ok(incoming(1, lead, kind).opacity < 1 / lead, 'eased: slower than linear at the start');
    assert.deepEqual(outgoing(0, lead, kind), {scale: 1, dy: -0});
    assert.ok(outgoing(lead, lead, kind).scale > 1);
  }
  assert.ok(incoming(3, XF_TOPIC, 'topic').scale > incoming(3, XF_SAME, 'same').scale);
  assert.deepEqual(incoming(0, 0, 'first'), {opacity: 1, scale: 1, dy: 0});
});

test('the old caption is gone before the new one starts, so two captions never overlap', () => {
  for (const lead of [XF_SAME, XF_TOPIC]) {
    // the old beat: the outgoing window is its last `lead` frames (toEnd counts down from lead to 0)
    assert.equal(captionAlpha(5, lead, lead).opacity, 1);
    assert.equal(captionAlpha(5, 0, lead).opacity, 0);
    for (let toEnd = lead; toEnd >= 0; toEnd--) {
      const old = captionAlpha(5, toEnd, lead).opacity;
      // the new beat, `toEnd` frames before its startFrame, shows no text at all until it starts
      const fresh = captionAlpha(-toEnd / 30 - 1e-9, 1e6, 0).opacity;
      assert.ok(old * fresh === 0, `lead ${lead} toEnd ${toEnd}`);
    }
  }
  assert.equal(captionAlpha(0, 1e6, 0).opacity, 0);
  assert.equal(captionAlpha(1, 1e6, 0).opacity, 1);
});

test('the topic label shows for about 1.5 s after the dissolve and then leaves', () => {
  assert.equal(labelAlpha(-0.5), 0);
  assert.equal(labelAlpha(0), 0);
  assert.equal(labelAlpha(0.15 + 0.25), 1);
  assert.equal(labelAlpha(1.0), 1);
  assert.equal(labelAlpha(1.8), 0);
  assert.ok(labelAlpha(0.15 + 1.5 - 0.1) < 1);
});

test('topic rules: one string, at most 28 width units, letters digits CJK and a few marks', () => {
  assert.equal(TOPIC_MAX_UNITS, 28);
  assert.equal(widthUnits('服务 Our'), 8);
  for (const ok of ['Our services', '服务', 'Our services · 服务', 'Q&A', 'AI / data', "What's new", 'A', 'x'.repeat(28)]) assert.ok(topicValid(ok), ok);
  for (const bad of ['', ' Home', 'Home ', 'a\nb', '<b>x</b>', 'x'.repeat(29), '服'.repeat(15), 'Hi 🙂', 'a—b', 5, undefined]) assert.ok(!topicValid(bad), String(bad));
});

test('progress: pips for short lists, one bar with a tick per topic change for long ones', () => {
  const short = beats(Array.from({length: PIPS_MAX}, (_, i) => [`p${i}`]));
  assert.deepEqual(progressLayout(short), {mode: 'pips', ticks: []});
  const long = beats(Array.from({length: 40}, (_, i) => [`p${Math.floor(i / 4)}`]));
  const l = progressLayout(long);
  assert.equal(l.mode, 'bar');
  assert.equal(l.ticks.length, 9);
  assert.ok(l.ticks.every((x, i) => x > 0 && x < 1 && (i === 0 || x > l.ticks[i - 1])));
  assert.ok(Math.abs(l.ticks[0] - 4 / 40) < 1e-9);
});
