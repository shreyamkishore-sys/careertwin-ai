import test from 'node:test';
import assert from 'node:assert/strict';
import { clearJourneySession, JOURNEY_SESSION_KEY, readJourneySession, writeJourneyField } from '../src/state/journeySession.ts';
import { buildEducationTrajectory } from '../src/utils/educationRoi.ts';

function installStorage() {
  const data = new Map();
  globalThis.window = { localStorage: {
    getItem: (key) => data.get(key) ?? null,
    setItem: (key, value) => data.set(key, String(value)),
    removeItem: (key) => data.delete(key),
  } };
  return data;
}

test('active profile and market restore from journey storage', () => {
  installStorage();
  writeJourneyField('profileId', 42);
  writeJourneyField('market', 'US');
  assert.equal(readJourneySession().profileId, 42);
  assert.equal(readJourneySession().market, 'US');
});

test('legacy profile ID migrates and brand-new sessions default to India', () => {
  const storage = installStorage();
  assert.equal(readJourneySession().market, 'IN');
  storage.set('careertwin-profile-id', '19');
  assert.equal(readJourneySession().profileId, 19);
});

test('Start Over clears active and legacy journey identifiers and scenario selections', () => {
  const storage = installStorage();
  writeJourneyField('profileId', 42);
  writeJourneyField('whatIfScenario', { avoid_coding: true });
  storage.set('careertwin-profile-id', '42');
  clearJourneySession();
  assert.equal(storage.has(JOURNEY_SESSION_KEY), false);
  assert.equal(storage.has('careertwin-profile-id'), false);
  assert.equal(readJourneySession().profileId, null);
});

test('What-If scenario is restored for the existing simulation overlay input', () => {
  installStorage();
  const scenario = { avoid_coding: true, willing_mba: false };
  writeJourneyField('whatIfScenario', scenario);
  assert.deepEqual(readJourneySession().whatIfScenario, scenario);
});

test('selected development-plan career is restored', () => {
  installStorage();
  writeJourneyField('developmentCareerId', 'product-manager');
  assert.equal(readJourneySession().developmentCareerId, 'product-manager');
});

test('career comparison selections persist with the existing journey session', () => {
  installStorage();
  writeJourneyField('comparisonCareerIds', ['data-analyst', 'product-analyst']);
  writeJourneyField('market', 'US');
  assert.deepEqual(readJourneySession().comparisonCareerIds, ['data-analyst', 'product-analyst']);
  assert.equal(readJourneySession().market, 'US');
});

test('market selection remains stable across unrelated journey updates', () => {
  installStorage();
  writeJourneyField('market', 'US');
  writeJourneyField('whatIfCareerId', 'data-analyst');
  assert.equal(readJourneySession().market, 'US');
});

test('part-time education retains current-career salary during study years', () => {
  const currentCareer = { career_title: 'Current', years: Array.from({ length: 11 }, (_, year) => ({ year, role: 'Current role', salary_low: 80 + year, salary_mid: 100 + year, salary_high: 120 + year })) };
  const targetCareer = { career_title: 'Target', years: Array.from({ length: 11 }, (_, year) => ({ year, role: 'Target role', salary_low: 180 + year, salary_mid: 200 + year, salary_high: 220 + year })) };
  const rows = buildEducationTrajectory({ currentCareer, targetCareer, duration: 2, startAfter: 0, directCost: 12, postAdjustment: 0, path: 'part_time_mba' });
  assert.equal(rows[0].education, rows[0].work);
  assert.equal(rows[1].education, rows[1].work);
  assert.equal(rows[2].education, targetCareer.years[1].salary_mid);
  assert.equal(rows[2].role, 'Target role');
});

test('full-time education models no salary during study and starts target trajectory after', () => {
  const currentCareer = { career_title: 'Current', years: Array.from({ length: 11 }, (_, year) => ({ year, role: 'Current role', salary_low: 80 + year, salary_mid: 100 + year, salary_high: 120 + year })) };
  const targetCareer = { career_title: 'Target', years: Array.from({ length: 11 }, (_, year) => ({ year, role: 'Target role', salary_low: 180 + year, salary_mid: 200 + year, salary_high: 220 + year })) };
  const rows = buildEducationTrajectory({ currentCareer, targetCareer, duration: 2, startAfter: 0, directCost: 12, postAdjustment: 0, path: 'full_time_mba' });
  assert.equal(rows[0].education, 0);
  assert.equal(rows[1].education, 0);
  assert.equal(rows[2].education, targetCareer.years[1].salary_mid);
});
