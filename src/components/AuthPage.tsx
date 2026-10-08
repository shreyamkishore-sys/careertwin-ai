import { useState, type FormEvent } from "react";
import { ArrowRight, LockKeyhole, Sparkles } from "lucide-react";
import { Brand } from "./Brand";

export interface AuthCredentials {
  name?: string;
  email: string;
  password: string;
}

interface AuthPageProps {
  mode: "login" | "signup";
  busy: boolean;
  error: string | null;
  onModeChange: (mode: "login" | "signup") => void;
  onSubmit: (credentials: AuthCredentials) => Promise<void>;
}

export function AuthPage({ mode, busy, error, onModeChange, onSubmit }: AuthPageProps) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);
  const signingUp = mode === "signup";

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setValidationError(null);
    if (signingUp && name.trim().length < 2) return setValidationError("Please enter your name.");
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) return setValidationError("Please enter a valid email address.");
    if (!password) return setValidationError("Please enter your password.");
    if (signingUp && password.length < 10) return setValidationError("Use at least 10 characters for your password.");
    if (signingUp && password !== confirmPassword) return setValidationError("Passwords do not match.");
    await onSubmit({ name: signingUp ? name.trim() : undefined, email: email.trim(), password });
  }

  return (
    <main className="auth-screen">
      <div className="auth-topbar"><Brand /></div>
      <section className="auth-layout">
        <div className="auth-story">
          <div className="auth-story-mark"><Sparkles size={15} /> A clearer way to choose your career</div>
          <h1>{signingUp ? <>Start building your<br /><em>career roadmap.</em></> : <>Build a career<br /><em>you’re confident about.</em></>}</h1>
          <p>Bring your strengths, priorities, and possibilities together in one place.</p>
          <div className="auth-story-note"><span><LockKeyhole size={16} /></span><div><strong>Your progress stays yours</strong><small>Your profile is saved privately to your account.</small></div></div>
        </div>

        <div className="auth-card">
          <div className="auth-card-heading">
            <span className="detail-label">CAREERTWIN ACCOUNT</span>
            <h2>{signingUp ? "Create your account" : "Welcome back"}</h2>
            <p>{signingUp ? "A thoughtful next step starts here." : "Log in to pick up where you left off."}</p>
          </div>
          <form onSubmit={submit} noValidate>
            {signingUp && <label className="text-field"><span>Full name</span><input autoComplete="name" value={name} onChange={event => setName(event.target.value)} placeholder="Your name" /></label>}
            <label className="text-field"><span>Email</span><input type="email" autoComplete="email" value={email} onChange={event => setEmail(event.target.value)} placeholder="you@example.com" /></label>
            <label className="text-field"><span>Password</span><input type="password" autoComplete={signingUp ? "new-password" : "current-password"} value={password} onChange={event => setPassword(event.target.value)} placeholder={signingUp ? "At least 10 characters" : "Your password"} /></label>
            {signingUp && <label className="text-field"><span>Confirm password</span><input type="password" autoComplete="new-password" value={confirmPassword} onChange={event => setConfirmPassword(event.target.value)} placeholder="Enter your password again" /></label>}
            {(validationError || error) && <p className="auth-error" role="alert">{validationError || error}</p>}
            <button className="button button-dark auth-submit" type="submit" disabled={busy}>
              {busy ? <><span className="auth-button-spinner" /> {signingUp ? "Creating account…" : "Logging in…"}</> : <>{signingUp ? "Create account" : "Log in"}<ArrowRight size={16} /></>}
            </button>
          </form>
          <p className="auth-switch">{signingUp ? "Already have an account?" : "Don’t have an account?"}{" "}
            <button type="button" onClick={() => { setValidationError(null); onModeChange(signingUp ? "login" : "signup"); }}>{signingUp ? "Log in" : "Create account"}</button>
          </p>
          <p className="auth-privacy">Your account keeps your profile and career journey together.</p>
        </div>
      </section>
      <footer className="auth-footer">Thoughtful possibilities. Your decisions.</footer>
    </main>
  );
}
