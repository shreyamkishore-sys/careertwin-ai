import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  ArrowDown,
  ArrowRight,
  ArrowUpRight,
  BarChart3,
  Check,
  ChevronDown,
  Compass,
  Menu,
  Sparkles,
  X,
} from "lucide-react";
import { ApiError, generateCareerTwin, getCurrentUser, getProfile, logIn, logOut, runDemoMarketUpdate, saveProfile, signUp } from "./api";
import { AuthPage, type AuthCredentials } from "./components/AuthPage";
import { Brand } from "./components/Brand";
import { CareerTwinDashboard } from "./components/CareerTwinDashboard";
import { StudentProfileForm } from "./components/StudentProfileForm";
import type {
  CareerTwin,
  SimulationMarketCode,
  StudentProfile,
  StudentProfileInput,
  AuthUser,
} from "./types";
import { clearJourneySession, readJourneySession, useJourneyState, type AppScreen } from "./state/journeySession";

const navLinks = [
  { label: "How it works", href: "#how-it-works" },
  { label: "Explore careers", href: "#explore" },
  { label: "Why CareerTwin", href: "#why-careertwin" },
];

const steps = [
  {
    number: "01",
    title: "Get to know you",
    description:
      "Share your interests, strengths, priorities, and the kind of life you want your work to support.",
    icon: Compass,
  },
  {
    number: "02",
    title: "Meet your CareerTwin",
    description:
      "See career paths that fit your profile, with a clear explanation behind every match.",
    icon: Sparkles,
  },
  {
    number: "03",
    title: "Try on a future",
    description:
      "Change your priorities and compare how different choices could play out over the next decade.",
    icon: BarChart3,
  },
];

function App() {
  const routerNavigate = useNavigate();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const [page, setPageState] = useState<"loading" | "login" | "signup" | AppScreen>("loading");
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isRestoringAuth, setIsRestoringAuth] = useState(true);
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [profile, setProfile] = useState<StudentProfile | undefined>();
  const [careerTwin, setCareerTwin] = useState<CareerTwin | null>(null);
  const [, setActiveProfileId] = useJourneyState("profileId", null);
  const [selectedMarket, setSelectedMarket] = useJourneyState("market", "IN" as SimulationMarketCode);
  const [isRefreshingMarket, setIsRefreshingMarket] = useState(false);
  const marketRequestId = useRef(0);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function navigate(nextPage: "home" | "profile" | "dashboard" | "login" | "signup", historyMode: "push" | "replace" = "push") {
    setPageState(nextPage);
    const paths = { home: "/", profile: "/profile", dashboard: "/career-twin", login: "/login", signup: "/signup" };
    routerNavigate(paths[nextPage], { replace: historyMode === "replace" });
  }

  useEffect(() => {
    const path = location.pathname.replace(/\/$/, "") || "/";
    if (path === "/career-twin" || path.startsWith("/career-twin/")) {
      if (user) setPageState("dashboard");
      return;
    }
    if (path === "/profile") { if (user) setPageState("profile"); return; }
    if (path === "/signup") { if (!user) setPageState("signup"); return; }
    if (path === "/login") { if (!user) setPageState("login"); return; }
    if (path === "/" && user) setPageState("home");
  }, [location.pathname, user]);

  function startOver() {
    clearJourneySession();
    setActiveProfileId(null);
    setSelectedMarket("IN");
    setCareerTwin(null);
    setError(null);
    setMenuOpen(false);
    navigate(profile ? "profile" : "home", "replace");
  }

  useEffect(() => {
    let active = true;
    async function restoreAuthentication() {
      try {
        const authenticatedUser = await getCurrentUser();
        if (!active) return;
        let marketToRestore = selectedMarket;
        if (readJourneySession().profileId !== authenticatedUser.profile_id) {
          clearJourneySession();
          setSelectedMarket("IN");
          marketToRestore = "IN";
        }
        setUser(authenticatedUser);
        setActiveProfileId(authenticatedUser.profile_id);
        if (!authenticatedUser.profile_id) {
          setProfile(undefined);
          setCareerTwin(null);
          setPageState("profile");
          routerNavigate("/profile", { replace: true });
          return;
        }
        const savedProfile = await getProfile(authenticatedUser.profile_id);
        if (active) {
          setProfile(savedProfile);
          const savedCareerTwin = await generateCareerTwin(savedProfile.id, marketToRestore);
          if (!active) return;
          setCareerTwin(savedCareerTwin);
          const path = location.pathname.replace(/\/$/, "") || "/";
          const legacyScreen = new URLSearchParams(window.location.search).get("screen");
          const legacyView = new URLSearchParams(window.location.search).get("view");
          const initialScreen: AppScreen = path === "/profile" || legacyScreen === "profile"
            ? "profile"
            : path === "/" && legacyScreen === "home" ? "home" : "dashboard";
          setPageState(initialScreen);
          if (initialScreen === "dashboard" && path.startsWith("/career-twin/")) return;
          const legacyRoutes: Record<string, string> = {
            overview: "/career-twin", "career-fit": "/career-twin/career-fit", compare: "/career-twin/comparison",
            "what-if": "/career-twin/what-if", simulation: "/career-twin/simulation", salary: "/career-twin/salary",
            skills: "/career-twin/skills", "development-plan": "/career-twin/development-plan", switching: "/career-twin/switching",
            "ai-risk": "/career-twin/ai-risk", market: "/career-twin/market", "trade-offs": "/career-twin/trade-offs",
            "education-roi": "/career-twin/education-roi",
          };
          const destination = initialScreen === "dashboard"
            ? legacyScreen === "dashboard" && legacyView && legacyRoutes[legacyView] ? legacyRoutes[legacyView] : "/career-twin"
            : initialScreen === "profile" ? "/profile" : "/";
          routerNavigate(destination, { replace: true });
        }
      } catch (restoreError) {
        if (!active) return;
        if (restoreError instanceof ApiError && restoreError.status === 401) {
          clearJourneySession();
          setActiveProfileId(null);
          setUser(null);
          navigate("login", "replace");
        } else if (restoreError instanceof ApiError && restoreError.status === 404) {
          setUser(null);
          navigate("login", "replace");
          setError("We couldn’t restore your saved profile. Please log in again.");
        } else {
          setUser(null);
          navigate("login", "replace");
          setError(restoreError instanceof Error ? restoreError.message : "We couldn't restore your account.");
        }
      } finally {
        if (active) setIsRestoringAuth(false);
      }
    }
    void restoreAuthentication();
    return () => { active = false; };
  }, []);

  useEffect(() => {
    function handleUnauthorized() {
      clearJourneySession();
      setActiveProfileId(null);
      setProfile(undefined);
      setCareerTwin(null);
      setUser(null);
      setError("Your session has expired. Please log in again.");
      navigate("login", "replace");
    }
    window.addEventListener("careertwin:unauthorized", handleUnauthorized);
    return () => window.removeEventListener("careertwin:unauthorized", handleUnauthorized);
  }, [setActiveProfileId]);

  useEffect(() => {
    if (page !== "dashboard" || !careerTwin || !window.location.hash) return;
    const targetId = decodeURIComponent(window.location.hash.slice(1));
    const timeout = window.setTimeout(() => document.getElementById(targetId)?.scrollIntoView(), 0);
    return () => window.clearTimeout(timeout);
  }, [page, careerTwin]);

  async function handleSaveProfile(profileInput: StudentProfileInput) {
    setIsSaving(true);
    setError(null);
    try {
      const savedProfile = await saveProfile(profileInput, profile?.id);
      setActiveProfileId(savedProfile.id);
      setProfile(savedProfile);
      setUser(current => current ? { ...current, profile_id: savedProfile.id } : current);
      const generatedTwin = await generateCareerTwin(savedProfile.id, selectedMarket);
      setCareerTwin(generatedTwin);
      navigate("dashboard");
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "We couldn't save your profile.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleAuthSubmit(credentials: AuthCredentials) {
    setIsAuthenticating(true);
    setError(null);
    try {
      const authenticatedUser = credentials.name
        ? await signUp({ name: credentials.name, email: credentials.email, password: credentials.password })
        : await logIn({ email: credentials.email, password: credentials.password });
      let marketToRestore = selectedMarket;
      if (readJourneySession().profileId !== authenticatedUser.profile_id || !authenticatedUser.profile_id) {
        clearJourneySession();
        setSelectedMarket("IN");
        marketToRestore = "IN";
      }
      setError(null);
      if (!authenticatedUser.profile_id) {
        setUser(authenticatedUser);
        setActiveProfileId(null);
        setProfile(undefined);
        setCareerTwin(null);
        navigate("profile", "replace");
        return;
      }
      const savedProfile = await getProfile(authenticatedUser.profile_id);
      const savedCareerTwin = await generateCareerTwin(savedProfile.id, marketToRestore);
      setUser(authenticatedUser);
      setActiveProfileId(authenticatedUser.profile_id);
      setProfile(savedProfile);
      setCareerTwin(savedCareerTwin);
      navigate("dashboard", "replace");
    } catch (authError) {
      setError(authError instanceof Error ? authError.message : "We couldn't complete that request.");
    } finally {
      setIsAuthenticating(false);
    }
  }

  async function handleLogout() {
    setError(null);
    try {
      await logOut();
      clearJourneySession();
      setActiveProfileId(null);
      setUser(null);
      setProfile(undefined);
      setCareerTwin(null);
      setSelectedMarket("IN");
      navigate("login", "replace");
    } catch (logoutError) {
      setError(logoutError instanceof Error ? logoutError.message : "We couldn't log out right now. Please try again.");
    }
  }

  async function handleMarketChange(market: SimulationMarketCode) {
    if (!profile) return;
    const requestId = ++marketRequestId.current;
    setSelectedMarket(market);
    setIsRefreshingMarket(true);
    setError(null);
    try {
      const updatedTwin = await generateCareerTwin(profile.id, market);
      if (requestId === marketRequestId.current) setCareerTwin(updatedTwin);
    } catch (marketError) {
      if (requestId === marketRequestId.current) {
        setError(marketError instanceof Error ? marketError.message : "We couldn't recalculate market-aligned careers.");
        setSelectedMarket(careerTwin?.market.code === "US" ? "US" : "IN");
      }
    } finally {
      if (requestId === marketRequestId.current) setIsRefreshingMarket(false);
    }
  }

  async function handleDemoMarketUpdate(market: SimulationMarketCode, careerId: string, action: "apply" | "reset" = "apply") {
    if (!profile) return null;
    const requestId = ++marketRequestId.current;
    setIsRefreshingMarket(true);
    setError(null);
    try {
      const result = await runDemoMarketUpdate(profile.id, market, careerId, action);
      if (requestId === marketRequestId.current) setCareerTwin(result.career_twin);
      return result;
    } catch (marketError) {
      if (requestId === marketRequestId.current) {
        setError(marketError instanceof Error ? marketError.message : "We couldn't update the illustrative market record.");
      }
      return null;
    } finally {
      if (requestId === marketRequestId.current) setIsRefreshingMarket(false);
    }
  }

  function openProfile() {
    setMenuOpen(false);
    setError(null);
    navigate("profile");
  }

  if (isRestoringAuth || page === "loading") {
    return (
      <main className="loading-screen">
        <Brand />
        <span className="loading-spinner" />
        <p>Getting your CareerTwin ready…</p>
      </main>
    );
  }

  if (!user) {
    return <AuthPage
      mode={page === "signup" ? "signup" : "login"}
      busy={isAuthenticating}
      error={error}
      onModeChange={nextMode => { setError(null); navigate(nextMode); }}
      onSubmit={handleAuthSubmit}
    />;
  }

  if (page === "profile") {
    return (
      <div className="min-h-screen bg-cream text-ink">
        <header className="site-header">
          <div className="nav-shell">
            <Brand onClick={(event) => { event.preventDefault(); navigate("home"); }} />
            <div className="auth-profile-actions"><button type="button" className="text-link" onClick={() => navigate("home")}>Back to home</button><button type="button" className="text-link" onClick={handleLogout}>Log out</button></div>
          </div>
        </header>
        <StudentProfileForm
          initialProfile={profile}
          isSaving={isSaving}
          error={error}
          onBack={() => navigate(profile ? "dashboard" : "home")}
          onSubmit={handleSaveProfile}
        />
      </div>
    );
  }

  if (page === "dashboard" && careerTwin) {
    return (
      <CareerTwinDashboard
        careerTwin={careerTwin}
        marketCode={selectedMarket}
        onMarketChange={handleMarketChange}
        marketRefreshing={isRefreshingMarket}
        marketError={error}
          onDemoMarketUpdate={handleDemoMarketUpdate}
          onEditProfile={openProfile}
          onStartOver={startOver}
          onLogout={handleLogout}
          accountName={user.name}
          accountEmail={user.email}
      />
    );
  }

  return (
    <div className="min-h-screen overflow-hidden bg-cream text-ink">
      <header className="site-header">
        <div className="nav-shell">
          <Brand />
          <nav className={`nav-links ${menuOpen ? "nav-links-open" : ""}`} aria-label="Main navigation">
            {navLinks.map((link) => (
              <a key={link.href} href={link.href} onClick={() => setMenuOpen(false)}>
                {link.label}
              </a>
            ))}
            <a className="nav-mobile-cta" href="#get-started" onClick={(event) => { event.preventDefault(); openProfile(); }}>
              Get started <ArrowRight size={15} />
            </a>
          </nav>
          <a className="button button-dark nav-cta" href="#get-started" onClick={(event) => { event.preventDefault(); openProfile(); }}>
            Get started <ArrowUpRight size={15} />
          </a>
          <button className="text-link home-logout" type="button" onClick={handleLogout}>Log out</button>
          <button
            className="menu-toggle"
            type="button"
            aria-label={menuOpen ? "Close navigation menu" : "Open navigation menu"}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen(!menuOpen)}
          >
            {menuOpen ? <X size={21} /> : <Menu size={21} />}
          </button>
        </div>
      </header>

      <main>
        {error && <div className="home-error" role="alert">{error}</div>}
        <section className="hero section-shell" id="explore">
          <div className="hero-copy">
            <div className="eyebrow"><span className="eyebrow-dot" /> A clearer way to choose your career</div>
            <h1>
              Your future
              <br />
              isn&apos;t <span className="serif-accent">one-size-fits-all.</span>
            </h1>
            <p className="hero-description">
              Get to know the careers that fit <em>you</em> — then see where each one could take you.
              No crystal ball. Just clearer possibilities.
            </p>
            <div className="hero-actions" id="get-started">
              <a className="button button-dark button-large" href="#get-started" onClick={(event) => { event.preventDefault(); openProfile(); }}>
                Explore your future <ArrowRight size={17} />
              </a>
              <a className="text-link" href="#how-it-works">
                See how it works <ArrowDown size={15} />
              </a>
            </div>
            <div className="hero-note">
              <span className="avatar-stack" aria-hidden="true">
                <span>N</span><span>A</span><span>M</span>
              </span>
              <span>Made for the path you&apos;re still figuring out.</span>
            </div>
          </div>

          <div className="future-card-wrap" aria-label="Example career future visualization">
            <div className="orbit orbit-one" />
            <div className="orbit orbit-two" />
            <div className="future-card">
              <div className="future-card-top">
                <div>
                  <div className="card-overline">YOUR CAREER SNAPSHOT</div>
                  <div className="card-heading">A future in product</div>
                </div>
                <span className="match-pill"><Sparkles size={13} /> Strong fit</span>
              </div>

              <div className="pathway">
                <div className="pathway-line" />
                <div className="pathway-item">
                  <span className="pathway-dot pathway-dot-filled" />
                  <div><span className="pathway-role">Product Analyst</span><span className="pathway-time">NOW · STARTING POINT</span></div>
                </div>
                <div className="pathway-item">
                  <span className="pathway-dot" />
                  <div><span className="pathway-role">Senior Product Analyst</span><span className="pathway-time">2–4 YEARS</span></div>
                </div>
                <div className="pathway-item">
                  <span className="pathway-dot" />
                  <div><span className="pathway-role">Product Manager</span><span className="pathway-time">5–8 YEARS</span></div>
                </div>
              </div>

              <div className="snapshot-bottom">
                <div className="snapshot-metric">
                  <span>10-YR OUTLOOK</span>
                  <strong>Room to grow <ArrowUpRight size={14} /></strong>
                </div>
                <div className="mini-chart" aria-hidden="true">
                  <span style={{ height: "28%" }} /><span style={{ height: "39%" }} />
                  <span style={{ height: "36%" }} /><span style={{ height: "54%" }} />
                  <span style={{ height: "49%" }} /><span style={{ height: "68%" }} />
                  <span style={{ height: "61%" }} /><span style={{ height: "83%" }} />
                  <span style={{ height: "76%" }} /><span style={{ height: "100%" }} />
                </div>
              </div>
              <div className="illustrative-note"><span /> Illustrative path, not a prediction</div>
            </div>
            <div className="floating-note"><span className="floating-check"><Check size={13} /></span><span><strong>Made for your priorities</strong><small>Not someone else&apos;s checklist</small></span></div>
            <div className="floating-sparkle"><Sparkles size={20} /></div>
          </div>
        </section>

        <section className="trust-strip" aria-label="CareerTwin approach">
          <div className="trust-inner">
            <p>A future-planning tool that puts <em>your life</em> in the picture.</p>
            <div className="trust-points">
              <span><Check size={14} /> Your priorities, first</span>
              <span><Check size={14} /> Reasons behind every fit</span>
              <span><Check size={14} /> Possibilities, not promises</span>
            </div>
          </div>
        </section>

        <section className="how-section section-shell" id="how-it-works">
          <div className="section-heading">
            <div>
              <div className="eyebrow"><span className="eyebrow-dot" /> YOUR NEXT CHAPTER, YOUR WAY</div>
              <h2>Big decisions feel lighter<br />when you can <span className="serif-accent">see the options.</span></h2>
            </div>
            <p>CareerTwin helps you move from “what should I do?” to “what could my life look like?” — one possibility at a time.</p>
          </div>
          <div className="steps-grid">
            {steps.map(({ number, title, description, icon: Icon }) => (
              <article className="step-card" key={number}>
                <div className="step-top"><span>{number}</span><Icon size={20} strokeWidth={1.6} /></div>
                <h3>{title}</h3>
                <p>{description}</p>
                <a href="#get-started" aria-label={`Get started: ${title}`} onClick={(event) => { event.preventDefault(); openProfile(); }}><ArrowUpRight size={16} /></a>
              </article>
            ))}
          </div>
        </section>

        <section className="closing-section section-shell" id="why-careertwin">
          <div className="closing-card">
            <div className="closing-decoration"><span /><span /><span /></div>
            <div className="closing-copy">
              <div className="eyebrow"><span className="eyebrow-dot" /> YOUR FUTURE IS YOURS TO SHAPE</div>
              <h2>Less guessing.<br /><span className="serif-accent">More exploring.</span></h2>
              <p>There isn&apos;t one right path. There are paths that feel more like you.</p>
              <a className="button button-light button-large" href="#get-started" onClick={(event) => { event.preventDefault(); openProfile(); }}>Find your possibilities <ArrowRight size={17} /></a>
            </div>
            <div className="closing-caption"><ChevronDown size={15} /> YOUR NEXT CHAPTER STARTS HERE</div>
          </div>
        </section>
      </main>

      <footer className="site-footer">
        <Brand />
        <p>Explore a future that feels like yours.</p>
        <span>Academic prototype · Career paths and outcomes are illustrative estimates, not guarantees.</span>
      </footer>
    </div>
  );
}

export default App;
