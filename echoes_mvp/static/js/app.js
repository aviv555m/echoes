const inputEl = () => document.getElementById("composerInput");
const suggestionsEl = () => document.getElementById("suggestions");
const languageSel = () => document.getElementById("language");

function speak(text) {
  if (!text) return;
  // Log to backend for metrics
  fetch("/api/speak", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({phrase: text})}).catch(()=>{});
  // Browser TTS
  if ("speechSynthesis" in window) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = languageSel().value || "en-US";
    window.speechSynthesis.speak(utterance);
  } else {
    alert("Speech not supported in this browser.");
  }
}

function renderSuggestions(list) {
  const el = suggestionsEl();
  el.innerHTML = "";
  (list || []).forEach(s => {
    const chip = document.createElement("button");
    chip.className = "chip";
    chip.textContent = s;
    chip.onclick = () => {
      inputEl().value = (inputEl().value + " " + s).trim();
      requestSuggestions();
    };
    el.appendChild(chip);
  });
}

async function requestSuggestions() {
  const current = inputEl().value.trim();
  try {
    const res = await fetch("/api/suggest", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({current, k: 6})});
    const data = await res.json();
    if (data.ok) renderSuggestions(data.suggestions);
  } catch (e) { /* ignore offline */ }
}

function attachBoardHandlers() {
  document.querySelectorAll(".cell").forEach(btn => {
    btn.addEventListener("click", () => {
      const phrase = btn.dataset.phrase;
      inputEl().value = (inputEl().value + " " + phrase).trim();
      requestSuggestions();
    });
    btn.addEventListener("dblclick", () => speak(btn.dataset.phrase));
  });
}

function loadCustomList() {
  fetch("/api/custom_phrase").then(r=>r.json()).then(d=>{
    if(!d.ok) return;
    const cont = document.getElementById("customList");
    cont.innerHTML = "";
    Object.entries(d.categories).forEach(([cat, arr]) => {
      const wrap = document.createElement("div");
      wrap.innerHTML = `<h4>${cat}</h4>`;
      const ul = document.createElement("div");
      ul.className = "chips";
      arr.forEach(p => {
        const chip = document.createElement("button");
        chip.className = "chip";
        chip.textContent = p;
        chip.title = "Click to remove";
        chip.onclick = async () => {
          await fetch("/api/custom_phrase", {method:"DELETE", headers:{"Content-Type":"application/json"}, body: JSON.stringify({category: cat, phrase: p})});
          loadCustomList();
        };
        ul.appendChild(chip);
      });
      wrap.appendChild(ul);
      cont.appendChild(wrap);
    });
  });
}

function saveSettings() {
  const theme = document.body.classList.contains("theme-dark") ? "dark" : "light";
  const language = languageSel().value || "en-US";
  fetch("/api/settings", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({theme, language})}).catch(()=>{});
}

window.addEventListener("DOMContentLoaded", () => {
  attachBoardHandlers();
  loadCustomList();
  requestSuggestions();

  document.getElementById("speakBtn").onclick = () => speak(inputEl().value.trim());
  document.getElementById("clearBtn").onclick = () => { inputEl().value = ""; requestSuggestions(); };
  document.getElementById("addBtn").onclick = async () => {
    const phrase = document.getElementById("newPhrase").value.trim() || inputEl().value.trim();
    if (!phrase) return;
    const category = document.getElementById("newCategory").value.trim() || "Custom";
    await fetch("/api/custom_phrase", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({category, phrase})});
    document.getElementById("newPhrase").value = "";
    document.getElementById("newCategory").value = "";
    loadCustomList();
  };

  document.getElementById("toggleTheme").onclick = () => {
    document.body.classList.toggle("theme-dark");
    document.body.classList.toggle("theme-light");
    saveSettings();
  };
  languageSel().addEventListener("change", saveSettings);

  inputEl().addEventListener("input", () => {
    requestSuggestions();
  });
});
