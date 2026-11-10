const app = document.querySelector("#app");

app.insertAdjacentHTML(
  "beforeend",
  `
    <form id="session-form">
      <label>
        Vertical
        <select name="vertical">
          <option value="invoice_to_pay">Invoice to pay</option>
          <option value="customer_support">Customer support</option>
        </select>
      </label>
      <label>
        Process description
        <textarea name="process_description" required></textarea>
      </label>
      <button type="submit">Start analysis</button>
    </form>
    <pre id="status" aria-live="polite"></pre>
  `,
);

document.querySelector("#session-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const response = await fetch("/api/sessions", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(Object.fromEntries(form)),
  });
  const payload = await response.json();
  document.querySelector("#status").textContent = response.ok
    ? `Session created: ${payload.session.id}`
    : payload.detail;
});
