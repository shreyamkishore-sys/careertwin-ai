import { useState, type FormEvent } from "react";
import { ArrowLeft, ArrowRight, Check, GraduationCap, UserRound } from "lucide-react";
import {
  careerPriorities,
  educationLevels,
  interests,
  skills,
  workPreferences,
} from "../data/profileOptions";
import type {
  CareerPriority,
  EducationLevel,
  Interest,
  Skill,
  StudentProfile,
  StudentProfileInput,
  WorkPreference,
  SkillRatings,
  PriorityRatings,
  PreferenceRatings,
  Rating,
} from "../types";
import { DEFAULT_PREFERENCE_RATINGS, DEFAULT_SKILL_RATINGS, defaultsForPriorities, normalizeRatingRecord, preferenceFields, priorityFields, skillFields } from "../data/profileRatings";
import { NYRA_DEMO } from "../data/nyraDemo";

interface StudentProfileFormProps {
  initialProfile?: StudentProfile;
  isSaving: boolean;
  error: string | null;
  onBack: () => void;
  onSubmit: (profile: StudentProfileInput) => void;
}

function ChoiceGroup<T extends string>({
  title,
  hint,
  options,
  selected,
  onChange,
  columns = 2,
}: {
  title: string;
  hint?: string;
  options: { value: T; label: string }[];
  selected: T[];
  onChange: (value: T) => void;
  columns?: 2 | 3;
}) {
  return (
    <fieldset className="choice-fieldset">
      <legend>{title}</legend>
      {hint && <p className="field-hint">{hint}</p>}
      <div className={`choice-grid choice-grid-${columns}`}>
        {options.map(({ value, label }) => {
          const checked = selected.includes(value);
          return (
            <label className={`choice-chip ${checked ? "choice-chip-selected" : ""}`} key={value}>
              <input
                type="checkbox"
                checked={checked}
                onChange={() => onChange(value)}
              />
              <span className="choice-check">{checked && <Check size={12} />}</span>
              <span>{label}</span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}

function toggleChoice<T extends string>(values: T[], value: T): T[] {
  return values.includes(value) ? values.filter((item) => item !== value) : [...values, value];
}

const RATING_LABELS = ["Beginner", "Basic", "Intermediate", "Strong", "Advanced"];
function RatingControl({
  title, value, onChange, hint, ratingLabels = RATING_LABELS,
}: { title: string; value: Rating; onChange: (value: Rating) => void; hint?: string; ratingLabels?: string[] }) {
  return <fieldset className="profile-rating-control">
    <legend>{title}<strong>{value} · {ratingLabels[value - 1]}</strong></legend>
    {hint && <small>{hint}</small>}
    <div className="rating-buttons" role="group" aria-label={`${title} rating`}>
      {[1, 2, 3, 4, 5].map(number => <button type="button" key={number} className={value === number ? "rating-button rating-button-selected" : "rating-button"} aria-pressed={value === number} aria-label={`${title}: ${number}, ${ratingLabels[number - 1]}`} onClick={() => onChange(number as Rating)}>{number}</button>)}
    </div>
  </fieldset>;
}

export function StudentProfileForm({
  initialProfile,
  isSaving,
  error,
  onBack,
  onSubmit,
}: StudentProfileFormProps) {
  const [name, setName] = useState(initialProfile?.name ?? "");
  const [educationLevel, setEducationLevel] = useState<EducationLevel>(
    initialProfile?.education_level ?? "undergraduate",
  );
  const [fieldOfStudy, setFieldOfStudy] = useState(initialProfile?.field_of_study ?? "");
  const [selectedSkills, setSelectedSkills] = useState<Skill[]>(initialProfile?.skills ?? []);
  const [selectedInterests, setSelectedInterests] = useState<Interest[]>(initialProfile?.interests ?? []);
  const [selectedWorkPreferences, setSelectedWorkPreferences] = useState<WorkPreference[]>(
    initialProfile?.work_preferences ?? [],
  );
  const [selectedPriorities, setSelectedPriorities] = useState<CareerPriority[]>(
    initialProfile?.career_priorities ?? [],
  );
  const [skillRatings, setSkillRatings] = useState<SkillRatings>(() => ({ ...DEFAULT_SKILL_RATINGS, ...(initialProfile?.skill_ratings ?? {}) }));
  const [priorityRatings, setPriorityRatings] = useState<PriorityRatings>(() => defaultsForPriorities(initialProfile));
  const [preferenceRatings, setPreferenceRatings] = useState<PreferenceRatings>(() => ({ ...DEFAULT_PREFERENCE_RATINGS, ...(initialProfile?.preference_ratings ?? {}) }));
  const [validationError, setValidationError] = useState<string | null>(null);

  function loadNyraDemo() {
    setName(NYRA_DEMO.name);
    setEducationLevel(NYRA_DEMO.education_level);
    setFieldOfStudy(NYRA_DEMO.field_of_study);
    setSelectedSkills(NYRA_DEMO.skills);
    setSelectedInterests(NYRA_DEMO.interests);
    setSelectedWorkPreferences(NYRA_DEMO.work_preferences);
    setSelectedPriorities(NYRA_DEMO.career_priorities);
    setSkillRatings(NYRA_DEMO.skill_ratings);
    setPreferenceRatings(NYRA_DEMO.preference_ratings);
    setPriorityRatings(NYRA_DEMO.priority_ratings);
    setValidationError(null);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (name.trim().length < 2 || fieldOfStudy.trim().length < 2) {
      setValidationError("Please enter a name and area of study using at least two characters.");
      return;
    }
    if (selectedInterests.length === 0 || selectedWorkPreferences.length === 0 || selectedPriorities.length === 0) {
      setValidationError("Choose at least one interest, work preference, and career priority to build your CareerTwin.");
      return;
    }
    setValidationError(null);
    onSubmit({
      name: name.trim(),
      education_level: educationLevel,
      field_of_study: fieldOfStudy.trim(),
      skills: selectedSkills,
      skill_ratings: normalizeRatingRecord(skillRatings, skillFields),
      interests: selectedInterests,
      work_preferences: selectedWorkPreferences,
      preference_ratings: normalizeRatingRecord(preferenceRatings, preferenceFields),
      career_priorities: selectedPriorities,
      priority_ratings: normalizeRatingRecord(priorityRatings, priorityFields),
    });
  }

  return (
    <main className="profile-page">
      <div className="profile-container">
        <button className="back-link" type="button" onClick={onBack}>
          <ArrowLeft size={15} /> Back
        </button>

        <div className="profile-intro">
          <div className="eyebrow"><span className="eyebrow-dot" /> YOUR STARTING POINT</div>
          <h1>First, a little about <span className="serif-accent">you.</span></h1>
          <p>There are no right answers. Your details help us find career paths worth exploring — not make a decision for you.</p>
          <button className="text-link profile-demo-button" type="button" onClick={loadNyraDemo}>Load Nyra demo profile</button>
        </div>

        <form className="profile-form" onSubmit={handleSubmit}>
          <section className="form-section">
            <div className="form-section-heading">
              <span className="form-section-icon"><UserRound size={17} /></span>
              <div><h2>Your background</h2><p>A little context for your starting point.</p></div>
              <span className="form-step-number">01</span>
            </div>
            <div className="form-fields form-fields-two">
              <label className="text-field">
                <span>What should we call you?</span>
                <input
                  autoComplete="given-name"
                  maxLength={60}
                  minLength={2}
                  placeholder="Your first name"
                  required
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                />
              </label>
              <label className="text-field">
                <span>Area of study</span>
                <input
                  maxLength={120}
                  minLength={2}
                  placeholder="e.g. Economics, Computer Science"
                  required
                  value={fieldOfStudy}
                  onChange={(event) => setFieldOfStudy(event.target.value)}
                />
              </label>
              <label className="text-field">
                <span>Current education level</span>
                <select
                  value={educationLevel}
                  onChange={(event) => setEducationLevel(event.target.value as EducationLevel)}
                >
                  {educationLevels.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                </select>
              </label>
            </div>
          </section>

          <section className="form-section">
            <div className="form-section-heading">
              <span className="form-section-icon"><GraduationCap size={18} /></span>
              <div><h2>What feels like you?</h2><p>Pick a few things you enjoy or feel curious about.</p></div>
              <span className="form-step-number">02</span>
            </div>
            <ChoiceGroup
              title="Interests"
              hint="Choose at least one."
              options={interests}
              selected={selectedInterests}
              onChange={(value) => setSelectedInterests(toggleChoice(selectedInterests, value))}
              columns={2}
            />
            <ChoiceGroup
              title="Skills you already have"
              hint="Optional — you can keep building these as you explore."
              options={skills}
              selected={selectedSkills}
              onChange={(value) => setSelectedSkills(toggleChoice(selectedSkills, value))}
              columns={3}
            />
            <div className="profile-rating-section">
              <h3>Skill proficiency</h3><p>Rate what you know today. You can leave untouched skills at the neutral middle value.</p>
              <div className="profile-rating-grid">{skillFields.map(field => <RatingControl key={field.key} title={field.label} value={skillRatings[field.key]} onChange={value => setSkillRatings(current => ({ ...current, [field.key]: value }))} />)}</div>
            </div>
          </section>

          <section className="form-section">
            <div className="form-section-heading">
              <span className="form-section-icon"><Check size={17} /></span>
              <div><h2>Your future, your terms</h2><p>Think about the kind of work and life you want.</p></div>
              <span className="form-step-number">03</span>
            </div>
            <ChoiceGroup
              title="Work preferences"
              hint="Choose at least one."
              options={workPreferences}
              selected={selectedWorkPreferences}
              onChange={(value) => setSelectedWorkPreferences(toggleChoice(selectedWorkPreferences, value))}
              columns={2}
            />
            <div className="profile-rating-section">
              <h3>What matters most to you?</h3><p>1 = low priority · 5 = very high priority</p>
              <div className="profile-rating-grid">{priorityFields.map(field => <RatingControl key={field.key} title={field.label} value={priorityRatings[field.key]} ratingLabels={["Low", "Somewhat low", "Medium", "High", "Very high"]} onChange={value => setPriorityRatings(current => ({ ...current, [field.key]: value }))} />)}</div>
            </div>
            <div className="profile-rating-section">
              <h3>How do you like to work?</h3><p>1 = very low preference · 5 = very high preference. Coding uses a specific scale.</p>
              <div className="profile-rating-grid">{preferenceFields.map(field => <RatingControl key={field.key} title={field.label} hint={field.hint} value={preferenceRatings[field.key]} ratingLabels={field.key === "coding" ? ["Low/no coding", "Prefer low coding", "Some coding", "Technical work", "Enjoy technical"] : ["Very low", "Low", "Moderate", "High", "Very high"]} onChange={value => setPreferenceRatings(current => ({ ...current, [field.key]: value }))} />)}</div>
            </div>
            <ChoiceGroup
              title="Career priorities"
              hint="What matters most to you? Choose at least one."
              options={careerPriorities}
              selected={selectedPriorities}
              onChange={(value) => setSelectedPriorities(toggleChoice(selectedPriorities, value))}
              columns={2}
            />
          </section>

          {(validationError || error) && (
            <p className="form-error" role="alert">{validationError ?? error}</p>
          )}
          <div className="form-submit-row">
            <p><span /> You can update your answers whenever you like.</p>
            <button className="button button-dark button-large" type="submit" disabled={isSaving}>
              {isSaving ? "Building your CareerTwin…" : "Build my CareerTwin"}
              {!isSaving && <ArrowRight size={17} />}
            </button>
          </div>
        </form>
        <p className="profile-disclaimer">Your career matches are exploratory suggestions based on your answers — not a score, prediction, or guarantee.</p>
      </div>
    </main>
  );
}
