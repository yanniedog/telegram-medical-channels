import test from 'node:test';
import assert from 'node:assert/strict';
import { recentlyCompleted } from './orchestrator-remind.mjs';

test('a recent reminder cannot stand in for a completed chief cycle', () => {
  const now = Date.parse('2026-09-12T04:00:00Z');
  assert.equal(recentlyCompleted({ lastChiefReminderAt: new Date(now).toISOString() }, now), false);
});

test('only a recent completed cycle suppresses repeat coordination', () => {
  const now = Date.parse('2026-09-12T04:00:00Z');
  assert.equal(recentlyCompleted({ lastChiefCompletedAt: new Date(now - 1000).toISOString() }, now), true);
  for (const at of ['invalid', new Date(now + 1000).toISOString(), new Date(now - 300000).toISOString()]) {
    assert.equal(recentlyCompleted({ lastChiefCompletedAt: at }, now), false);
  }
});
