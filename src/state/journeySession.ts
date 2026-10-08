import { useCallback, useState, type Dispatch, type SetStateAction } from "react";
import type {
  CareerSwitchRequest,
  SimulationMarketCode,
  TransitionLearningOption,
  WhatIfScenario,
} from "../types";
import type { DecisionPriorities } from "../utils/decisionScoring";

export const JOURNEY_SESSION_KEY = "careertwin-journey-v1";
const LEGACY_PROFILE_KEY = "careertwin-profile-id";

export type AppScreen = "home" | "profile" | "dashboard";

export interface CareerSwitchSession {
  currentId: string;
  targetId: string;
  switchYear: CareerSwitchRequest["years_before_switch"];
  learnedSkills: TransitionLearningOption[];
  willingEducation: boolean;
  willingMba: boolean;
  demandChange: "none" | "up" | "down";
  aiChange: "none" | "up" | "down";
}

export interface EducationSession {
  path: "full_time_mba" | "part_time_mba";
  duration: number;
  startAfter: CareerSwitchRequest["years_before_switch"];
  tuition: number;
  living: number;
  other: number;
  postAdjustment: number;
  currentId: string;
  targetId: string;
  experience: number;
  graduationYear: number;
}

export interface JourneySession {
  profileId: number | null;
  market: SimulationMarketCode;
  screen: AppScreen;
  whatIfScenario?: WhatIfScenario;
  developmentCareerId?: string;
  simulationCareerIds?: string[];
  whatIfCareerId?: string;
  aiRiskCareerId?: string;
  aiRiskCompareIds?: string[];
  aiRiskTaskName?: string;
  decisionCareerIds?: string[];
  comparisonCareerIds?: string[];
  decisionPriorities?: DecisionPriorities;
  decisionSwitchPair?: [string, string];
  careerSwitch?: CareerSwitchSession;
  education?: EducationSession;
}

function inBrowser(): boolean {
  return typeof window !== "undefined" && !!window.localStorage;
}

export function readJourneySession(): Partial<JourneySession> {
  if (!inBrowser()) return {};
  try {
    const raw = window.localStorage.getItem(JOURNEY_SESSION_KEY);
    const parsed: unknown = raw ? JSON.parse(raw) : {};
    const session = parsed && typeof parsed === "object" ? parsed as Partial<JourneySession> : {};
    const legacyId = Number(window.localStorage.getItem(LEGACY_PROFILE_KEY));
    const profileId = Number.isInteger(session.profileId) && Number(session.profileId) > 0
      ? Number(session.profileId)
      : Number.isInteger(legacyId) && legacyId > 0 ? legacyId : null;
    return {
      ...session,
      profileId,
      market: session.market === "US" ? "US" : "IN",
      screen: session.screen === "profile" || session.screen === "home" ? session.screen : "dashboard",
    };
  } catch {
    return {};
  }
}

export function writeJourneyField<K extends keyof JourneySession>(key: K, value: JourneySession[K]): void {
  if (!inBrowser()) return;
  try {
    const current = readJourneySession();
    window.localStorage.setItem(JOURNEY_SESSION_KEY, JSON.stringify({ ...current, [key]: value }));
  } catch {
    // The in-memory state remains usable if storage is unavailable or full.
  }
}

export function clearJourneySession(): void {
  if (!inBrowser()) return;
  try {
    window.localStorage.removeItem(JOURNEY_SESSION_KEY);
    window.localStorage.removeItem(LEGACY_PROFILE_KEY);
  } catch {
    // Continue the current reset in memory if browser storage is unavailable.
  }
}

type StoredJourneyValue<K extends keyof JourneySession> = Exclude<JourneySession[K], undefined>;

export function useJourneyState<K extends keyof JourneySession>(
  key: K,
  initialValue: StoredJourneyValue<K> | (() => StoredJourneyValue<K>),
): [StoredJourneyValue<K>, Dispatch<SetStateAction<StoredJourneyValue<K>>>] {
  const [value, setValue] = useState<StoredJourneyValue<K>>(() => {
    const saved = readJourneySession()[key];
    if (saved !== undefined) return saved as StoredJourneyValue<K>;
    return typeof initialValue === "function"
      ? (initialValue as () => StoredJourneyValue<K>)()
      : initialValue;
  });
  const setPersistedValue = useCallback<Dispatch<SetStateAction<StoredJourneyValue<K>>>>((nextValue) => {
    setValue((current) => {
      const resolved = typeof nextValue === "function"
        ? (nextValue as (previous: StoredJourneyValue<K>) => StoredJourneyValue<K>)(current)
        : nextValue;
      writeJourneyField(key, resolved as JourneySession[K]);
      return resolved;
    });
  }, [key]);
  return [value, setPersistedValue];
}
