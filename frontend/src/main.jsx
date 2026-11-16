import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const initialForm = {
  vertical: "invoice_to_pay",
  process_description: "",
};

function Icon({ name, size = 18 }) {
  const paths = {
    activity: <><path d="M3 12h4l2-7 4 14 2-7h6" /></>,
    arrow: <><path d="M5 12h14" /><path d="m13 6 6 6-6 6" /></>,
    check: <><path d="m5 12 4 4L19 6" /></>,
    chevron: <path d="m7 10 5 5 5-5" />,
    file: <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><path d="M14 2v6h6" /><path d="M8 13h8M8 17h6" /></>,
    grid: <><rect x="4" y="4" width="6" height="6" rx="1" /><rect x="14" y="4" width="6" height="6" rx="1" /><rect x="4" y="14" width="6" height="6" rx="1" /><rect x="14" y="14" width="6" height="6" rx="1" /></>,
    plus: <><path d="M12 5v14M5 12h14" /></>,
    search: <><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></>,
    shield: <><path d="M12 3 20 7v5c0 5-3.5 8-8 9-4.5-1-8-4-8-9V7z" /><path d="m9 12 2 2 4-4" /></>,
    spark: <><path d="m12 3 1.5 6.5L20 12l-6.5 1.5L12 20l-1.5-6.5L4 12l6.5-2.5z" /></>,
    upload: <><path d="M12 16V4" /><path d="m7 9 5-5 5 5" /><path d="M5 20h14" /></>,
    user: <><circle cx="12" cy="8" r="3" /><path d="M5 20a7 7 0 0 1 14 0" /></>,
  };
  return <svg aria-hidden="true" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>;
}

const request = async (path, options = {}) => {
  const response = await fetch(path, {
    headers: { "content-type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const body = await response.json();
  if (!response.ok) throw new Error(body.detail || "Request failed");
  return body;
};

function App() {
  const [form, setForm] = useState(initialForm);
  const [sessionId, setSessionId] = useState(null);
  const [discovery, setDiscovery] = useState(null);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [source, setSource] = useState({ title: "", text: "" });
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState({ type: "idle", message: "Ready when you are." });
  const [busy, setBusy] = useState(false);

  const updateForm = (event) => setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  const run = async (work, success) => {
    setBusy(true);
    setStatus({ type: "working", message: "ConsultAI is thinking..." });
    try {
      await work();
      setStatus({ type: "success", message: success });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setBusy(false);
    }
  };

  const createSession = (event) => {
    event.preventDefault();
    run(async () => {
      const created = await request("/api/sessions", { method: "POST", body: JSON.stringify(form) });
      const nextDiscovery = await request("/api/discovery", { method: "POST", body: JSON.stringify(form) });
      setSessionId(created.session.id);
      setDiscovery(nextDiscovery);
      setAnswers({});
    }, "Workspace created. Add context to sharpen the analysis.");
  };

  const generateRequirements = () => run(async () => {
    const body = await request("/api/requirements", {
      method: "POST",
      body: JSON.stringify({ process_description: form.process_description, discovery_answers: answers }),
    });
    setResult(body);
  }, "Requirements generated from your process context.");

  const addSource = (event) => {
    event.preventDefault();
    run(async () => {
      await request(`/api/sessions/${sessionId}/sources`, { method: "POST", body: JSON.stringify(source) });
      setSource({ title: "", text: "" });
    }, "Evidence added to this workspace.");
  };

  const research = (event) => {
    event.preventDefault();
    run(async () => {
      const body = await request(`/api/sessions/${sessionId}/research`, { method: "POST", body: JSON.stringify({ query }) });
      setResult(body);
    }, "Research summary generated with citation status.");
  };

  const runWorkflow = () => run(async () => {
    const body = await request(`/api/sessions/${sessionId}/run`, { method: "POST", body: "{}" });
    setResult(body.result);
  }, "Workflow complete. Review the generated opportunity map.");

  const hasWorkspace = Boolean(sessionId);
  const isComplete = Boolean(result);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><Icon name="spark" size={18} /></div>
          <span>consult<span>ai</span></span>
        </div>
        <div className="workspace-switcher">
          <span className="workspace-dot" /> Local workspace <Icon name="chevron" size={15} />
        </div>
        <nav className="side-nav" aria-label="Primary navigation">
          <p className="nav-label">Workspace</p>
          <a className="nav-item active" href="#overview"><Icon name="grid" /> Overview</a>
          <a className="nav-item" href="#evidence"><Icon name="file" /> Evidence <span className="nav-count">0</span></a>
          <a className="nav-item" href="#activity"><Icon name="activity" /> Activity</a>
          <p className="nav-label nav-label-spaced">Manage</p>
          <a className="nav-item" href="#security"><Icon name="shield" /> Security</a>
        </nav>
        <div className="sidebar-footer">
          <div className="system-status"><span className="pulse" /> All systems operational</div>
          <div className="profile"><div className="avatar">A</div><div><strong>Analyst workspace</strong><small>Local-first mode</small></div><Icon name="chevron" size={15} /></div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumbs"><span>Workspace</span><Icon name="chevron" size={14} /><strong>Overview</strong></div>
          <div className="top-actions"><span className="live-tag"><span className="pulse" /> Live</span><button className="icon-button" aria-label="Search"><Icon name="search" /></button><button className="avatar small" aria-label="Open profile">A</button></div>
        </header>

        <div className="content-wrap" id="overview">
          <section className="hero">
            <div className="hero-copy">
              <div className="eyebrow"><span className="eyebrow-line" /> PROCESS INTELLIGENCE</div>
              <h1>Turn operational<br /><em>friction into flow.</em></h1>
              <p>Map the work behind your business, surface high-impact AI opportunities, and keep every recommendation grounded in evidence.</p>
              <div className="hero-meta"><span><Icon name="shield" size={15} /> Private by default</span><span><Icon name="activity" size={15} /> Deterministic analysis</span></div>
            </div>
            <div className="hero-visual" aria-label="Analysis pipeline preview">
              <div className="orbit orbit-one" /><div className="orbit orbit-two" />
              <div className="visual-core"><Icon name="spark" size={28} /><span>AI<br />WORKFLOW</span></div>
              <div className="signal signal-one"><span className="signal-dot green" /> Context captured</div>
              <div className="signal signal-two"><span className="signal-dot amber" /> Evidence checked</div>
              <div className="signal signal-three"><span className="signal-dot blue" /> Opportunities ranked</div>
            </div>
          </section>

          <section className="metrics" aria-label="Workspace metrics">
            <div className="metric"><span className="metric-label">ANALYSIS STATUS</span><strong>{hasWorkspace ? "In progress" : "Ready to begin"}</strong><span className="metric-note"><span className="signal-dot green" /> Local engine online</span></div>
            <div className="metric"><span className="metric-label">EVIDENCE COVERAGE</span><strong>{hasWorkspace ? "Collecting" : "Not started"}</strong><span className="metric-note">Citations stay attached to claims</span></div>
            <div className="metric"><span className="metric-label">WORKSPACE MODE</span><strong>Private local</strong><span className="metric-note"><Icon name="shield" size={13} /> No data leaves this stack</span></div>
          </section>

          {!hasWorkspace ? (
            <section className="card setup-card">
              <div className="section-heading"><div><span className="step-badge">01</span><div><h2>Start with a process</h2><p>Give your analyst a little context. You can refine it as you go.</p></div></div><span className="section-kicker">2 MIN SETUP</span></div>
              <form onSubmit={createSession} className="setup-form">
                <label className="field"><span>Business area</span><div className="select-wrap"><select name="vertical" value={form.vertical} onChange={updateForm}><option value="invoice_to_pay">Invoice to pay</option><option value="customer_support">Customer support</option></select><Icon name="chevron" size={16} /></div></label>
                <label className="field field-wide"><span>What happens today?</span><textarea name="process_description" required value={form.process_description} onChange={updateForm} placeholder="Example: Agents copy invoices from email into the accounting system, then route them for approval..." /></label>
                <div className="form-footer"><span className="helper-text"><Icon name="spark" size={14} /> Specific details lead to better opportunities.</span><button className="primary-button" disabled={busy}>Create workspace <Icon name="arrow" size={17} /></button></div>
              </form>
            </section>
          ) : (
            <div className="workspace-grid">
              <section className="card discovery-card">
                <div className="section-heading"><div><span className="step-badge">02</span><div><h2>Discover the workflow</h2><p>Answer a few focused questions to reveal the real shape of the work.</p></div></div><span className="status-chip"><span className="signal-dot green" /> Active</span></div>
                <div className="question-list">
                  {(discovery?.questions || []).map((question) => <label className="question" key={question.id}><span>{question.text}</span><input value={answers[question.id] || ""} onChange={(event) => setAnswers((current) => ({ ...current, [question.id]: event.target.value }))} placeholder="Add context..." /></label>)}
                </div>
                <button className="secondary-button" onClick={generateRequirements} disabled={busy}>Generate requirements <Icon name="arrow" size={16} /></button>
              </section>
              <section className="card evidence-card" id="evidence">
                <div className="section-heading"><div><span className="step-badge">03</span><div><h2>Ground with evidence</h2><p>Bring trusted sources into the conversation.</p></div></div><span className="section-kicker">OPTIONAL</span></div>
                <form onSubmit={addSource} className="compact-form"><label className="field"><span>Source title</span><input required value={source.title} onChange={(event) => setSource({ ...source, title: event.target.value })} placeholder="Invoice policy" /></label><label className="field"><span>Evidence</span><textarea required value={source.text} onChange={(event) => setSource({ ...source, text: event.target.value })} placeholder="Paste a policy, SOP, or trusted note..." /></label><button className="ghost-button" disabled={busy}><Icon name="upload" size={16} /> Add source</button></form>
                <form onSubmit={research} className="research-row"><input required value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ask a research question..." /><button className="icon-submit" aria-label="Research" disabled={busy}><Icon name="arrow" size={17} /></button></form>
              </section>
              <section className="card workflow-card">
                <div className="workflow-copy"><span className="step-badge">04</span><div><h2>Run the full analysis</h2><p>Combine discovery, requirements, evidence, and risk into one reviewable workflow.</p></div></div>
                <button className="primary-button" onClick={runWorkflow} disabled={busy}>Run workflow <Icon name="arrow" size={17} /></button>
              </section>
            </div>
          )}

          <section className="lower-grid" id="activity">
            <div className="card output-card">
              <div className="output-header"><div><span className="metric-label">LATEST OUTPUT</span><h2>{isComplete ? "Analysis snapshot" : "Your analysis will appear here"}</h2></div><span className="output-icon"><Icon name="activity" /></span></div>
              {result ? <pre className="result">{JSON.stringify(result, null, 2)}</pre> : <div className="empty-output"><div className="empty-icon"><Icon name="spark" size={22} /></div><p>Start a workspace to see requirements, research summaries, and ranked opportunities.</p></div>}
            </div>
            <div className="card trust-card" id="security"><div className="trust-icon"><Icon name="shield" size={20} /></div><div><h3>Built for responsible analysis</h3><p>Every recommendation is traceable. Sensitive content is redacted before it enters the workflow.</p><a href="#evidence">Explore evidence model <Icon name="arrow" size={14} /></a></div></div>
          </section>
          <div className={`toast ${status.type}`} role="status"><span className="toast-indicator" />{status.message}</div>
        </div>
      </main>
    </div>
  );
}

createRoot(document.getElementById("app")).render(<App />);
