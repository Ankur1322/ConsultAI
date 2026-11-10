const app = document.querySelector("#app");
const state = { sessionId: null, discovery: null };

app.insertAdjacentHTML(
  "beforeend",
  `
    <form id="session-form">
      <label>Vertical <select name="vertical">
        <option value="invoice_to_pay">Invoice to pay</option>
        <option value="customer_support">Customer support</option>
      </select></label>
      <label>Process description <textarea name="process_description" required></textarea></label>
      <button type="submit">Start analysis</button>
    </form>
    <section id="workspace" hidden>
      <h2>Discovery</h2><form id="discovery-form"></form>
      <button id="requirements-button">Generate requirements</button>
      <h2>Evidence</h2>
      <form id="source-form">
        <input name="title" placeholder="Source title" required />
        <textarea name="text" placeholder="Paste trusted evidence" required></textarea>
        <button>Add source</button>
      </form>
      <form id="research-form">
        <input name="query" placeholder="Research question" required />
        <button>Research</button>
      </form>
      <button id="run-button">Run full workflow</button>
      <button id="approve-button" hidden>Approve human review</button>
    </section>
    <pre id="status" aria-live="polite"></pre>
    <pre id="result"></pre>
  `,
);

const status = document.querySelector("#status");
const result = document.querySelector("#result");
const show = (value) => { result.textContent = JSON.stringify(value, null, 2); };
const request = async (path, options = {}) => {
  const response = await fetch(path, { headers: { "content-type": "application/json" }, ...options });
  const body = await response.json();
  if (!response.ok) throw new Error(body.detail || "Request failed");
  return body;
};

document.querySelector("#session-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const form = new FormData(event.currentTarget);
    const payload = Object.fromEntries(form);
    const created = await request("/api/sessions", { method: "POST", body: JSON.stringify(payload) });
    state.sessionId = created.session.id;
    state.discovery = await request("/api/discovery", { method: "POST", body: JSON.stringify(payload) });
    const discoveryForm = document.querySelector("#discovery-form");
    discoveryForm.replaceChildren(...state.discovery.questions.map((question) => {
      const label = document.createElement("label");
      label.textContent = question.text;
      const input = document.createElement("input");
      input.name = question.id;
      label.append(input);
      return label;
    }));
    document.querySelector("#workspace").hidden = false;
    status.textContent = `Session ${state.sessionId} created.`;
  } catch (error) { status.textContent = error.message; }
});

document.querySelector("#requirements-button").addEventListener("click", async () => {
  try {
    const answers = Object.fromEntries(new FormData(document.querySelector("#discovery-form")));
    const description = document.querySelector('[name="process_description"]').value;
    show(await request("/api/requirements", {
      method: "POST", body: JSON.stringify({ process_description: description, discovery_answers: answers }),
    }));
    status.textContent = "Requirements generated.";
  } catch (error) { status.textContent = error.message; }
});

document.querySelector("#source-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const payload = Object.fromEntries(new FormData(event.currentTarget));
    status.textContent = `Source added: ${(await request(`/api/sessions/${state.sessionId}/sources`, {
      method: "POST", body: JSON.stringify(payload),
    })).source_id}`;
    event.currentTarget.reset();
  } catch (error) { status.textContent = error.message; }
});

document.querySelector("#research-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const payload = Object.fromEntries(new FormData(event.currentTarget));
    show(await request(`/api/sessions/${state.sessionId}/research`, {
      method: "POST", body: JSON.stringify(payload),
    }));
    status.textContent = "Research summary generated with citation status.";
  } catch (error) { status.textContent = error.message; }
});

document.querySelector("#run-button").addEventListener("click", async () => {
  try {
    const body = await request(`/api/sessions/${state.sessionId}/run`, { method: "POST", body: "{}" });
    show(body.result);
    const review = body.session.status === "review";
    document.querySelector("#approve-button").hidden = !review;
    status.textContent = review ? "Waiting for human review." : "Workflow completed.";
  } catch (error) { status.textContent = error.message; }
});

document.querySelector("#approve-button").addEventListener("click", async () => {
  try {
    const body = await request(`/api/sessions/${state.sessionId}/review`, {
      method: "POST", body: JSON.stringify({ approved: true }),
    });
    show(body.result);
    document.querySelector("#approve-button").hidden = true;
    status.textContent = "Human review approved; workflow completed.";
  } catch (error) { status.textContent = error.message; }
});
