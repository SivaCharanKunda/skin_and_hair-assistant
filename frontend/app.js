/**
 * Frontend logic for the Skin & Hair Health Assistant.
 *
 * This is a small vanilla-JS single-page app: it renders the intake form,
 * submits it to the backend's LangGraph-powered API, then renders the
 * result view -- all in the same #app container. No build step needed;
 * open index.html directly or serve this folder with any static server.
 *
 * The backend (a separate Flask app in ../backend) exposes:
 *   POST {API_BASE_URL}/api/analyze  (multipart/form-data)
 *   POST {API_BASE_URL}/api/book     (JSON: { session_id })
 */

const API_BASE_URL = window.API_BASE_URL || "http://127.0.0.1:5000";

const app = document.getElementById("app");

let currentSessionId = null;

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str == null ? "" : String(str);
  return div.innerHTML;
}

function renderIntakeForm() {
  app.innerHTML = `
    <p class="eyebrow">Intake · Skin &amp; Hair</p>
    <h1>Let's take a look at what's going on.</h1>
    <p class="sub">Describe what you're noticing, add a photo if you have one, and get a personalized routine — plus a dermatologist referral and booking if it looks like something to have checked in person.</p>

    <div class="disclaimer">
      This is a demo assistant, not a medical device. It does not diagnose conditions — it flags when a professional opinion is worth getting.
    </div>

    <form id="intake-form" class="card">
      <fieldset>
        <legend>About you</legend>
        <div class="field">
          <label for="user_name">Your name</label>
          <input type="text" id="user_name" name="user_name" placeholder="e.g. Asha">
        </div>
        <div class="field">
          <label for="city">Your city (helps match a nearby dermatologist)</label>
          <input type="text" id="city" name="city" placeholder="e.g. Kurnool">
        </div>
      </fieldset>

      <fieldset>
        <legend>What's the concern?</legend>
        <div class="field radio-row">
          <input type="radio" id="concern_skin" name="concern_type" value="skin" checked>
          <label class="pill checked" id="lbl_skin" for="concern_skin">Skin</label>

          <input type="radio" id="concern_hair" name="concern_type" value="hair">
          <label class="pill" id="lbl_hair" for="concern_hair">Hair</label>
        </div>

        <div class="field">
          <label for="symptoms_text">Describe what you're noticing</label>
          <textarea id="symptoms_text" name="symptoms_text" placeholder="e.g. a dry, itchy patch on my cheek that's been there for a week"></textarea>
        </div>

        <div class="field">
          <label>Photo (optional)</label>
          <label class="upload-box" for="photo">
            Click to choose a photo, or drag one here
            <input type="file" id="photo" name="photo" accept="image/*">
            <span id="file-name"></span>
          </label>
        </div>
      </fieldset>

      <fieldset>
        <legend>A little more detail</legend>
        <div class="grid-2">
          <div class="field">
            <label for="skin_or_hair_type">Type</label>
            <select id="skin_or_hair_type" name="skin_or_hair_type">
              <option value="normal">Normal</option>
              <option value="oily">Oily</option>
              <option value="dry">Dry</option>
              <option value="combination">Combination</option>
              <option value="sensitive">Sensitive</option>
              <option value="acne-prone">Acne-prone</option>
              <option value="curly">Curly</option>
              <option value="colored">Colored/treated</option>
              <option value="damaged">Damaged</option>
              <option value="thinning">Thinning</option>
              <option value="flaky-scalp">Flaky scalp</option>
            </select>
          </div>
          <div class="field">
            <label for="budget">Budget</label>
            <select id="budget" name="budget">
              <option value="low">Low</option>
              <option value="medium" selected>Medium</option>
              <option value="high">High</option>
            </select>
          </div>
        </div>
      </fieldset>

      <button type="submit" class="primary" id="submit-btn">Analyze &amp; get my routine</button>
    </form>
  `;

  document.getElementById("concern_skin").addEventListener("change", updateConcernPills);
  document.getElementById("concern_hair").addEventListener("change", updateConcernPills);
  document.getElementById("photo").addEventListener("change", (e) => {
    document.getElementById("file-name").textContent = e.target.files.length ? e.target.files[0].name : "";
  });
  document.getElementById("intake-form").addEventListener("submit", handleAnalyzeSubmit);
}

function updateConcernPills() {
  const skinChecked = document.getElementById("concern_skin").checked;
  document.getElementById("lbl_skin").classList.toggle("checked", skinChecked);
  document.getElementById("lbl_hair").classList.toggle("checked", !skinChecked);
}

async function handleAnalyzeSubmit(evt) {
  evt.preventDefault();
  const form = evt.target;
  const submitBtn = document.getElementById("submit-btn");
  submitBtn.disabled = true;
  submitBtn.textContent = "Analyzing…";

  try {
    const formData = new FormData(form);
    const res = await fetch(`${API_BASE_URL}/api/analyze`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      throw new Error(`Server responded with ${res.status}`);
    }

    const data = await res.json();
    currentSessionId = data.session_id;
    renderResult(data.result, false);
  } catch (err) {
    submitBtn.disabled = false;
    submitBtn.textContent = "Analyze & get my routine";
    alert(
      "Something went wrong reaching the assistant backend. " +
      "Make sure the backend server is running (see backend/README.md).\n\n" +
      err.message
    );
  }
}

function renderResult(result, justBooked) {
  const riskLevel = result.risk_level || "low";
  const hasImageReading = result.image_analysis && result.image_analysis.redness_score != null;
  const greetingName = result.user_name && result.user_name !== "Guest" ? `, ${escapeHtml(result.user_name)}` : "";

  const reasonsHtml = (result.risk_reasons || [])
    .map((r) => `<li>${escapeHtml(r)}</li>`)
    .join("");

  const routineColsHtml = Object.entries(result.routine || {})
    .filter(([key, value]) => !["notes", "caution"].includes(key) && Array.isArray(value))
    .map(([key, value]) => `
      <div class="routine-col">
        <h4>${escapeHtml(key.replace(/_/g, " "))}</h4>
        <ul>${value.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
      </div>
    `)
    .join("");

  const productsHtml = (result.recommended_products || [])
    .map((p) => `
      <div class="product">
        <span class="name">${escapeHtml(p.name)}</span>
        <span class="budget">${escapeHtml(p.budget)}</span>
      </div>
    `)
    .join("");

  const remindersHtml = (result.reminders || [])
    .map((r) => `<li>${escapeHtml(r)}</li>`)
    .join("");

  const booking = result.booking;
  let bookingSectionHtml = "";
  if (result.needs_dermatologist && !booking) {
    bookingSectionHtml = `
      <form id="book-form">
        <button type="submit" class="primary" style="background: var(--alert);">Book a dermatologist appointment</button>
      </form>
    `;
  } else if (booking && booking.status === "confirmed") {
    bookingSectionHtml = `
      <div class="appointment">
        <div><span class="k">Appointment ID</span>${escapeHtml(booking.appointment_id)}</div>
        <div><span class="k">Dermatologist</span>${escapeHtml(booking.dermatologist_name)} (${escapeHtml(booking.specialty)})</div>
        <div><span class="k">Date/Time</span>${escapeHtml(booking.datetime)}</div>
        <div><span class="k">Reason</span>${escapeHtml(booking.reason)}</div>
      </div>
    `;
  } else if (booking) {
    bookingSectionHtml = `<p style="color:var(--alert); font-size:14px;">Booking failed: ${escapeHtml(booking.reason || "unknown error")}</p>`;
  }

  app.innerHTML = `
    <p class="eyebrow">Assessment</p>
    <h1>Here's what we found${greetingName}.</h1>
    <p class="sub">Based on what you described${hasImageReading ? " and your photo" : ""}.</p>

    ${justBooked ? `
    <div class="disclaimer" style="border-color:var(--sage); color:var(--sage-dark);">
      Appointment confirmed below — details also saved to your records.
    </div>` : ""}

    <div class="card risk-strip">
      <div class="risk-bar ${escapeHtml(riskLevel)}"></div>
      <div>
        <p class="risk-label">Risk level</p>
        <p class="risk-value ${escapeHtml(riskLevel)}">${escapeHtml(riskLevel.charAt(0).toUpperCase() + riskLevel.slice(1))}</p>
        <ul class="reasons">${reasonsHtml}</ul>
      </div>
    </div>

    <div class="card">
      <p class="section-title">Your routine</p>
      <div class="routine-cols">${routineColsHtml}</div>
      ${result.routine && result.routine.notes ? `<p style="color:var(--ink-soft); font-size:14px; margin-top:16px;">${escapeHtml(result.routine.notes)}</p>` : ""}
      ${result.routine && result.routine.caution ? `<p class="caution-note">⚠ ${escapeHtml(result.routine.caution)}</p>` : ""}
    </div>

    <div class="card">
      <p class="section-title">Recommended products</p>
      <div class="product-list">${productsHtml}</div>
    </div>

    <div class="card">
      <p class="section-title">Habit reminders</p>
      <ul class="reminders">${remindersHtml}</ul>
    </div>

    <div class="card">
      <p class="section-title">Dermatologist guidance</p>
      <div class="referral-box ${result.needs_dermatologist ? "high" : "low"}">
        <p>${escapeHtml(result.referral_message)}</p>
        ${bookingSectionHtml}
      </div>
    </div>

    <a class="back" href="#" id="back-link">← Start a new check</a>
  `;

  document.getElementById("back-link").addEventListener("click", (e) => {
    e.preventDefault();
    currentSessionId = null;
    renderIntakeForm();
  });

  const bookForm = document.getElementById("book-form");
  if (bookForm) {
    bookForm.addEventListener("submit", handleBookSubmit);
  }
}

async function handleBookSubmit(evt) {
  evt.preventDefault();
  const btn = evt.target.querySelector("button");
  btn.disabled = true;
  btn.textContent = "Booking…";

  try {
    const res = await fetch(`${API_BASE_URL}/api/book`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: currentSessionId }),
    });

    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      throw new Error(errBody.error || `Server responded with ${res.status}`);
    }

    const data = await res.json();
    renderResult(data.result, true);
  } catch (err) {
    btn.disabled = false;
    btn.textContent = "Book a dermatologist appointment";
    alert("Couldn't complete the booking.\n\n" + err.message);
  }
}

renderIntakeForm();
