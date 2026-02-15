(function () {

  // Charts (if present)
  async function loadStats() {
    const canvas = document.getElementById("statsChart");
    if (!canvas || !window.Chart) return;

    try {
      const res = await fetch("/api/stats", { headers: { "Accept": "application/json" } });
      if (!res.ok) return;
      const data = await res.json();

      // Update KPIs if present
      const t = document.getElementById("kpiTeachers");
      const s = document.getElementById("kpiStudents");
      const subs = document.getElementById("kpiSubs");
      if (t && data.teachers != null) t.textContent = data.teachers;
      if (s && data.students != null) s.textContent = data.students;
      if (subs && data.submissions != null) subs.textContent = data.submissions;

      const labels = [];
      const values = [];

      // admin/teacher chart
      if (data.teachers != null) { labels.push("Teachers"); values.push(data.teachers); }
      if (data.students != null) { labels.push("Students"); values.push(data.students); }
      if (data.lessons != null) { labels.push("Lessons"); values.push(data.lessons); }
      if (data.exercises != null) { labels.push("Exercises"); values.push(data.exercises); }
      if (data.submissions != null) { labels.push("Submissions"); values.push(data.submissions); }

      // student extras
      if (data.passed != null) { labels.push("Passed"); values.push(data.passed); }
      if (data.tokens != null) { labels.push("Tokens"); values.push(data.tokens); }

      new Chart(canvas, {
        type: "bar",
        data: {
          labels,
          datasets: [{ label: "Stats", data: values }]
        },
        options: {
          responsive: true,
          plugins: { legend: { display: false } },
          scales: {
            y: { beginAtZero: true }
          }
        }
      });
    } catch (e) {
      // ignore
    }
  }

  loadStats();
})();


// --- I18N (EN/AR) with smooth transitions ---
const I18N = {
  en: {
    "nav.dashboard": "Dashboard",
    "nav.search": "Search",
    "nav.lab": "Laboratory",
    "nav.reviews": "Reviews",
    "nav.logout": "Logout",
    "nav.login": "Login",
    "ui.online": "Online",
    "ui.offline": "Offline",
    "auth.signin": "Sign in"
  },
  ar: {
    "nav.dashboard": "لوحة التحكم",
    "nav.search": "بحث",
    "nav.lab": "المختبر",
    "nav.reviews": "المراجعات",
    "nav.logout": "تسجيل الخروج",
    "nav.login": "تسجيل الدخول",
    "ui.online": "متصل",
    "ui.offline": "غير متصل",
    "auth.signin": "تسجيل الدخول"
  }
};

function applyLang(lang) {
  const root = document.documentElement;
  root.setAttribute("data-lang", lang);
  root.setAttribute("dir", lang === "ar" ? "rtl" : "ltr");

  const view = document.getElementById("view");
  if (view) {
    view.classList.add("lang-swap");
    setTimeout(() => view.classList.remove("lang-swap"), 260);
  }

  const btn = document.getElementById("langToggle");
  if (btn) btn.textContent = lang === "ar" ? "🌐 AR" : "🌐 EN";

  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    const txt = (I18N[lang] && I18N[lang][key]) || (I18N.en[key]) || null;
    if (txt) el.textContent = txt;
  });

  const net = document.getElementById("netStatus");
  if (net) {
    net.textContent = navigator.onLine ? I18N[lang]["ui.online"] : I18N[lang]["ui.offline"];
  }
}

(function initLang() {
  const saved = localStorage.getItem("lang") || "en";
  applyLang(saved);
  const btn = document.getElementById("langToggle");
  if (btn) {
    btn.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-lang") || "en";
      const next = current === "en" ? "ar" : "en";
      localStorage.setItem("lang", next);
      applyLang(next);
    });
  }
})();


(function pageEnterInit(){
  const overlay = document.getElementById("pageTransition");
  if (overlay) overlay.classList.remove("active");
})();


// --- Loading bar (top) ---
let __lbTimer = null;
function startLoadingBar(){
  const bar = document.getElementById("loadingBar");
  const fill = bar ? bar.querySelector("span") : null;
  if (!bar || !fill) return;

  bar.classList.add("active");
  fill.style.transition = "none";
  fill.style.width = "0%";

  requestAnimationFrame(() => {
    fill.style.transition = "width .6s ease";
    fill.style.width = "22%";
  });

  let p = 22;
  clearInterval(__lbTimer);
  __lbTimer = setInterval(() => {
    p = Math.min(p + (p < 70 ? 8 : 2), 92);
    fill.style.width = p + "%";
  }, 260);
}

function stopLoadingBar(){
  const bar = document.getElementById("loadingBar");
  const fill = bar ? bar.querySelector("span") : null;
  if (!bar || !fill) return;

  clearInterval(__lbTimer);
  fill.style.transition = "width .18s ease";
  fill.style.width = "100%";
  setTimeout(() => {
    bar.classList.remove("active");
    fill.style.transition = "none";
    fill.style.width = "0%";
  }, 220);
}

document.addEventListener("DOMContentLoaded", () => {
  // quick load feel on first render
  startLoadingBar();
  setTimeout(stopLoadingBar, 5000);
});

window.addEventListener("pageshow", () => {
  stopLoadingBar();
});
