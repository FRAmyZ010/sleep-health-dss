const I18N = window.SLEEP_I18N;
const CLASS_ORDER = ["None", "Insomnia", "Sleep Apnea"];
const COLORS = { None: "#047857", Insomnia: "#C2410C", "Sleep Apnea": "#B91C1C" };
const TONES = { None: "low", Insomnia: "medium", "Sleep Apnea": "high" };
const PROFILE_FIELDS = [
  "Gender", "Age", "Occupation", "BMI Category", "Sleep Duration", "Quality of Sleep",
  "Physical Activity Level", "Stress Level", "Daily Steps", "Heart Rate"
];
const SESSION_KEY = "sleep-health-web-v4";
const ANON_KEY = "sleep-health-anon-v1";

const SCREENING_SECTIONS = [
  { id: "before", ids: [1] },
  { id: "during", ids: [2, 3, 4, 5, 6, 7] },
  { id: "after", ids: [8, 9, 10, 11, 12, 13] }
];
// Flag a group only with enough hits, or an apnea red-flag item.
const SCREENING_GROUPS = [
  { id: "insomnia", questions: [1, 6, 9], deep: true, severity: 3, minHits: 2, redFlags: [] },
  {
    id: "sleep_apnea",
    questions: [2, 3, 4, 5, 7, 8, 10, 11, 12, 13],
    deep: true,
    severity: 5,
    minHits: 2,
    redFlags: [3, 4, 12]
  }
];
const SCREENING_IDS = SCREENING_SECTIONS.flatMap((section) => section.ids);
const SCREEN_CLASS = { insomnia: "Insomnia", sleep_apnea: "Sleep Apnea" };
// Partner-observed items: people who live alone can answer "unknown".
const PARTNER_DEPENDENT_IDS = new Set([2, 3, 4, 5]);
const WATCH_FORM_KEYS = ["sleep", "quality", "activity", "stress", "steps", "heart"];
const WATCH_DEMO = {
  sleep: "7.2",
  quality: "7",
  activity: "58",
  stress: "4",
  steps: "7420",
  heart: "68"
};

function blankWatchSource() {
  return {
    sleep: false,
    quality: false,
    activity: false,
    stress: false,
    steps: false,
    heart: false
  };
}

function defaultForm() {
  return {
    gender: "Female",
    age: "40",
    occupation: "Nurse",
    weight: "70.0",
    height: "170.0",
    sleep: "7.0",
    quality: "7",
    activity: "60",
    stress: "5",
    steps: "6000",
    heart: "72"
  };
}

function occupationChoices() {
  const list = (state.meta && Array.isArray(state.meta.occupations))
    ? state.meta.occupations.slice()
    : [];
  if (!list.includes("Student")) {
    const otherIndex = list.indexOf("Other");
    if (otherIndex >= 0) list.splice(otherIndex, 0, "Student");
    else list.push("Student");
  }
  return list;
}

const state = {
  lang: "en",
  page: "home",
  meta: null,
  form: defaultForm(),
  watchSource: blankWatchSource(),
  result: null,
  notice: null,
  step: 0,
  busy: false,
  filters: null,
  eda: null,
  screening: {
    answers: {},
    triage: null,
    view: "questions"
  },
  logs: null,
  logsPeople: null,
  logsPerson: "",
  logsBusy: false,
  logsDetail: null,
  logsNotice: null,
  trust: null,
  trustBusy: false,
  trustNotice: null
};

function classTone(label) {
  return TONES[label] || "low";
}

function nextActionKey(decision) {
  if (decision && decision.conflict) return "action_conflict";
  const risk = decision && decision.risk_level;
  if (risk === "High") return "action_high";
  if (risk === "Medium") return "action_medium";
  return "action_low";
}

function resetDemoState() {
  state.form = defaultForm();
  state.watchSource = blankWatchSource();
  state.result = null;
  state.notice = { kind: "ok", title: tr("refresh_done") };
  state.step = 0;
  state.busy = false;
  state.screening = { answers: {}, triage: null, view: "questions" };
  state.filters = null;
  state.eda = null;
  state.page = "home";
  sessionStorage.removeItem(SESSION_KEY);
  saveSession();
  render();
}

let edaToken = 0;
let ageTimer = 0;

function tr(key, values) {
  const table = I18N.TEXT[state.lang] || I18N.TEXT.en;
  const template = table[key] || I18N.TEXT.en[key] || key;
  return template.replace(/\{(\w+)\}/g, (_, name) => (values && values[name] != null ? String(values[name]) : ""));
}

function named(group, value) {
  const table = (I18N.LABELS[state.lang] || I18N.LABELS.en)[group] || {};
  return table[value] || value;
}

const SVG_NS = "http://www.w3.org/2000/svg";
const ICONS = {
  clipboard: [["path", { d: "M9 3.5h6a1 1 0 0 1 1 1V6H8V4.5a1 1 0 0 1 1-1z" }], ["rect", { x: "6", y: "5.5", width: "12", height: "15", rx: "2" }], ["path", { d: "M9 12h6M9 16h4" }]],
  list: [["path", { d: "M9 6h11M9 12h11M9 18h11M4.5 6.5l1.2 1.2L8 5.2M4.5 12.5l1.2 1.2L8 11.2M4.5 18.5l1.2 1.2L8 17.2" }]],
  bars: [["path", { d: "M5 19V9M12 19V4M19 19v-7" }]],
  user: [["circle", { cx: "12", cy: "8", r: "3.2" }], ["path", { d: "M5.5 19.5c1.4-3.2 3.4-4.8 6.5-4.8s5.1 1.6 6.5 4.8" }]],
  calendar: [["rect", { x: "4.5", y: "5.5", width: "15", height: "14", rx: "2" }], ["path", { d: "M8 3.5v4M16 3.5v4M4.5 10h15" }]],
  briefcase: [["rect", { x: "3.5", y: "8", width: "17", height: "11", rx: "2" }], ["path", { d: "M9 8V6.2A1.2 1.2 0 0 1 10.2 5h3.6A1.2 1.2 0 0 1 15 6.2V8M3.5 13h17" }]],
  scale: [["path", { d: "M12 4v16M8 20h8M12 7l-6 7h5.2M12 7l6 7h-5.2" }]],
  ruler: [["path", { d: "M8 3.5v17M8 4.5h4M8 8.5h2.5M8 12.5h4M8 16.5h2.5M8 20.5h4" }]],
  moon: [["path", { d: "M16 3.5a8.2 8.2 0 1 0 4.2 14.2A7.2 7.2 0 0 1 16 3.5z" }]],
  star: [["path", { d: "M12 3.8l2.2 4.6 5 .7-3.6 3.5.9 5.1L12 15.4 7.5 17.7l.9-5.1L4.8 9.1l5-.7z" }]],
  pulse: [["path", { d: "M3 12h4.2l2.1-5.2L13 17.2l2.2-5.2H21" }]],
  bolt: [["path", { d: "M13 2.8 6.5 13H12l-1 8.2L17.5 11H12z" }]],
  steps: [["ellipse", { cx: "9", cy: "16.5", rx: "3", ry: "3.6" }], ["ellipse", { cx: "15.2", cy: "9.2", rx: "2.4", ry: "3.2" }]],
  heart: [["path", { d: "M12 20s-7-4.4-7-9a4 4 0 0 1 7-2 4 4 0 0 1 7 2c0 4.6-7 9-7 9z" }]],
  up: [["path", { d: "M12 19V6M6.5 11 12 5.5 17.5 11" }]],
  down: [["path", { d: "M12 5v13M6.5 13 12 18.5 17.5 13" }]],
  shield: [["path", { d: "M12 3.2 19 6v6.2c0 4.6-3.1 7.2-7 8.6-3.9-1.4-7-4-7-8.6V6z" }], ["path", { d: "M8.8 12.1 11 14.3 15.4 9.8" }]],
  alert: [["path", { d: "M12 4.2 20.5 19H3.5z" }], ["path", { d: "M12 9.2v4.6M12 16.8h.01" }]],
  lungs: [["path", { d: "M12 4v7M12 8c-4.2 0-6.2 2.8-6.2 6.6 2.2 1.8 4 1.6 6.2.6M12 8c4.2 0 6.2 2.8 6.2 6.6-2.2 1.8-4 1.6-6.2.6" }]],
  check: [["circle", { cx: "12", cy: "12", r: "8" }], ["path", { d: "M8.5 12.2 11 14.6 15.6 9.6" }]],
  filter: [["path", { d: "M4 5.5h16l-6 7.2V19l-4 1.6v-8z" }]],
  compare: [["path", { d: "M7 5v14M17 5v14M4 8h6M14 16h6" }]],
  decision: [["path", { d: "M12 3.5 14.2 8l5 .6-3.7 3.4.9 5-4.4-2.4L8.6 17l.9-5L5.8 8.6 10.8 8z" }]],
  grid: [["rect", { x: "4", y: "4", width: "6.5", height: "6.5", rx: "1.2" }], ["rect", { x: "13.5", y: "4", width: "6.5", height: "6.5", rx: "1.2" }], ["rect", { x: "4", y: "13.5", width: "6.5", height: "6.5", rx: "1.2" }], ["rect", { x: "13.5", y: "13.5", width: "6.5", height: "6.5", rx: "1.2" }]],
  dots: [["circle", { cx: "7", cy: "16", r: "2" }], ["circle", { cx: "12", cy: "9", r: "2" }], ["circle", { cx: "17", cy: "13", r: "2" }]],
  table: [["rect", { x: "4", y: "5", width: "16", height: "14", rx: "2" }], ["path", { d: "M4 10h16M10 10v9" }]],
  arrow: [["path", { d: "M5 12h14M13 6l6 6-6 6" }]],
  back: [["path", { d: "M19 12H5M11 6 5 12l6 6" }]],
  rows: [["path", { d: "M4 7h16M4 12h16M4 17h10" }]],
  home: [["path", { d: "M4 11.5 12 4.5l8 7V20a1 1 0 0 1-1 1h-5v-6H10v6H5a1 1 0 0 1-1-1z" }]]
};
const PAGES = ["home", "screen", "assess", "result", "logs", "trust", "eda"];
const NAV_ICONS = {
  home: "home",
  screen: "list",
  assess: "clipboard",
  result: "list",
  logs: "rows",
  trust: "shield",
  eda: "bars"
};
const CLASS_ICONS = { None: "check", Insomnia: "moon", "Sleep Apnea": "lungs" };
const RISK_ICONS = { Low: "shield", Medium: "moon", High: "alert" };
const FEATURE_ICONS = {
  Age: "calendar",
  "Sleep Duration": "moon",
  "Quality of Sleep": "star",
  "Physical Activity Level": "pulse",
  "Stress Level": "bolt",
  "Heart Rate": "heart",
  "Daily Steps": "steps",
  Gender: "user",
  Occupation: "briefcase",
  "BMI Category": "scale",
  "Disorder Risk": "alert"
};

function svgNode(tag, attrs, children) {
  const node = document.createElementNS(SVG_NS, tag);
  Object.entries(attrs || {}).forEach(([key, value]) => node.setAttribute(key, value));
  (children || []).forEach((child) => node.append(child));
  return node;
}

function flag(lang) {
  const svg = svgNode("svg", {
    viewBox: lang === "th" ? "0 0 9 6" : "0 0 60 30",
    "aria-hidden": "true"
  });
  if (lang === "th") {
    svg.append(
      svgNode("rect", { width: "9", height: "6", fill: "#A51931" }),
      svgNode("rect", { y: "1", width: "9", height: "4", fill: "#F4F5F8" }),
      svgNode("rect", { y: "2", width: "9", height: "2", fill: "#2D2A4A" })
    );
  } else {
    const clip = svgNode("clipPath", { id: "flag-uk" }, [
      svgNode("path", { d: "M0 0v30h60V0z" })
    ]);
    svg.append(
      svgNode("defs", {}, [clip]),
      svgNode("path", { d: "M0 0v30h60V0z", fill: "#012169" }),
      svgNode("path", { d: "m0 0 60 30m0-30L0 30", stroke: "#fff", "stroke-width": "6", "clip-path": "url(#flag-uk)" }),
      svgNode("path", { d: "m0 0 60 30m0-30L0 30", stroke: "#C8102E", "stroke-width": "4", "clip-path": "url(#flag-uk)" }),
      svgNode("path", { d: "M30 0v30M0 15h60", stroke: "#fff", "stroke-width": "10", "clip-path": "url(#flag-uk)" }),
      svgNode("path", { d: "M30 0v30M0 15h60", stroke: "#C8102E", "stroke-width": "6", "clip-path": "url(#flag-uk)" })
    );
  }
  return el("span", { class: "flag" }, [svg]);
}

function icon(name) {
  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("fill", "none");
  svg.setAttribute("stroke", "currentColor");
  svg.setAttribute("stroke-width", "1.8");
  svg.setAttribute("stroke-linecap", "round");
  svg.setAttribute("stroke-linejoin", "round");
  (ICONS[name] || ICONS.check).forEach(([tag, attrs]) => {
    const node = document.createElementNS(SVG_NS, tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    svg.append(node);
  });
  return el("span", { class: "glyph" }, [svg]);
}

function title(tag, iconName, text) {
  return el(tag, { class: "with-icon" }, [icon(iconName), el("span", { text })]);
}

function el(tag, attrs, children) {
  const node = document.createElement(tag);
  Object.entries(attrs || {}).forEach(([key, value]) => {
    if (value == null) return;
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = String(value);
    else if (typeof value === "function" && key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, String(value));
  });
  const list = children == null ? [] : Array.isArray(children) ? children : [children];
  list.forEach((child) => {
    if (child == null || child === false) return;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  });
  return node;
}

function getAnonId() {
  try {
    let id = localStorage.getItem(ANON_KEY);
    if (!id) {
      id = (window.crypto && crypto.randomUUID)
        ? crypto.randomUUID()
        : `anon-${Date.now()}-${Math.random().toString(16).slice(2)}`;
      localStorage.setItem(ANON_KEY, id);
    }
    return id;
  } catch (_error) {
    return `anon-${Date.now()}`;
  }
}

function saveSession() {
  sessionStorage.setItem(SESSION_KEY, JSON.stringify({
    lang: state.lang,
    page: state.page,
    form: state.form,
    watchSource: state.watchSource,
    result: state.result,
    notice: state.notice,
    step: state.step,
    screening: state.screening
  }));
}

async function postAssessmentLog(result, decision, formPayload) {
  if (!result || result.log_id) return;
  const triage = state.screening.triage;
  const answers = {};
  SCREENING_IDS.forEach((id) => {
    answers[String(id)] = Object.prototype.hasOwnProperty.call(state.screening.answers, id)
      ? state.screening.answers[id]
      : null;
  });
  const entry = {
    anon_id: getAnonId(),
    screening_answers: answers,
    screening_triage: triage
      ? {
        topClass: triage.topClass,
        deepEligible: triage.deepEligible,
        yesCount: triage.yesCount,
        unknownCount: triage.unknownCount,
        flagged: triage.flagged,
        standards: result.standards || triage.standards || null
      }
      : null,
    form_payload: formPayload,
    model_result: {
      label: result.label,
      risk_level: result.risk_level,
      probabilities: result.probabilities,
      factors: result.factors,
      support_notes: result.support_notes
    },
    standards: result.standards || (triage && triage.standards) || null,
    decision,
    profile: result.profile || null,
    body: result.body || null,
    screen_class: decision.screen_class,
    model_label: result.label,
    risk_level: decision.risk_level,
    yes_count: triage ? triage.yesCount : null,
    unknown_count: triage ? triage.unknownCount : null
  };
  try {
    const response = await fetch("/api/logs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(entry)
    });
    const body = await response.json();
    if (response.ok && body.row && body.row.id != null) {
      result.log_id = body.row.id;
    }
  } catch (_error) {
    // Logging must not block the demo UI.
  }
}

function restoreSession() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(SESSION_KEY) || "null");
    if (!saved || !I18N.TEXT[saved.lang]) return;
    state.lang = saved.lang;
    state.page = PAGES.includes(saved.page) ? saved.page : "home";
    state.form = Object.assign(state.form, saved.form || {});
    delete state.form.systolic;
    delete state.form.diastolic;
    state.watchSource = Object.assign(blankWatchSource(), saved.watchSource || {});
    state.result = saved.result || null;
    state.notice = saved.notice || null;
    state.step = Number.isInteger(saved.step) ? saved.step : 0;
    if (saved.screening && typeof saved.screening === "object") {
      state.screening = {
        answers: saved.screening.answers || {},
        triage: saved.screening.triage || null,
        view: saved.screening.view === "triage" ? "triage" : "questions"
      };
    }
  } catch (_error) {
    sessionStorage.removeItem(SESSION_KEY);
  }
}

function bmiCategory(bmi) {
  if (bmi < 18.5) return "Underweight";
  if (bmi < 25) return "Normal";
  if (bmi < 30) return "Overweight";
  return "Obese";
}

function formatBmi(bmi, category) {
  const rounded = Math.round(bmi * 10) / 10;
  if (bmiCategory(rounded) !== category) return bmi.toFixed(2);
  return bmi.toFixed(1);
}

function readBmi() {
  const weight = Number(state.form.weight);
  const height = Number(state.form.height);
  if (!Number.isFinite(weight) || !Number.isFinite(height) || height <= 0) return null;
  const bmi = weight / ((height / 100) ** 2);
  const category = bmiCategory(bmi);
  return { bmi, category, display: formatBmi(bmi, category) };
}

function pretty(feature, value) {
  const number = Number(value);
  const thai = state.lang === "th";
  if (feature === "Quality of Sleep" || feature === "Stress Level") return `${Math.round(number)}/10`;
  if (feature === "Sleep Duration") return `${number.toFixed(1)} ${thai ? "ชม." : "hours"}`;
  if (feature === "Daily Steps") return `${Math.round(number).toLocaleString("en-US")} ${thai ? "ก้าว" : "steps"}`;
  const units = {
    "Physical Activity Level": ["นาที/วัน", "min/day"],
    "Heart Rate": ["ครั้ง/นาที", "bpm"],
    Age: ["ปี", "years"]
  };
  const shown = Math.abs(number - Math.round(number)) < 1e-6 ? number.toFixed(0) : number.toFixed(1);
  const pair = units[feature];
  return pair ? `${shown} ${pair[thai ? 0 : 1]}` : shown;
}

function factorText(factor) {
  if (factor.kind === "categorical" && factor.rate != null) {
    const group = factor.feature === "Occupation" ? "job" : "bmi";
    return tr("factor_cat", {
      name: named("feature", factor.feature),
      category: named(group, factor.category),
      rate: `${Math.round(factor.rate * 100)}%`,
      label: named("class", factor.class_label),
      base: `${Math.round(factor.base_rate * 100)}%`
    });
  }
  if (factor.kind === "numeric" && factor.user_value != null) {
    const shared = {
      name: named("feature", factor.feature),
      user: pretty(factor.feature, factor.user_value),
      none: pretty(factor.feature, factor.none_value)
    };
    if (factor.relation === "same_group") return tr("factor_none", shared);
    return tr("factor_shift", Object.assign({
      relation: tr(`rel_${factor.relation}`),
      label: named("class", factor.class_label || ""),
      predicted: pretty(factor.feature, factor.predicted_value)
    }, shared));
  }
  return factor.sentence || "";
}

function noteText(note) {
  if (typeof note === "string") return note;
  if (note.kind === "range") {
    return tr("outside_range", {
      name: named("feature", note.feature),
      low: pretty(note.feature, note.low),
      high: pretty(note.feature, note.high)
    });
  }
  let value = note.value;
  if (note.feature === "Occupation") value = named("job", value);
  if (note.feature === "BMI Category") value = named("bmi", value);
  if (note.feature === "Gender") value = named("gender", value);
  return tr("unknown_category", { name: named("feature", note.feature), value });
}

function profileValue(feature, value) {
  if (feature === "Gender") return named("gender", value);
  if (feature === "Occupation") return named("job", value);
  if (feature === "BMI Category") return named("bmi", value);
  return String(value);
}

function errorText(item) {
  if (item.code === "weight_range" || item.code === "height_range" || item.code === "server") {
    return tr(item.code === "server" ? "server_error" : item.code);
  }
  return item.message || tr("score_failed");
}

function canAccessDeepAssess() {
  // Deep assess opens after any completed triage, including None (optional path).
  return Boolean(state.screening.triage);
}

function showPage(page) {
  if (page === "assess" && !canAccessDeepAssess()) {
    state.notice = { kind: "warn", text: tr("assess_locked") };
    page = "screen";
    state.screening.view = state.screening.triage ? "triage" : "questions";
  }
  state.page = page;
  if (location.hash !== `#${page}`) location.hash = page;
  saveSession();
  render();
  if (page === "eda") fetchEda();
  if (page === "logs") fetchLogs();
  if (page === "trust") fetchTrust();
}

function render() {
  document.documentElement.lang = state.lang === "th" ? "th" : "en";
  document.title = tr("app_name");
  document.getElementById("app").replaceChildren(el("div", { class: "shell" }, [renderSidebar(), renderMain()]));
}

function renderSidebar() {
  const nav = el("nav", { class: "nav" }, PAGES.map((page) => el("button", {
    type: "button",
    class: state.page === page ? "active" : "",
    onclick: () => showPage(page)
  }, [icon(NAV_ICONS[page]), el("span", { text: tr(`nav_${page}`) })])));
  const children = [
    el("div", { class: "brand-lockup" }, [
      icon("moon"),
      el("div", {}, [
        el("p", { class: "kicker", text: tr("course") }),
        el("p", { class: "brand", text: tr("app_name") })
      ])
    ]),
    el("p", { class: "tagline", text: tr("tagline") }),
    nav
  ];
  if (state.page === "eda" && state.filters) children.push(renderFilters());
  children.push(el("p", { class: "side-note" }, [icon("shield"), el("span", { text: tr("footer") })]));
  return el("aside", { class: "sidebar" }, children);
}

function renderFilters() {
  const filters = state.filters;
  const box = (listName, value, group) => {
    const input = el("input", { type: "checkbox" });
    input.checked = filters[listName].includes(value);
    input.addEventListener("change", () => {
      const list = filters[listName];
      const index = list.indexOf(value);
      if (input.checked && index < 0) list.push(value);
      if (!input.checked && index >= 0) list.splice(index, 1);
      fetchEda();
    });
    return el("label", { class: "check" }, [input, el("span", { text: named(group, value) })]);
  };
  const ageSame = state.meta.age_min === state.meta.age_max;
  const ageControl = ageSame
    ? el("p", { class: "note", text: tr("every_age", { age: state.meta.age_min }) })
    : el("div", {}, [
      el("p", { class: "age-readout", id: "age-readout", text: `${filters.age_min}–${filters.age_max}` }),
      range("age_min"),
      range("age_max")
    ]);
  return el("div", { class: "filters" }, [
    title("h2", "filter", tr("filters")),
    el("p", { class: "field-label" }, [icon("user"), el("span", { text: tr("gender") })]),
    el("div", { class: "check-list" }, state.meta.filter_genders.map((value) => box("genders", value, "gender"))),
    el("p", { class: "field-label" }, [icon("briefcase"), el("span", { text: tr("occupation") })]),
    el("div", { class: "check-list" }, state.meta.filter_occupations.map((value) => box("occupations", value, "job"))),
    el("p", { class: "field-label" }, [icon("calendar"), el("span", { text: tr("age_range") })]),
    ageControl
  ]);
}

function range(key) {
  const input = el("input", {
    type: "range",
    min: state.meta.age_min,
    max: state.meta.age_max,
    step: "1",
    value: state.filters[key]
  });
  input.addEventListener("input", () => {
    state.filters[key] = Number(input.value);
    const readout = document.getElementById("age-readout");
    if (readout) readout.textContent = `${state.filters.age_min}–${state.filters.age_max}`;
    clearTimeout(ageTimer);
    ageTimer = setTimeout(fetchEda, 180);
  });
  return input;
}

function renderMain() {
  const language = el("div", { class: "segment" }, ["en", "th"].map((lang) => {
    const label = lang === "en" ? "English" : "ไทย";
    return el("button", {
      type: "button",
      class: state.lang === lang ? "active" : "",
      "aria-pressed": state.lang === lang ? "true" : "false",
      "aria-label": label,
      onclick: () => {
        state.lang = lang;
        saveSession();
        render();
      }
    }, [
      flag(lang),
      el("span", { text: label })
    ]);
  }));
  const refresh = el("button", {
    type: "button",
    class: "secondary refresh-btn",
    title: tr("refresh_hint"),
    onclick: resetDemoState
  }, [icon("back"), el("span", { text: tr("refresh") })]);
  const page = state.page === "home"
    ? renderHome()
    : state.page === "screen"
      ? renderScreen()
      : state.page === "result"
        ? renderResult()
        : state.page === "logs"
          ? renderLogs()
          : state.page === "trust"
            ? renderTrust()
            : state.page === "eda"
              ? renderEda()
              : renderAssess();
  return el("main", { class: "main" }, [
    el("div", { class: "topbar" }, [
      el("div", { class: "topbar-tools" }, [
        el("span", { text: tr("language") }),
        language,
        refresh
      ])
    ]),
    page
  ]);
}

function isScreeningAnswered(value) {
  return value === true || value === false || value === "unknown";
}

function screeningAnsweredCount() {
  return SCREENING_IDS.filter((id) => isScreeningAnswered(state.screening.answers[id])).length;
}

function evaluateScreening(answers) {
  const flagged = SCREENING_GROUPS.map((group) => {
    const hits = group.questions.filter((id) => answers[id] === true);
    const redHits = (group.redFlags || []).filter((id) => answers[id] === true);
    const byThreshold = hits.length >= (group.minHits || 1);
    const byRedFlag = redHits.length > 0;
    return {
      id: group.id,
      deep: group.deep,
      severity: group.severity,
      hits: hits.slice(),
      redHits: redHits.slice(),
      hitCount: hits.length,
      total: group.questions.length,
      minHits: group.minHits || 1,
      flagged: byThreshold || byRedFlag,
      trigger: byRedFlag ? "red_flag" : byThreshold ? "threshold" : "none"
    };
  }).filter((group) => group.flagged);
  flagged.sort((a, b) => b.hitCount - a.hitCount || b.severity - a.severity);
  const triage = {
    flagged,
    deepEligible: flagged.length > 0,
    topClass: flagged.length ? SCREEN_CLASS[flagged[0].id] : "None",
    yesCount: SCREENING_IDS.filter((id) => answers[id] === true).length,
    unknownCount: SCREENING_IDS.filter((id) => answers[id] === "unknown").length
  };
  // Parallel standard scores do not replace rule triage / deep unlock.
  triage.standards = buildStandardScores(answers, null);
  return triage;
}

function answerYesNo(answers, id) {
  const value = answers[id];
  if (value === true) return true;
  if (value === false) return false;
  return null;
}

function stopBangBand(score, answered) {
  if (answered === 0) return "unavailable";
  if (score <= 2) return "low";
  if (score <= 4) return "intermediate";
  return "high";
}

function isiBand(score) {
  if (score <= 7) return "none";
  if (score <= 14) return "subthreshold";
  if (score <= 21) return "moderate";
  return "severe";
}

function buildStandardScores(answers, context) {
  const ctx = context || {};
  const stopItems = [
    { key: "S", source: "screen_q2", value: answerYesNo(answers, 2) },
    { key: "T", source: "screen_q11", value: answerYesNo(answers, 11) },
    { key: "O", source: "screen_q3", value: answerYesNo(answers, 3) },
    { key: "P", source: "bp_unavailable", value: null, unavailable: true },
    {
      key: "B",
      source: "bmi_gt_35",
      value: ctx.bmi == null ? null : Number(ctx.bmi) > 35,
      unavailable: ctx.bmi == null
    },
    {
      key: "A",
      source: "age_gt_50",
      value: ctx.age == null ? null : Number(ctx.age) > 50,
      unavailable: ctx.age == null
    },
    { key: "N", source: "neck_unavailable", value: null, unavailable: true },
    {
      key: "G",
      source: "gender_male",
      value: ctx.gender == null ? null : String(ctx.gender) === "Male",
      unavailable: ctx.gender == null
    }
  ];
  let stopScore = 0;
  let stopAnswered = 0;
  const stopMissing = [];
  stopItems.forEach((item) => {
    if (item.unavailable || item.value == null) {
      stopMissing.push(item.key);
      return;
    }
    stopAnswered += 1;
    if (item.value) stopScore += 1;
  });

  const isiParts = [];
  const pushIsi = (id, points, source) => {
    const value = answerYesNo(answers, id);
    if (value == null) {
      isiParts.push({ source, points: null, unavailable: true });
      return;
    }
    isiParts.push({ source, points: value ? points : 0, unavailable: false });
  };
  pushIsi(1, 2, "screen_q1");
  pushIsi(6, 2, "screen_q6");
  pushIsi(9, 2, "screen_q9");
  pushIsi(11, 2, "screen_q11");
  pushIsi(13, 1, "screen_q13");
  let qualityPoints = null;
  if (ctx.quality != null && Number.isFinite(Number(ctx.quality))) {
    const quality = Number(ctx.quality);
    qualityPoints = Math.max(0, Math.min(4, Math.round(((10 - quality) / 10) * 4)));
    isiParts.push({ source: "quality_of_sleep", points: qualityPoints, unavailable: false });
  } else {
    isiParts.push({ source: "quality_of_sleep", points: null, unavailable: true });
  }
  const isiScore = isiParts.reduce((sum, part) => sum + (part.points || 0), 0);
  const isiAnswered = isiParts.filter((part) => !part.unavailable).length;

  return {
    mode: "parallel",
    note: "Rule triage still gates deep unlock. STOP-Bang and ISI-inspired scores are supporting evidence only.",
    stop_bang: {
      score: stopScore,
      answered: stopAnswered,
      max: 8,
      missing: stopMissing,
      band: stopBangBand(stopScore, stopAnswered),
      items: stopItems.map((item) => ({
        key: item.key,
        source: item.source,
        hit: item.unavailable || item.value == null ? null : Boolean(item.value),
        unavailable: Boolean(item.unavailable || item.value == null)
      }))
    },
    isi_inspired: {
      score: isiScore,
      answered: isiAnswered,
      max: 13,
      band: isiBand(isiScore),
      parts: isiParts
    }
  };
}

function refreshStandards(triage, context) {
  if (!triage) return null;
  triage.standards = buildStandardScores(state.screening.answers, context);
  return triage.standards;
}

function renderStandardsPanel(standards, opts) {
  if (!standards) return null;
  const stop = standards.stop_bang;
  const isi = standards.isi_inspired;
  const stopItems = el("ul", { class: "actions" }, stop.items.map((item) => el("li", {
    text: item.unavailable
      ? tr("standards_item_na", { key: item.key, source: tr(item.source) })
      : tr("standards_item_hit", {
        key: item.key,
        source: tr(item.source),
        hit: item.hit ? tr("standards_hit_yes") : tr("standards_hit_no")
      })
  })));
  return el("section", { class: "card" }, [
    title("h2", "shield", tr("standards_title")),
    el("p", { class: "lede", text: tr("standards_lead") }),
    el("p", { class: "note", text: tr("standards_parallel_note") }),
    el("p", {
      text: tr("standards_stopbang_line", {
        score: stop.score,
        answered: stop.answered,
        band: tr(`standards_stopbang_${stop.band}`)
      })
    }),
    el("p", { class: "note", text: tr("standards_stopbang_missing", { missing: stop.missing.join(", ") || "—" }) }),
    stopItems,
    el("p", {
      text: tr("standards_isi_line", {
        score: isi.score,
        answered: isi.answered,
        band: tr(`standards_isi_${isi.band}`)
      })
    }),
    el("p", { class: "note", text: tr("standards_isi_note") }),
    opts && opts.footer ? el("p", { class: "note", text: opts.footer }) : null
  ]);
}

function confidenceBand(probability) {
  if (probability < 0.40) return "low";
  if (probability < 0.70) return "mid";
  return "high";
}

function screenEvidence(triage) {
  if (!triage || !triage.flagged || !triage.flagged.length) {
    return { strength: 0, red_flag: false, hit_count: 0, total: 0, trigger: "none" };
  }
  const top = triage.flagged[0];
  const ratio = top.total ? top.hitCount / top.total : 0;
  const strength = top.trigger === "red_flag" ? Math.max(0.85, ratio) : ratio;
  return {
    strength,
    red_flag: top.trigger === "red_flag",
    hit_count: top.hitCount,
    total: top.total,
    trigger: top.trigger,
    group_id: top.id
  };
}

function escalateRiskLevel(riskLevel) {
  if (riskLevel === "Low") return "Medium";
  if (riskLevel === "Medium") return "High";
  return "High";
}

function buildDecision(result, triage, logPrior) {
  const label = result.label;
  const topProb = Number(result.probabilities[label] || 0);
  const band = confidenceBand(topProb);
  const evidence = screenEvidence(triage);
  const screenClass = triage && triage.deepEligible ? triage.topClass : "None";
  let conflict = null;
  let riskLevel = result.risk_level;
  let adviceKey = label;
  const notes = [];

  if (triage && triage.deepEligible && screenClass !== "None") {
    if (label === "None") {
      conflict = "screen_positive_model_none";
      riskLevel = "High";
      adviceKey = "conflict_review";
    } else if (label !== screenClass) {
      conflict = "screen_model_mismatch";
      riskLevel = "High";
      adviceKey = "conflict_mismatch";
    }
  }

  if (!conflict) {
    if (band === "low") {
      riskLevel = label === "Sleep Apnea" ? "High" : "Medium";
      adviceKey = `uncertain_${label === "Sleep Apnea" ? "apnea" : label === "Insomnia" ? "insomnia" : "none"}`;
    } else if (band === "mid" && label === "None") {
      riskLevel = "Low";
      adviceKey = "None";
    } else if (band === "mid") {
      riskLevel = label === "Sleep Apnea" ? "High" : "Medium";
      adviceKey = label;
    } else {
      riskLevel = TONES[label] === "high" ? "High" : TONES[label] === "medium" ? "Medium" : "Low";
      adviceKey = label;
    }

    // Pre-screen evidence adjusts risk when stages agree (not inside the RF).
    if (screenClass === label && screenClass !== "None") {
      if (evidence.red_flag || evidence.strength >= 0.5) {
        if (riskLevel === "Medium") riskLevel = "High";
        notes.push("screen_boost");
      }
      if (evidence.red_flag && label === "Sleep Apnea") {
        adviceKey = "Sleep Apnea";
        riskLevel = "High";
        notes.push("red_flag_apnea");
      }
    }
  }

  // Anonymous log prior: escalate caution only; never lower risk.
  if (logPrior && logPrior.escalate) {
    const before = riskLevel;
    riskLevel = escalateRiskLevel(riskLevel);
    notes.push("log_prior_boost");
    if (before !== riskLevel && !conflict) {
      if (riskLevel === "High" && adviceKey === "None") adviceKey = "uncertain_none";
    }
  }

  const agree = screenClass === label;
  let hybridScore = conflict
    ? 1
    : Math.min(1, 0.6 * topProb + 0.4 * (agree ? evidence.strength : evidence.strength * 0.25));
  if (logPrior && logPrior.escalate) {
    hybridScore = Math.min(1, hybridScore + 0.05);
  }

  const pack = I18N.ADVICE[state.lang][adviceKey] || I18N.ADVICE[state.lang][label];
  return {
    label,
    screen_class: screenClass,
    top_probability: topProb,
    confidence_band: band,
    screen_strength: evidence.strength,
    screen_red_flag: evidence.red_flag,
    hybrid_score: hybridScore,
    conflict,
    risk_level: riskLevel,
    decision: pack.decision,
    actions: pack.actions.slice(),
    advice_key: adviceKey,
    notes,
    log_prior: logPrior || null
  };
}

async function fetchLogPrior(query) {
  try {
    const response = await fetch("/api/logs/prior", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(query)
    });
    if (!response.ok) return null;
    return await response.json();
  } catch (_error) {
    return null;
  }
}

function setScreeningAnswer(id, value) {
  state.screening.answers[id] = value;
  state.screening.triage = null;
  state.screening.view = "questions";
  if (state.notice && state.notice.kind === "warn") state.notice = null;
  saveSession();
  render();
}

function submitScreening() {
  if (screeningAnsweredCount() < SCREENING_IDS.length) {
    state.notice = { kind: "warn", text: tr("screen_incomplete") };
    saveSession();
    render();
    return;
  }
  state.notice = null;
  state.screening.triage = evaluateScreening(state.screening.answers);
  state.screening.view = "triage";
  saveSession();
  render();
}

function resetScreening() {
  state.screening = { answers: {}, triage: null, view: "questions" };
  state.notice = null;
  saveSession();
  render();
}

function renderHome() {
  const card = (iconName, titleKey, bodyKey, tone) => el("article", {
    class: tone ? `card landing-card tone-${tone}` : "card landing-card"
  }, [
    title("h2", iconName, tr(titleKey)),
    el("p", { text: tr(bodyKey) })
  ]);
  return el("section", { class: "landing" }, [
    title("h1", "moon", tr("page_home")),
    el("p", { class: "lede", text: tr("home_lead") }),
    el("div", { class: "grid-3" }, [
      card("check", "home_low_title", "home_low", "low"),
      card("moon", "home_mid_title", "home_mid", "medium"),
      card("lungs", "home_high_title", "home_high", "high")
    ]),
    title("h2", "clipboard", tr("home_does_title")),
    el("p", { class: "lede", text: tr("home_does") }),
    el("div", { class: "grid-2" }, [
      card("list", "home_step_screen_title", "home_step_screen"),
      card("user", "home_step_you_title", "home_step_you"),
      card("moon", "home_step_sleep_title", "home_step_sleep"),
      card("heart", "home_step_heart_title", "home_step_heart")
    ]),
    title("h2", "table", tr("home_data_title")),
    el("p", { class: "lede", text: tr("home_data") }),
    title("h2", "shield", tr("home_scope_title")),
    el("p", { class: "lede", text: tr("home_scope") }),
    el("div", { class: "grid-2 landing-actions" }, [
      el("button", {
        type: "button",
        class: "primary",
        onclick: () => {
          state.screening.view = "questions";
          showPage("screen");
        }
      }, [icon("list"), el("span", { text: tr("home_start") })]),
      el("button", {
        type: "button",
        class: "secondary",
        onclick: () => showPage("eda")
      }, [icon("bars"), el("span", { text: tr("home_explore") })])
    ])
  ]);
}

function renderScreen() {
  if (state.screening.view === "triage" && state.screening.triage) {
    return renderScreenTriage(state.screening.triage);
  }
  const answered = screeningAnsweredCount();
  const sections = SCREENING_SECTIONS.map((section) => el("article", { class: "card screen-section" }, [
    title("h2", section.id === "before" ? "moon" : section.id === "during" ? "pulse" : "star", tr(`screen_section_${section.id}`)),
    el("div", { class: "screen-list" }, section.ids.map((id) => renderScreenQuestion(id)))
  ]));
  return el("section", { class: "screen-page" }, [
    title("h1", "list", tr("page_screen")),
    el("p", { class: "lede", text: tr("screen_lead") }),
    el("p", { class: "note", text: tr("screen_progress", { answered, total: SCREENING_IDS.length }) }),
    state.notice && state.notice.kind === "warn"
      ? el("p", { class: "banner-warn", text: state.notice.text })
      : null,
    ...sections,
    el("div", { class: "step-actions" }, [
      el("button", {
        type: "button",
        class: "secondary",
        onclick: resetScreening
      }, [icon("back"), el("span", { text: tr("screen_reset") })]),
      el("button", {
        type: "button",
        class: "primary",
        onclick: submitScreening
      }, [icon("decision"), el("span", { text: tr("screen_submit") })])
    ])
  ]);
}

function renderScreenQuestion(id) {
  const answer = state.screening.answers[id];
  const partner = PARTNER_DEPENDENT_IDS.has(id);
  const choice = (value, labelKey) => el("button", {
    type: "button",
    class: `screen-choice${answer === value ? " active" : ""}`,
    "aria-pressed": answer === value ? "true" : "false",
    onclick: () => setScreeningAnswer(id, value)
  }, [el("span", { text: tr(labelKey) })]);
  const choices = [
    choice(true, "screen_yes"),
    choice(false, "screen_no")
  ];
  if (partner) choices.push(choice("unknown", "screen_unknown"));
  return el("div", { class: "screen-item" }, [
    el("p", { class: "screen-q", text: `${id}. ${tr(`screen_q${id}`)}` }),
    partner ? el("p", { class: "field-help", text: tr("screen_partner_hint") }) : null,
    el("div", { class: `screen-choices${partner ? " three" : ""}` }, choices)
  ]);
}

function renderScreenTriage(triage) {
  const ranked = triage.flagged.length
    ? el("ol", { class: "screen-rank" }, triage.flagged.map((group, index) => el("li", {
      class: `screen-rank-item${group.deep ? " deep" : ""}`
    }, [
      el("strong", { text: tr(`screen_group_${group.id}`) }),
      el("span", {
        text: tr("screen_group_hits", {
          hits: group.hitCount,
          total: group.total,
          min: group.minHits,
          rank: index + 1
        })
      }),
      el("span", {
        text: group.trigger === "red_flag"
          ? tr("screen_trigger_red", { items: group.redHits.join(", ") })
          : tr("screen_trigger_threshold", { min: group.minHits })
      }),
      el("p", { text: tr(`screen_group_why_${group.id}`) })
    ])))
    : el("p", { class: "banner-ok", text: tr("screen_none_flagged") });

  const actions = [
    el("button", {
      type: "button",
      class: "secondary",
      onclick: () => {
        state.screening.view = "questions";
        saveSession();
        render();
      }
    }, [icon("back"), el("span", { text: tr("screen_edit") })])
  ];

  if (triage.deepEligible) {
    actions.push(el("button", {
      type: "button",
      class: "primary",
      onclick: () => showPage("assess")
    }, [icon("clipboard"), el("span", { text: tr("screen_go_deep") })]));
  } else {
    actions.push(el("button", {
      type: "button",
      class: "secondary",
      onclick: () => showPage("home")
    }, [icon("home"), el("span", { text: tr("screen_done") })]));
    actions.push(el("button", {
      type: "button",
      class: "primary",
      onclick: () => showPage("assess")
    }, [icon("clipboard"), el("span", { text: tr("screen_go_deep_optional") })]));
  }

  const tone = triage.deepEligible ? "high" : "low";
  const leadKey = triage.deepEligible ? "screen_triage_deep" : "screen_triage_low";

  return el("section", { class: "screen-page" }, [
    title("h1", "decision", tr("page_screen_result")),
    el("div", { class: `risk risk-${tone === "high" ? "high" : tone === "medium" ? "medium" : "low"}` }, [
      icon(tone === "high" ? "alert" : tone === "medium" ? "moon" : "check"),
      el("div", {}, [
        el("p", { class: "risk-kicker", text: tr("screen_rule_kicker") }),
        el("p", { class: "risk-title", text: tr(leadKey) })
      ])
    ]),
    el("p", { class: "lede", text: tr("screen_rule_explain", {
      yes: triage.yesCount,
      groups: triage.flagged.length,
      unknown: triage.unknownCount || 0
    }) }),
    triage.deepEligible
      ? null
      : el("p", { class: "banner-info", text: tr("screen_optional_deep_note") }),
    el("p", { class: "note", text: tr("screen_rule_policy") }),
    triage.unknownCount
      ? el("p", { class: "note", text: tr("screen_unknown_note", { unknown: triage.unknownCount }) })
      : null,
    title("h2", "bars", tr("screen_rank_title")),
    ranked,
    el("p", { class: "note", text: tr("screen_disclaimer") }),
    el("div", { class: "step-actions" }, actions)
  ]);
}

function field(iconName, label, control, help, badge) {
  return el("label", { class: "field" }, [
    el("span", { class: "field-label" }, [
      icon(iconName),
      el("span", { text: label }),
      badge || null
    ]),
    control,
    help ? el("span", { class: "field-help", text: help }) : null
  ]);
}

function watchBadge(key) {
  if (!WATCH_FORM_KEYS.includes(key) || !state.watchSource[key]) return null;
  return el("span", { class: "source-badge", text: tr("watch_badge") });
}

function markWatchManual(key) {
  if (!WATCH_FORM_KEYS.includes(key)) return;
  if (!state.watchSource[key]) return;
  state.watchSource[key] = false;
}

function importWatchDemo() {
  Object.assign(state.form, WATCH_DEMO);
  WATCH_FORM_KEYS.forEach((key) => {
    state.watchSource[key] = true;
  });
  state.notice = { kind: "ok", title: tr("watch_imported") };
  saveSession();
  render();
}

function numberField(iconName, label, key, min, max, step, help) {
  const input = el("input", {
    type: "number", id: key, min, max, step, value: state.form[key], inputmode: "decimal"
  });
  input.addEventListener("input", () => {
    state.form[key] = input.value;
    markWatchManual(key);
    if (key === "weight" || key === "height") updateBmi();
    refreshGuide();
    saveSession();
  });
  return field(iconName, label, input, help, watchBadge(key));
}

function selectField(iconName, label, key, options, group, help) {
  const select = el("select", { id: key });
  options.forEach((value) => {
    const option = el("option", { value, text: named(group, value) });
    option.selected = value === state.form[key];
    select.append(option);
  });
  select.addEventListener("change", () => {
    state.form[key] = select.value;
    saveSession();
  });
  return field(iconName, label, select, help);
}

function sliderField(iconName, label, key, min, max, help) {
  const input = el("input", { type: "range", min, max, step: "1", value: state.form[key] });
  const bubble = el("span", { class: "slider-value", id: `${key}-value`, text: state.form[key] });
  input.addEventListener("input", () => {
    state.form[key] = input.value;
    markWatchManual(key);
    bubble.textContent = input.value;
    refreshGuide();
    saveSession();
  });
  return field(iconName, label, el("div", { class: "slider-row" }, [input, bubble]), help, watchBadge(key));
}

function updateBmi() {
  const reading = readBmi();
  const value = document.getElementById("bmi-value");
  const category = document.getElementById("bmi-category");
  if (!reading || !value || !category) return;
  value.textContent = reading.display;
  category.textContent = named("bmi", reading.category);
}

const METER_FEATURE = {
  age: "Age",
  sleep: "Sleep Duration",
  quality: "Quality of Sleep",
  activity: "Physical Activity Level",
  stress: "Stress Level",
  steps: "Daily Steps",
  heart: "Heart Rate"
};
const BMI_SCALE = { min: 15, max: 40 };
const BMI_BANDS = [
  ["Underweight", 15, 18.5, "#BFDBFE"],
  ["Normal", 18.5, 25, "#86EFAC"],
  ["Overweight", 25, 30, "#FDE68A"],
  ["Obese", 30, 40, "#FECACA"]
];

function fractionBetween(value, min, max) {
  if (!Number.isFinite(value) || max === min) return 0;
  return Math.max(0, Math.min(1, (value - min) / (max - min)));
}

function meter(key, label, bounds) {
  const [min, max] = bounds;
  const value = Number(state.form[key]);
  const fraction = fractionBetween(value, min, max);
  const fill = el("div", { class: "meter-fill" });
  fill.style.width = `${fraction * 100}%`;
  const marker = el("div", { class: "meter-marker" });
  marker.style.left = `${fraction * 100}%`;
  return el("div", { class: "meter", "data-meter": key, "data-min": String(min), "data-max": String(max) }, [
    el("div", { class: "meter-head" }, [
      el("span", { text: label }),
      el("strong", { "data-readout": key, text: pretty(METER_FEATURE[key], value) })
    ]),
    el("div", { class: "meter-track" }, [fill, marker]),
    el("div", { class: "meter-scale" }, [
      el("span", { text: String(min) }),
      el("span", { text: String(max) })
    ])
  ]);
}

function bmiVisual(reading) {
  const span = BMI_SCALE.max - BMI_SCALE.min;
  const bands = el("div", { class: "bmi-scale" }, BMI_BANDS.map(([, low, high, color]) => {
    const band = el("div", { class: "bmi-band" });
    band.style.width = `${((high - low) / span) * 100}%`;
    band.style.background = color;
    return band;
  }));
  const marker = el("div", { class: "bmi-marker", "data-bmi-marker": "1" });
  const fraction = reading ? fractionBetween(reading.bmi, BMI_SCALE.min, BMI_SCALE.max) : 0;
  marker.style.left = `${fraction * 100}%`;
  marker.style.display = reading ? "" : "none";
  return el("div", { class: "viz" }, [
    title("h3", "scale", tr("viz_you")),
    el("div", { class: "bmi-scale-wrap" }, [bands, marker]),
    el("div", { class: "band-legend" }, BMI_BANDS.map(([category, , , color]) => {
      const swatch = el("span", { class: "swatch" });
      swatch.style.background = color;
      return el("span", {}, [swatch, named("bmi", category)]);
    })),
    el("p", {
      class: "note",
      id: "bmi-caption",
      text: reading ? tr("bmi_place", { category: named("bmi", reading.category) }) : tr("bmi_missing")
    }),
    meter("age", tr("age"), state.meta.limits.Age)
  ]);
}

function lifestyleVisual() {
  const limits = state.meta.limits;
  return el("div", { class: "viz" }, [
    title("h3", "moon", tr("viz_sleep")),
    meter("sleep", tr("sleep_duration"), limits["Sleep Duration"]),
    meter("quality", tr("quality"), limits["Quality of Sleep"]),
    meter("activity", tr("activity"), limits["Physical Activity Level"]),
    meter("stress", tr("stress"), limits["Stress Level"]),
    meter("steps", tr("steps"), limits["Daily Steps"])
  ]);
}

function heartVisual() {
  const limits = state.meta.limits;
  return el("div", { class: "viz" }, [
    title("h3", "heart", tr("viz_heart")),
    meter("heart", tr("heart_rate"), limits["Heart Rate"])
  ]);
}

function guidePanel(step, reading) {
  const stories = ["story_you", "story_sleep", "story_heart", "story_review"];
  const pictures = step === 0
    ? [bmiVisual(reading)]
    : step === 1
      ? [lifestyleVisual()]
      : step === 2
        ? [heartVisual()]
        : [bmiVisual(reading), lifestyleVisual(), heartVisual()];
  return el("aside", { class: "guide" }, [
    title("h2", "decision", tr("guide_title")),
    el("p", { class: "story", text: tr(stories[step]) }),
    ...pictures
  ]);
}

function refreshGuide() {
  document.querySelectorAll("[data-meter]").forEach((row) => {
    const key = row.dataset.meter;
    const value = Number(state.form[key]);
    const fraction = fractionBetween(value, Number(row.dataset.min), Number(row.dataset.max));
    const fill = row.querySelector(".meter-fill");
    const marker = row.querySelector(".meter-marker");
    const readout = row.querySelector("[data-readout]");
    if (fill) fill.style.width = `${fraction * 100}%`;
    if (marker) marker.style.left = `${fraction * 100}%`;
    if (readout && Number.isFinite(value)) readout.textContent = pretty(METER_FEATURE[key], value);
  });
  const marker = document.querySelector("[data-bmi-marker]");
  const caption = document.getElementById("bmi-caption");
  if (!marker && !caption) return;
  const reading = readBmi();
  if (marker) {
    marker.style.display = reading ? "" : "none";
    if (reading) marker.style.left = `${fractionBetween(reading.bmi, BMI_SCALE.min, BMI_SCALE.max) * 100}%`;
  }
  if (caption) {
    caption.textContent = reading
      ? tr("bmi_place", { category: named("bmi", reading.category) })
      : tr("bmi_missing");
  }
}

function resultStory(result, decision) {
  const profile = result.profile;
  const risk = (decision && decision.risk_level) || result.risk_level;
  return tr("result_story", {
    age: profile.Age,
    gender: named("gender", profile.Gender),
    job: named("job", profile.Occupation),
    bmi: result.body.bmi_display,
    category: named("bmi", result.body.category),
    sleep: Number(profile["Sleep Duration"]).toFixed(1),
    quality: profile["Quality of Sleep"],
    stress: profile["Stress Level"],
    hr: profile["Heart Rate"],
    steps: pretty("Daily Steps", profile["Daily Steps"]),
    label: named("class", result.label),
    risk: named("risk", risk)
  });
}

function renderAssess() {
  if (!canAccessDeepAssess()) {
    return el("section", {}, [
      title("h1", "clipboard", tr("page_assess")),
      el("p", { class: "banner-warn", text: tr("assess_locked") }),
      el("div", { class: "step-actions" }, [
        el("button", {
          type: "button",
          class: "primary",
          onclick: () => showPage("screen")
        }, [icon("list"), el("span", { text: tr("nav_screen") })])
      ])
    ]);
  }
  const limits = state.meta.limits;
  const reading = readBmi();
  const step = Math.min(3, Math.max(0, state.step || 0));
  state.step = step;
  const steps = [
    ["user", "step_personal"],
    ["moon", "step_sleep"],
    ["heart", "step_heart"],
    ["list", "step_review"]
  ];
  const stepper = el("div", { class: "stepper" }, steps.map(([iconName, key], index) => {
    const button = el("button", {
      type: "button",
      class: index === step ? "current" : index < step ? "done" : "",
      disabled: index > step ? "disabled" : null
    }, [
      icon(iconName),
      el("span", { class: "step-index", text: String(index + 1) }),
      el("span", { text: tr(key) })
    ]);
    if (index <= step) {
      button.addEventListener("click", () => {
        if (index !== step) moveStep(index);
      });
    }
    if (index === step) button.setAttribute("aria-current", "step");
    return button;
  }));
  let body = null;
  if (step === 0) {
    body = el("div", {}, [
      title("h2", "user", tr("personal")),
      el("p", { class: "note", text: tr("personal_hint") }),
      el("div", { class: "card grid-3" }, [
        selectField("user", tr("gender"), "gender", state.meta.genders, "gender"),
        numberField("calendar", tr("age"), "age", limits.Age[0], limits.Age[1], "1"),
        selectField("briefcase", tr("occupation"), "occupation", occupationChoices(), "job", tr("occupation_help")),
        numberField("scale", tr("weight"), "weight", state.meta.weight_limits[0], state.meta.weight_limits[1], "0.1", tr("weight_help")),
        numberField("ruler", tr("height"), "height", state.meta.height_limits[0], state.meta.height_limits[1], "0.1", tr("height_help")),
        el("div", { class: "bmi-card" }, [
          icon("scale"),
          el("div", {}, [
            el("p", { class: "kicker", text: tr("bmi_short") }),
            el("p", { class: "bmi-value", id: "bmi-value", text: reading ? reading.display : "—" }),
            el("p", { class: "bmi-meta", id: "bmi-category", text: reading ? named("bmi", reading.category) : "" })
          ])
        ])
      ])
    ]);
  } else if (step === 1) {
    body = el("div", {}, [
      title("h2", "moon", tr("sleep_section")),
      el("p", { class: "note", text: tr("watch_section_hint") }),
      el("div", { class: "step-actions" }, [
        el("button", {
          type: "button",
          class: "secondary",
          onclick: importWatchDemo
        }, [icon("pulse"), el("span", { text: tr("watch_import") })])
      ]),
      el("div", { class: "card grid-2" }, [
        numberField("moon", tr("sleep_duration"), "sleep", limits["Sleep Duration"][0], limits["Sleep Duration"][1], "0.1", tr("watch_field_help")),
        sliderField("star", tr("quality"), "quality", limits["Quality of Sleep"][0], limits["Quality of Sleep"][1], tr("quality_help")),
        numberField("pulse", tr("activity"), "activity", limits["Physical Activity Level"][0], limits["Physical Activity Level"][1], "1", tr("watch_field_help")),
        sliderField("bolt", tr("stress"), "stress", limits["Stress Level"][0], limits["Stress Level"][1], tr("stress_help")),
        numberField("steps", tr("steps"), "steps", limits["Daily Steps"][0], limits["Daily Steps"][1], "100", tr("watch_field_help"))
      ])
    ]);
  } else if (step === 2) {
    body = el("div", {}, [
      title("h2", "heart", tr("cardio")),
      el("p", { class: "note", text: tr("watch_heart_hint") }),
      el("div", { class: "step-actions" }, [
        el("button", {
          type: "button",
          class: "secondary",
          onclick: importWatchDemo
        }, [icon("pulse"), el("span", { text: tr("watch_import") })])
      ]),
      el("div", { class: "card grid-2" }, [
        numberField("heart", tr("heart_rate"), "heart", limits["Heart Rate"][0], limits["Heart Rate"][1], "1", tr("watch_field_help"))
      ])
    ]);
  } else {
    body = el("div", {}, [
      title("h2", "list", tr("step_review")),
      reviewCard(reading)
    ]);
  }
  const actions = el("div", { class: "step-actions" }, [
    step > 0 ? el("button", { class: "secondary", type: "button", onclick: () => moveStep(step - 1) }, [
      icon("back"),
      el("span", { text: tr("back") })
    ]) : null,
    step < 3
      ? el("button", { class: "primary", type: "submit" }, [icon("arrow"), el("span", { text: tr("next") })])
      : el("button", { class: "primary", type: "submit", disabled: state.busy ? "disabled" : null }, [
        icon("pulse"),
        el("span", { text: tr("evaluate") })
      ])
  ]);
  const form = el("form", {
    onsubmit: (event) => {
      event.preventDefault();
      if (state.step < 3) goNext();
      else submitAssess();
    }
  }, [
    body,
    el("div", { class: "stack" }, [
      actions,
      noticeNode(),
      state.result ? el("button", {
        class: "secondary",
        type: "button",
        onclick: () => showPage("result")
      }, [icon("arrow"), el("span", { text: tr("view_result") })]) : null
    ])
  ]);
  return el("section", {}, [
    el("div", { class: "banner" }, [
      el("img", { src: "/assets/clinic-background.jpg", alt: tr("banner_alt") }),
      el("div", {}, [
        el("p", { class: "kicker", text: tr("banner_kicker") }),
        el("p", { text: tr("banner_body") })
      ])
    ]),
    title("h1", "clipboard", tr("page_assess")),
    el("p", { class: "lede", text: tr("step_of", { current: step + 1, total: 4 }) }),
    step < 3 ? el("p", { class: "note", text: tr("assess_intro") }) : null,
    stepper,
    el("div", { class: "assess-layout" }, [form, guidePanel(step, reading)])
  ]);
}

function reviewCard(reading) {
  const row = (label, value, fromWatch) => el("div", { class: "review-row" }, [
    el("span", {}, [
      el("span", { text: label }),
      fromWatch ? el("span", { class: "source-badge", text: tr("watch_badge") }) : null
    ]),
    el("strong", { text: value })
  ]);
  return el("div", { class: "card review" }, [
    row(tr("gender"), named("gender", state.form.gender), false),
    row(tr("age"), state.form.age, false),
    row(tr("occupation"), named("job", state.form.occupation), false),
    row(tr("weight"), `${Number(state.form.weight).toFixed(1)} ${tr("kg")}`, false),
    row(tr("height"), `${Number(state.form.height).toFixed(1)} ${tr("cm")}`, false),
    row(tr("bmi_short"), reading ? `${reading.display} · ${named("bmi", reading.category)}` : "—", false),
    row(tr("sleep_duration"), pretty("Sleep Duration", state.form.sleep), state.watchSource.sleep),
    row(tr("quality"), pretty("Quality of Sleep", state.form.quality), state.watchSource.quality),
    row(tr("activity"), pretty("Physical Activity Level", state.form.activity), state.watchSource.activity),
    row(tr("stress"), pretty("Stress Level", state.form.stress), state.watchSource.stress),
    row(tr("steps"), pretty("Daily Steps", state.form.steps), state.watchSource.steps),
    row(tr("heart_rate"), pretty("Heart Rate", state.form.heart), state.watchSource.heart)
  ]);
}

function noticeNode() {
  if (!state.notice) return null;
  const notice = state.notice;
  let title = notice.title || "";
  const lines = notice.code === "failed" && notice.client
    ? stepErrors(state.step).concat(state.result ? [tr("kept_result")] : [])
    : (notice.lines || []).slice();
  if (notice.code === "saved") {
    title = tr("saved", {
      bmi: notice.bmi,
      category: named("bmi", notice.category),
      label: named("class", notice.label)
    });
    if (notice.actionKey) lines.unshift(tr("saved_action", { action: tr(notice.actionKey) }));
  } else if (notice.code === "failed") title = tr("score_failed");
  else if (notice.code === "offline") title = tr("load_failed");
  const tone = notice.code === "saved"
    ? `banner-tone banner-${classTone(notice.label)}`
    : "";
  const box = el("div", {
    class: tone || (notice.kind === "ok" ? "banner-ok" : "banner-warn"),
    role: "status"
  });
  box.append(el("p", { text: title }));
  lines.forEach((line) => box.append(el("p", { text: line })));
  return box;
}

function pushRange(errors, feature, key) {
  const value = Number(state.form[key]);
  const [low, high] = state.meta.limits[feature];
  if (!Number.isFinite(value)) errors.push(tr("required", { name: named("feature", feature) }));
  else if (value < low || value > high) errors.push(tr("between", { name: named("feature", feature), low, high }));
}

function stepErrors(step) {
  const errors = [];
  const checkBody = step === 0 || step === 3;
  const checkSleep = step === 1 || step === 3;
  const checkHeart = step === 2 || step === 3;
  if (checkBody) {
    const weight = Number(state.form.weight);
    const height = Number(state.form.height);
    if (!Number.isFinite(weight) || weight < 30 || weight > 250) errors.push(tr("weight_range"));
    if (!Number.isFinite(height) || height < 120 || height > 220) errors.push(tr("height_range"));
    pushRange(errors, "Age", "age");
  }
  if (checkSleep) {
    [
      ["Sleep Duration", "sleep"],
      ["Quality of Sleep", "quality"],
      ["Physical Activity Level", "activity"],
      ["Stress Level", "stress"],
      ["Daily Steps", "steps"]
    ].forEach(([feature, key]) => pushRange(errors, feature, key));
  }
  if (checkHeart) {
    pushRange(errors, "Heart Rate", "heart");
  }
  return errors;
}

function clientErrors() {
  return stepErrors(3);
}

function moveStep(nextStep) {
  state.notice = null;
  state.step = nextStep;
  saveSession();
  render();
}

function goNext() {
  if (stepErrors(state.step).length) {
    state.notice = { kind: "error", code: "failed", client: true };
    saveSession();
    render();
    return;
  }
  moveStep(Math.min(3, state.step + 1));
}

async function submitAssess() {
  const errors = clientErrors();
  if (errors.length) {
    state.notice = { kind: "error", code: "failed", client: true };
    saveSession();
    render();
    return;
  }
  state.busy = true;
  render();
  const payload = {
    Gender: state.form.gender,
    Age: Number(state.form.age),
    Occupation: state.form.occupation,
    weight_kg: Number(state.form.weight),
    height_cm: Number(state.form.height),
    "Sleep Duration": Number(state.form.sleep),
    "Quality of Sleep": Number(state.form.quality),
    "Physical Activity Level": Number(state.form.activity),
    "Stress Level": Number(state.form.stress),
    "Daily Steps": Number(state.form.steps),
    "Heart Rate": Number(state.form.heart),
    data_sources: {
      watch: WATCH_FORM_KEYS.filter((key) => state.watchSource[key]),
      manual: WATCH_FORM_KEYS.filter((key) => !state.watchSource[key]).concat([
        "gender", "age", "occupation", "weight", "height"
      ])
    }
  };
  try {
    const response = await fetch("/api/assess", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const body = await response.json();
    if (!response.ok) {
      const lines = (body.errors || []).map(errorText);
      state.notice = {
        kind: "error",
        code: "failed",
        lines: lines.concat(state.result ? [tr("kept_result")] : [])
      };
    } else {
      const standards = refreshStandards(state.screening.triage, {
        age: Number(state.form.age),
        gender: state.form.gender,
        bmi: body.body && body.body.bmi,
        quality: Number(state.form.quality)
      });
      const triage = state.screening.triage;
      const screenClass = triage && triage.deepEligible ? triage.topClass : "None";
      const logPrior = await fetchLogPrior({
        screen_class: screenClass,
        model_label: body.label,
        age: Number(state.form.age),
        bmi_category: body.body && body.body.category,
        min_similar: 3,
        age_window: 10
      });
      const decision = buildDecision(body, triage, logPrior);
      const yesIds = SCREENING_IDS.filter((id) => state.screening.answers[id] === true);
      state.result = Object.assign({}, body, {
        decision,
        standards,
        log_prior: logPrior,
        screening: triage
          ? {
            top_class: triage.topClass,
            flagged: triage.flagged.map((group) => ({
              id: group.id,
              hitCount: group.hitCount,
              minHits: group.minHits,
              trigger: group.trigger,
              redHits: group.redHits
            })),
            yesCount: triage.yesCount,
            yes_ids: yesIds,
            standards
          }
          : null
      });
      await postAssessmentLog(state.result, decision, payload);
      state.notice = {
        kind: "ok",
        code: "saved",
        bmi: body.body.bmi_display,
        category: body.body.category,
        label: body.label,
        risk: decision.risk_level,
        conflict: decision.conflict,
        actionKey: nextActionKey(decision),
        logged: Boolean(state.result.log_id)
      };
    }
  } catch (_error) {
    state.notice = { kind: "error", code: "offline" };
  }
  state.busy = false;
  saveSession();
  render();
}

function renderResult() {
  if (!state.result) {
    return el("section", {}, [
      title("h1", "list", tr("page_result")),
      el("p", { class: "story", text: tr("empty_story") }),
      el("p", { class: "banner-info inline-note" }, [icon("clipboard"), el("span", { text: tr("empty_result") })])
    ]);
  }
  const result = state.result;
  const decision = result.decision || buildDecision(result, state.screening.triage);
  const body = result.body;
  const riskLevel = decision.risk_level;
  const heroTone = classTone(result.label);
  const actionKey = nextActionKey(decision);
  const importanceRows = topImportanceRows(result.importances, 5);
  const conflictBanner = decision.conflict
    ? el("p", { class: "banner-warn", text: tr(`conflict_${decision.conflict}`) })
    : null;
  const screenCard = result.screening
    ? el("div", { class: "card" }, [
      title("h2", "list", tr("result_screen_title")),
      el("p", {
        text: tr("result_screen_summary", {
          screen: named("class", result.screening.top_class),
          model: named("class", result.label),
          conf: `${(decision.top_probability * 100).toFixed(1)}%`,
          band: tr(`confidence_${decision.confidence_band}`)
        })
      }),
      el("p", {
        class: "note",
        text: tr("result_hybrid_line", {
          screen: `${(Number(decision.screen_strength || 0) * 100).toFixed(0)}%`,
          hybrid: `${(Number(decision.hybrid_score || 0) * 100).toFixed(0)}%`
        })
      }),
      el("p", { class: "note", text: tr("result_hybrid_note") }),
      result.screening.flagged && result.screening.flagged.length
        ? el("ul", { class: "actions" }, result.screening.flagged.map((group) => el("li", {
          text: tr("result_screen_group", {
            name: tr(`screen_group_${group.id}`),
            hits: group.hitCount,
            min: group.minHits,
            trigger: group.trigger === "red_flag"
              ? tr("screen_trigger_red", { items: (group.redHits || []).join(", ") })
              : tr("screen_trigger_threshold", { min: group.minHits })
          })
        })))
        : el("p", { class: "note", text: tr("result_screen_none") }),
      result.screening.yes_ids && result.screening.yes_ids.length
        ? el("p", { class: "note", text: tr("result_yes_items", { items: result.screening.yes_ids.join(", ") }) })
        : null
    ])
    : null;
  return el("section", {}, [
    title("h1", "list", tr("page_result")),
    el("p", { class: "lede", text: tr("result_caption") }),
    conflictBanner,
    screenCard,
    el("div", { class: "card story-card" }, [
      title("h2", "decision", tr("visit_title")),
      el("p", { class: "story", text: resultStory(result, decision) }),
      el("p", { class: "note", text: tr("result_next") })
    ]),
    title("h2", "scale", tr("body")),
    el("div", { class: "metrics" }, [
      metric("scale", tr("weight"), `${Number(body.weight_kg).toFixed(1)} ${tr("kg")}`),
      metric("ruler", tr("height"), `${Number(body.height_cm).toFixed(1)} ${tr("cm")}`),
      metric("scale", tr("bmi_short"), body.bmi_display),
      metric("user", tr("bmi_category"), named("bmi", body.category), body.category.toLowerCase())
    ]),
    el("p", { class: "note", text: tr("bmi_formula") }),
    el("div", { class: `risk risk-${heroTone}` }, [
      icon(CLASS_ICONS[result.label] || RISK_ICONS[riskLevel]),
      el("div", {}, [
        el("p", { class: "risk-kicker", text: tr("result_model_kicker") }),
        el("p", { class: "risk-title", text: named("class", result.label) }),
        el("p", { class: "note", text: tr("confidence_line", {
          conf: `${(decision.top_probability * 100).toFixed(1)}%`,
          band: tr(`confidence_${decision.confidence_band}`)
        }) }),
        el("p", {
          class: `action-line action-${decision.conflict ? "conflict" : riskLevel.toLowerCase()}`,
          text: tr("result_next_action", { action: tr(actionKey) })
        })
      ])
    ]),
    decision.notes && decision.notes.includes("screen_boost")
      ? el("p", { class: "banner-info", text: tr("screen_boost_note") })
      : null,
    title("h2", "bars", tr("probabilities")),
    el("p", { class: "note", text: tr("probabilities_caption") }),
    probabilitySpider(result.probabilities),
    title("h2", "pulse", tr("importance")),
    el("p", { class: "note", text: tr("importance_caption") }),
    importanceRankCard(importanceRows),
    title("h2", "compare", tr("comparison")),
    el("p", { class: "note", text: tr("comparison_caption") }),
    result.factors && result.factors.length
      ? el("ul", { class: "card actions" }, result.factors.map((factor) => el("li", { text: factorText(factor) })))
      : el("p", { class: "banner-info", text: tr("no_factors") }),
    reduceRisk(result, decision),
    renderLogPriorPanel(result.log_prior || decision.log_prior),
    title("h2", "table", tr("submitted")),
    profileTable(result.profile)
  ]);
}

function renderLogPriorPanel(prior) {
  if (!prior) {
    return el("section", { class: "card" }, [
      title("h2", "rows", tr("log_prior_title")),
      el("p", { class: "note", text: tr("log_prior_unavailable") })
    ]);
  }
  const rateText = (value) => (value == null ? "—" : `${(Number(value) * 100).toFixed(0)}%`);
  return el("section", { class: "card" }, [
    title("h2", "rows", tr("log_prior_title")),
    el("p", { class: "lede", text: tr("log_prior_lead") }),
    el("p", { class: "note", text: prior.note || tr("log_prior_note") }),
    el("p", {
      text: tr("log_prior_match", {
        screen: named("class", prior.match && prior.match.screen_class),
        model: named("class", prior.match && prior.match.model_label),
        age: prior.match && prior.match.age != null ? prior.match.age : "—",
        window: prior.match && prior.match.age_window != null ? prior.match.age_window : 10,
        bmi: prior.match && prior.match.bmi_category ? named("bmi", prior.match.bmi_category) : "—"
      })
    }),
    el("p", {
      text: tr("log_prior_counts", {
        similar: prior.similar_count || 0,
        min: prior.min_similar || 3,
        conflict: rateText(prior.conflict_rate),
        high: rateText(prior.high_risk_rate)
      })
    }),
    prior.eligible
      ? (prior.escalate
        ? el("p", { class: "banner-warn", text: tr("log_prior_escalate") })
        : el("p", { class: "banner-ok", text: tr("log_prior_stable") }))
      : el("p", { class: "banner-info", text: tr("log_prior_insufficient") })
  ]);
}

function reduceRisk(result, decision) {
  const riskLevel = decision.risk_level;
  const tone = classTone(result.label);
  const actionKey = nextActionKey(decision);
  return el("section", { class: `card reduce-risk tone-${tone}` }, [
    title("h2", CLASS_ICONS[result.label] || RISK_ICONS[riskLevel] || "shield", tr("reduce_title")),
    el("p", { class: "lede", text: tr("reduce_lead", {
      label: named("class", result.label),
      action: tr(actionKey)
    }) }),
    el("p", { text: decision.decision }),
    el("ol", { class: "actions" }, decision.actions.map((action) => el("li", { text: action })))
  ]);
}

function metric(iconName, label, value, tone) {
  return el("div", { class: tone ? `metric metric-${tone}` : "metric" }, [
    el("p", { class: "metric-label" }, [icon(iconName), el("span", { text: label })]),
    el("p", { class: "metric-value", text: value })
  ]);
}

function barRow(label, fraction, value, color, iconName, paintLabel) {
  const width = Math.max(0, Math.min(1, fraction)) * 100;
  const fill = el("div", { class: "bar-fill" });
  fill.style.width = `${width}%`;
  fill.style.background = color;
  const labelNode = el("span", { class: "bar-label" }, iconName ? [icon(iconName), el("span", { text: label })] : [label]);
  if (paintLabel) labelNode.style.color = color;
  return el("div", { class: "bar-row" }, [
    labelNode,
    el("div", { class: "bar-track" }, [fill]),
    el("span", { class: "bar-value", text: value })
  ]);
}

function topImportanceRows(importances, limit) {
  const ranked = (importances || []).slice().sort((a, b) => b.importance - a.importance);
  const top = ranked.slice(0, limit);
  const rest = ranked.slice(limit);
  const restSum = rest.reduce((sum, item) => sum + Number(item.importance || 0), 0);
  const rows = top.map((item) => ({
    key: item.feature,
    label: named("feature", item.feature),
    importance: item.importance,
    iconName: FEATURE_ICONS[item.feature]
  }));
  if (restSum > 0) {
    rows.push({
      key: "__other__",
      label: tr("importance_other"),
      importance: restSum,
      iconName: "dots"
    });
  }
  return rows;
}

function importanceRankCard(rows) {
  return el("div", { class: "card rank-list" }, rows.map((row, index) => el("div", { class: "rank-row" }, [
    el("span", { class: "rank-index", text: String(index + 1) }),
    el("span", { class: "rank-label" }, [
      row.iconName ? icon(row.iconName) : null,
      el("span", { text: row.label })
    ]),
    el("strong", { class: "rank-value", text: `${(row.importance * 100).toFixed(1)}%` })
  ])));
}

function probabilitySpider(probabilities) {
  const size = 280;
  const center = size / 2;
  const radius = 92;
  const values = CLASS_ORDER.map((label) => Math.max(0, Math.min(1, Number(probabilities[label] || 0))));
  const angleAt = (index) => (-Math.PI / 2) + (index * 2 * Math.PI) / CLASS_ORDER.length;
  const pointAt = (index, fraction) => {
    const angle = angleAt(index);
    return [
      center + Math.cos(angle) * radius * fraction,
      center + Math.sin(angle) * radius * fraction
    ];
  };
  const rings = [0.25, 0.5, 0.75, 1].map((fraction) => {
    const points = CLASS_ORDER.map((_, index) => pointAt(index, fraction).join(",")).join(" ");
    return elSvg("polygon", {
      points,
      class: "spider-ring"
    });
  });
  const axes = CLASS_ORDER.map((_, index) => {
    const [x, y] = pointAt(index, 1);
    return elSvg("line", {
      x1: String(center),
      y1: String(center),
      x2: String(x),
      y2: String(y),
      class: "spider-axis"
    });
  });
  const areaPoints = values.map((value, index) => pointAt(index, value).join(",")).join(" ");
  const dots = values.map((value, index) => {
    const [x, y] = pointAt(index, value);
    return elSvg("circle", {
      cx: String(x),
      cy: String(y),
      r: "4.5",
      fill: COLORS[CLASS_ORDER[index]]
    });
  });
  const labels = CLASS_ORDER.map((label, index) => {
    const [x, y] = pointAt(index, 1.28);
    return el("div", {
      class: "spider-label",
      style: `left:${(x / size) * 100}%;top:${(y / size) * 100}%`
    }, [
      el("span", { class: "spider-swatch", style: `background:${COLORS[label]}` }),
      el("span", { text: `${named("class", label)} ${(values[index] * 100).toFixed(1)}%` })
    ]);
  });
  const svg = elSvg("svg", {
    viewBox: `0 0 ${size} ${size}`,
    class: "spider-svg",
    role: "img",
    "aria-label": tr("probabilities")
  }, [
    ...rings,
    ...axes,
    elSvg("polygon", { points: areaPoints, class: "spider-area" }),
    ...dots
  ]);
  return el("div", { class: "card spider-card" }, [
    el("div", { class: "spider-wrap" }, [svg, ...labels])
  ]);
}

function elSvg(tag, attrs, children) {
  const node = document.createElementNS(SVG_NS, tag);
  Object.entries(attrs || {}).forEach(([key, value]) => {
    if (value == null) return;
    if (key === "class") node.setAttribute("class", value);
    else node.setAttribute(key, String(value));
  });
  const list = children == null ? [] : Array.isArray(children) ? children : [children];
  list.forEach((child) => {
    if (child == null || child === false) return;
    node.appendChild(child instanceof Node ? child : document.createTextNode(String(child)));
  });
  return node;
}

function profileTable(profile) {
  const table = el("table", {}, [
    el("thead", {}, [el("tr", {}, [el("th", { text: tr("field") }), el("th", { text: tr("value") })])])
  ]);
  const body = el("tbody");
  PROFILE_FIELDS.forEach((feature) => {
    body.append(el("tr", {}, [
      el("td", { text: named("feature", feature) }),
      el("td", { text: profileValue(feature, profile[feature]) })
    ]));
  });
  table.append(body);
  return el("div", { class: "card chart-scroll" }, [table]);
}

function formatLogTime(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString(state.lang === "th" ? "th-TH" : "en-GB");
}

function shortAnon(value) {
  const text = String(value || "");
  if (text.length <= 12) return text || "—";
  return `${text.slice(0, 8)}…`;
}

async function fetchLogPeople() {
  try {
    const response = await fetch("/api/logs/people?limit=200");
    if (!response.ok) throw new Error("people_failed");
    state.logsPeople = await response.json();
    if (!state.logsPerson && state.logsPeople.people && state.logsPeople.people.length) {
      state.logsPerson = state.logsPeople.people[0].anon_id;
    }
  } catch (_error) {
    state.logsPeople = null;
  }
}

async function fetchLogs() {
  state.logsBusy = true;
  state.logsNotice = null;
  if (state.page === "logs") render();
  try {
    await fetchLogPeople();
    const params = new URLSearchParams({ limit: "200", enrich: "true" });
    if (state.logsPerson) params.set("anon_id", state.logsPerson);
    const response = await fetch(`/api/logs?${params.toString()}`);
    if (!response.ok) throw new Error("logs_failed");
    state.logs = await response.json();
  } catch (_error) {
    state.logs = null;
    state.logsNotice = { kind: "error", text: tr("logs_load_failed") };
  }
  state.logsBusy = false;
  if (state.page === "logs") render();
}

async function selectLogPerson(anonId) {
  state.logsPerson = anonId || "";
  state.logsDetail = null;
  await fetchLogs();
}

async function fetchLogDetail(rowId) {
  state.logsBusy = true;
  state.logsNotice = null;
  render();
  try {
    const response = await fetch(`/api/logs/${rowId}?enrich=true`);
    if (!response.ok) throw new Error("detail_failed");
    state.logsDetail = await response.json();
  } catch (_error) {
    state.logsDetail = null;
    state.logsNotice = { kind: "error", text: tr("logs_detail_failed") };
  }
  state.logsBusy = false;
  if (state.page === "logs") render();
}

function yesNoLabel(value) {
  if (value === true || value === "yes") return tr("logs_yes");
  if (value === false || value === "no") return tr("logs_no");
  if (value == null) return "—";
  return String(value);
}

function numOrDash(value) {
  if (value == null || value === "") return "—";
  return String(value);
}

function matchNumLabel(value) {
  if (value == null) return "—";
  return `${numOrDash(value)} · ${yesNoLabel(value === 1 || value === true)}`;
}

function classCodeLabel(label, code) {
  const name = label ? named("class", label) : tr("logs_gt_proxy_na");
  if (code == null || code === "") return name;
  return `${code} · ${name}`;
}

function renderPersonLogDetail(detail) {
  if (!detail) return null;
  const qRows = [];
  for (let q = 1; q <= 13; q += 1) {
    const num = detail[`q${q}_num`];
    qRows.push(el("tr", {}, [
      el("td", { text: `Q${q}` }),
      el("td", { text: tr(`screen_q${q}`) }),
      el("td", { text: detail[`q${q}`] || "—" }),
      el("td", { text: numOrDash(num) })
    ]));
  }
  const compareRows = [
    ["logs_gt_rule", classCodeLabel(detail.gt_rule_class || "None", detail.gt_rule_class_code)],
    ["logs_gt_proxy", detail.gt_proxy_class
      ? classCodeLabel(detail.gt_proxy_class, detail.gt_proxy_class_code)
      : tr("logs_gt_proxy_na")],
    ["logs_col_screen", classCodeLabel(detail.screen_class || "None", detail.screen_class_code)],
    ["logs_col_model", classCodeLabel(detail.model_label || "None", detail.model_label_code)],
    ["logs_col_risk", detail.risk_level
      ? `${numOrDash(detail.risk_code)} · ${detail.risk_level}`
      : "—"],
    ["logs_col_hybrid", detail.hybrid_score != null ? Number(detail.hybrid_score).toFixed(3) : "—"],
    ["logs_agreement", numOrDash(detail.agreement_score)],
    ["logs_q_yes_score", numOrDash(detail.questionnaire_yes_score)],
    ["logs_system_doctor", matchNumLabel(detail.system_see_doctor_num)],
    ["logs_match_rule_model", matchNumLabel(detail.match_rule_vs_model_num)],
    ["logs_match_proxy_model", matchNumLabel(detail.match_proxy_vs_model_num)],
    ["logs_match_rule_proxy", matchNumLabel(detail.match_rule_vs_proxy_num)],
    ["logs_proxy_n", detail.gt_proxy_similar_count != null ? String(detail.gt_proxy_similar_count) : "—"],
    ["logs_score_why", detail.score_why_th || detail.score_why || "—"]
  ].map(([key, value]) => el("tr", {}, [
    el("td", { text: tr(key) }),
    el("td", { text: value })
  ]));
  return el("section", { class: "card" }, [
    title("h2", "table", tr("logs_detail_title", { id: detail.id })),
    el("p", { class: "note", text: tr("logs_detail_anon", { anon: detail.anon_id }) }),
    el("p", { class: "banner-info", text: tr("logs_gt_explain") }),
    el("p", { class: "note", text: tr("logs_code_legend") }),
    title("h3", "list", tr("logs_compare_title")),
    el("div", { class: "card chart-scroll" }, [
      el("table", {}, [
        el("thead", {}, [el("tr", {}, [el("th", { text: tr("field") }), el("th", { text: tr("value") })])]),
        el("tbody", {}, compareRows)
      ])
    ]),
    title("h3", "clipboard", tr("logs_quest_title")),
    el("div", { class: "card chart-scroll" }, [
      el("table", {}, [
        el("thead", {}, [el("tr", {}, [
          el("th", { text: tr("logs_q_id") }),
          el("th", { text: tr("logs_q_text") }),
          el("th", { text: tr("logs_q_answer") }),
          el("th", { text: tr("logs_q_num") })
        ])]),
        el("tbody", {}, qRows)
      ])
    ]),
    title("h3", "rows", tr("logs_raw_title")),
    el("pre", { class: "logs-json", text: JSON.stringify({
      form_payload: detail.form_payload,
      decision: detail.decision,
      profile: detail.profile,
      gt_proxy_match: detail.gt_proxy_match,
      score_why: detail.score_why,
      score_why_th: detail.score_why_th,
      agreement_score: detail.agreement_score
    }, null, 2) })
  ]);
}

function pctRate(rate) {
  if (rate == null || !Number.isFinite(Number(rate))) return "—";
  return `${(Number(rate) * 100).toFixed(1)}%`;
}

function metricMeanStd(stats) {
  if (!stats) return "—";
  return `${Number(stats.mean).toFixed(3)} ± ${Number(stats.std).toFixed(3)}`;
}

async function fetchTrust() {
  state.trustBusy = true;
  state.trustNotice = null;
  if (state.page === "trust") render();
  try {
    const response = await fetch("/api/trust");
    if (!response.ok) throw new Error("trust_failed");
    state.trust = await response.json();
  } catch (_error) {
    state.trust = null;
    state.trustNotice = { kind: "error", text: tr("trust_load_failed") };
  }
  state.trustBusy = false;
  if (state.page === "trust") render();
}

function renderTrust() {
  if (state.trustBusy && !state.trust) {
    return el("section", {}, [
      title("h1", "shield", tr("page_trust")),
      el("p", { class: "loading", text: tr("loading") })
    ]);
  }
  if (!state.trust) {
    return el("section", {}, [
      title("h1", "shield", tr("page_trust")),
      state.trustNotice
        ? el("p", { class: "banner-warn", text: state.trustNotice.text })
        : el("p", { class: "banner-info", text: tr("trust_empty") }),
      el("div", { class: "step-actions" }, [
        el("button", {
          type: "button",
          class: "primary",
          onclick: () => fetchTrust()
        }, [icon("back"), el("span", { text: tr("trust_refresh") })])
      ])
    ]);
  }

  const proxy = state.trust.kaggle_proxy || {};
  const spot = state.trust.in_sample_spotcheck || {};
  const reference = state.trust.reference_profiles || {};
  const refRows = reference.rows || [];

  const proxyTable = el("table", {}, [
    el("thead", {}, [el("tr", {}, [
      el("th", { text: tr("trust_metric") }),
      el("th", { text: tr("trust_value") })
    ])]),
    el("tbody", {}, [
      el("tr", {}, [el("td", { text: tr("trust_rows") }), el("td", { text: String(proxy.row_count ?? "—") })]),
      el("tr", {}, [el("td", { text: tr("trust_folds") }), el("td", { text: String(proxy.folds ?? "—") })]),
      el("tr", {}, [el("td", { text: "Accuracy" }), el("td", { text: metricMeanStd(proxy.accuracy) })]),
      el("tr", {}, [el("td", { text: "Macro F1" }), el("td", { text: metricMeanStd(proxy.f1_macro) })]),
      el("tr", {}, [el("td", { text: tr("trust_age_range") }), el("td", {
        text: Array.isArray(proxy.observed_age_range)
          ? `${proxy.observed_age_range[0]}–${proxy.observed_age_range[1]}`
          : "—"
      })]),
      el("tr", {}, [el("td", { text: tr("trust_class_counts") }), el("td", {
        text: proxy.class_counts
          ? Object.entries(proxy.class_counts).map(([k, v]) => `${named("class", k)} ${v}`).join(" · ")
          : "—"
      })])
    ])
  ]);

  const refTable = el("table", { class: "logs-table" }, [
    el("thead", {}, [el("tr", {}, [
      el("th", { text: tr("trust_col_id") }),
      el("th", { text: tr("trust_col_kind") }),
      el("th", { text: tr("trust_col_screen") }),
      el("th", { text: tr("trust_col_model") }),
      el("th", { text: tr("trust_col_match") })
    ])]),
    el("tbody", {}, refRows.length
      ? refRows.map((row) => {
        const screenText = row.expected_screen_class == null
          ? "—"
          : `${row.predicted_screen_class || "—"} / ${row.expected_screen_class}`;
        const modelText = row.expected_label == null
          ? "—"
          : `${row.predicted_label || "—"} / ${row.expected_label}`;
        const ok = (row.screen_match !== false) && (row.model_match !== false);
        const matchLabel = row.kind === "screen"
          ? (row.screen_match ? tr("trust_match_yes") : tr("trust_match_no"))
          : (ok ? tr("trust_match_yes") : tr("trust_match_no"));
        return el("tr", {}, [
          el("td", { class: "mono", text: row.id || "—" }),
          el("td", { text: row.kind || "—" }),
          el("td", { text: screenText }),
          el("td", { text: modelText }),
          el("td", { text: matchLabel })
        ]);
      })
      : [el("tr", {}, [el("td", { colspan: "5", text: tr("trust_no_profiles") })])])
  ]);

  return el("section", {}, [
    title("h1", "shield", tr("page_trust")),
    el("p", { class: "lede", text: tr("trust_lead") }),
    el("p", { class: "banner-info", text: state.trust.disclaimer || tr("trust_disclaimer") }),
    el("div", { class: "step-actions" }, [
      el("button", {
        type: "button",
        class: "secondary",
        disabled: state.trustBusy ? "disabled" : null,
        onclick: () => fetchTrust()
      }, [icon("back"), el("span", { text: tr("trust_refresh") })])
    ]),
    title("h2", "table", tr("trust_proxy_title")),
    el("p", { class: "note", text: proxy.note || tr("trust_proxy_note") }),
    el("div", { class: "card chart-scroll" }, [proxyTable]),
    proxy.caveat ? el("p", { class: "banner-warn", text: tr("trust_proxy_caveat") }) : null,
    title("h2", "bars", tr("trust_spot_title")),
    el("p", { class: "note", text: spot.note || tr("trust_spot_note") }),
    el("p", {
      text: tr("trust_spot_rate", {
        correct: spot.correct || 0,
        total: spot.total || 0,
        rate: pctRate(spot.rate)
      })
    }),
    title("h2", "clipboard", tr("trust_ref_title")),
    el("p", { class: "note", text: reference.disclaimer || tr("trust_ref_note") }),
    el("p", {
      text: tr("trust_ref_screen_rate", {
        correct: (reference.screen && reference.screen.correct) || 0,
        total: (reference.screen && reference.screen.total) || 0,
        rate: pctRate(reference.screen && reference.screen.rate)
      })
    }),
    el("p", {
      text: tr("trust_ref_model_rate", {
        correct: (reference.model && reference.model.correct) || 0,
        total: (reference.model && reference.model.total) || 0,
        rate: pctRate(reference.model && reference.model.rate)
      })
    }),
    el("div", { class: "card chart-scroll" }, [refTable]),
    title("h2", "shield", tr("trust_standards_title")),
    el("p", { class: "note", text: tr("trust_standards_lead") }),
    el("ul", { class: "card actions" }, [
      el("li", { text: tr("trust_standards_rule") }),
      el("li", { text: tr("trust_standards_isi") }),
      el("li", { text: tr("trust_standards_missing") })
    ]),
    renderDoctorGate(state.trust.doctor_gate),
    el("p", { class: "note", text: tr("trust_cli_hint") })
  ]);
}

function renderDoctorGate(gate) {
  if (!gate) {
    return el("section", {}, [
      title("h2", "alert", tr("trust_doctor_title")),
      el("p", { class: "note", text: tr("trust_doctor_missing") })
    ]);
  }
  const metricLine = (key, stats) => el("p", {
    text: tr("trust_doctor_metric", {
      name: tr(key),
      agree: stats && stats.agree != null ? stats.agree : 0,
      total: stats && stats.total != null ? stats.total : 0,
      rate: pctRate(stats && stats.rate != null ? stats.rate : stats && stats.agreement_rate),
      precision: pctRate(stats && stats.precision),
      recall: pctRate(stats && stats.recall)
    })
  });
  const questRows = gate.questionnaire_rows || [];
  const questTable = el("table", { class: "logs-table" }, [
    el("thead", {}, [el("tr", {}, [
      el("th", { text: tr("trust_col_id") }),
      el("th", { text: tr("trust_doctor_col_gt") }),
      el("th", { text: tr("trust_doctor_col_screen") }),
      el("th", { text: tr("trust_doctor_col_clinical") }),
      el("th", { text: tr("trust_col_match") })
    ])]),
    el("tbody", {}, questRows.length
      ? questRows.map((row) => {
        const screenOk = row.agree_screen !== false;
        const clinicalOk = row.agree_clinical == null ? null : row.agree_clinical !== false;
        const match = clinicalOk == null
          ? (screenOk ? tr("trust_match_yes") : tr("trust_match_no"))
          : ((screenOk && clinicalOk) ? tr("trust_match_yes") : tr("trust_match_no"));
        return el("tr", {}, [
          el("td", { class: "mono", text: row.id || "—" }),
          el("td", { text: row.gt_see_doctor ? tr("trust_doctor_yes") : tr("trust_doctor_no") }),
          el("td", {
            text: row.system_screen_flag == null
              ? "—"
              : (row.system_screen_flag ? tr("trust_doctor_yes") : tr("trust_doctor_no"))
          }),
          el("td", {
            text: row.system_see_doctor == null
              ? "—"
              : (row.system_see_doctor ? tr("trust_doctor_yes") : tr("trust_doctor_no"))
          }),
          el("td", { text: match })
        ]);
      })
      : [el("tr", {}, [el("td", { colspan: "5", text: tr("trust_no_profiles") })])])
  ]);
  return el("section", {}, [
    title("h2", "alert", tr("trust_doctor_title")),
    el("p", { class: "lede", text: tr("trust_doctor_lead") }),
    el("p", { class: "note", text: gate.note || tr("trust_doctor_note") }),
    metricLine("trust_doctor_a", gate.kaggle_vs_model_disorder),
    metricLine("trust_doctor_b", gate.kaggle_vs_clinical_gate),
    metricLine("trust_doctor_c", gate.questionnaire_screen_vs_gt),
    metricLine("trust_doctor_d", gate.questionnaire_full_vs_gt),
    el("p", {
      class: "note",
      text: tr("trust_doctor_mismatch", {
        count: gate.kaggle_mismatch_count || 0
      })
    }),
    title("h3", "clipboard", tr("trust_doctor_quest_title")),
    el("div", { class: "card chart-scroll" }, [questTable]),
    el("p", { class: "note", text: tr("trust_doctor_cli", { cmd: gate.cli_hint || "python scripts/check_doctor_gate.py" }) })
  ]);
}

function renderLogs() {
  const rows = (state.logs && state.logs.rows) || [];
  const total = state.logs ? state.logs.total : 0;
  const people = (state.logsPeople && state.logsPeople.people) || [];
  const personSelect = el("select", {
    id: "logs-person",
    onchange: (event) => selectLogPerson(event.target.value)
  }, [
    el("option", { value: "", text: tr("logs_person_all") }),
    ...people.map((person) => el("option", {
      value: person.anon_id,
      selected: state.logsPerson === person.anon_id ? "selected" : null,
      text: tr("logs_person_option", {
        anon: shortAnon(person.anon_id),
        runs: person.runs
      })
    }))
  ]);
  if (!state.logsPerson) personSelect.value = "";

  const actions = el("div", { class: "step-actions" }, [
    el("label", { class: "field", style: "flex:1;margin:0" }, [
      el("span", { class: "field-label", text: tr("logs_person_label") }),
      personSelect
    ]),
    el("button", {
      type: "button",
      class: "secondary",
      disabled: state.logsBusy ? "disabled" : null,
      onclick: () => fetchLogs()
    }, [icon("back"), el("span", { text: tr("logs_refresh") })]),
    el("a", {
      class: "button primary",
      href: "/api/logs/export.csv",
      download: "assessment_logs.csv"
    }, [icon("table"), el("span", { text: tr("logs_export") })])
  ]);

  const table = el("table", { class: "logs-table" }, [
    el("thead", {}, [
      el("tr", {}, [
        el("th", { text: tr("logs_col_id") }),
        el("th", { text: tr("logs_col_time") }),
        el("th", { text: tr("logs_col_screen") }),
        el("th", { text: tr("logs_col_model") }),
        el("th", { text: tr("logs_gt_rule") }),
        el("th", { text: tr("logs_gt_proxy") }),
        el("th", { text: tr("logs_col_risk") }),
        el("th", { text: tr("logs_match_rule_model") }),
        el("th", { text: tr("logs_agreement") }),
        el("th", { text: tr("logs_col_actions") })
      ])
    ])
  ]);
  const body = el("tbody");
  if (!rows.length) {
    body.append(el("tr", {}, [
      el("td", { colspan: "10", text: state.logsBusy ? tr("loading") : tr("logs_empty") })
    ]));
  } else {
    rows.forEach((row) => {
      body.append(el("tr", {
        class: state.logsDetail && state.logsDetail.id === row.id ? "logs-row-active" : ""
      }, [
        el("td", { text: String(row.id) }),
        el("td", { text: formatLogTime(row.created_at) }),
        el("td", { text: classCodeLabel(row.screen_class || "None", row.screen_class_code) }),
        el("td", { text: classCodeLabel(row.model_label || "None", row.model_label_code) }),
        el("td", { text: classCodeLabel(row.gt_rule_class || "None", row.gt_rule_class_code) }),
        el("td", {
          text: row.gt_proxy_class
            ? classCodeLabel(row.gt_proxy_class, row.gt_proxy_class_code)
            : tr("logs_gt_proxy_na")
        }),
        el("td", {
          text: row.risk_level
            ? `${numOrDash(row.risk_code)} · ${row.risk_level}`
            : "—"
        }),
        el("td", { text: matchNumLabel(row.match_rule_vs_model_num) }),
        el("td", { text: numOrDash(row.agreement_score) }),
        el("td", {}, [
          el("button", {
            type: "button",
            class: "secondary compact",
            disabled: state.logsBusy ? "disabled" : null,
            onclick: () => fetchLogDetail(row.id)
          }, [el("span", { text: tr("logs_view") })])
        ])
      ]));
    });
  }
  table.append(body);

  return el("section", {}, [
    title("h1", "rows", tr("page_logs")),
    el("p", { class: "lede", text: tr("logs_lead") }),
    el("p", { class: "note", text: tr("logs_privacy") }),
    el("p", { class: "note", text: tr("logs_gt_explain") }),
    actions,
    state.logsNotice
      ? el("p", { class: "banner-warn", text: state.logsNotice.text })
      : null,
    el("p", {
      class: "note",
      text: tr("logs_count_person", {
        shown: rows.length,
        total,
        person: state.logsPerson ? shortAnon(state.logsPerson) : tr("logs_person_all")
      })
    }),
    el("div", { class: "card chart-scroll" }, [table]),
    renderPersonLogDetail(state.logsDetail)
  ]);
}

function renderEda() {
  const header = [
    title("h1", "bars", tr("page_eda")),
    el("p", { class: "lede", text: tr("eda_intro") })
  ];
  if (!state.eda) return el("section", {}, header.concat([el("p", { class: "loading", text: tr("loading") })]));
  const data = state.eda;
  const source = data.metrics.source_kind === "synthetic" ? tr("synthetic") : data.metrics.source_name;
  const blocks = [
    el("p", { class: "note", text: tr("training_rows", { count: data.training_rows, source }) })
  ];
  if (data.status === "need_filter") blocks.push(el("p", { class: "banner-warn", text: tr("need_filter") }));
  else if (data.status === "empty") blocks.push(el("p", { class: "banner-info", text: tr("no_rows") }));
  else {
    blocks.push(el("p", { class: "note", text: tr("chart_rows", { count: data.filtered_rows }) }));
    blocks.push(el("div", { class: "metrics" }, [
      metric("rows", tr("filtered_rows"), String(data.filtered_rows)),
      ...CLASS_ORDER.map((label) => metric(CLASS_ICONS[label], named("class", label), String(data.class_counts[label] || 0)))
    ]));
    blocks.push(title("h2", "grid", tr("heatmap")));
    blocks.push(el("p", { class: "note", text: tr("heatmap_story") }));
    blocks.push(data.heatmap ? heatmapBlock(data.heatmap) : el("p", { class: "banner-info", text: tr("heatmap_need3") }));
    blocks.push(title("h2", "dots", tr("scatter")));
    blocks.push(el("p", { class: "note", text: tr("scatter_story") }));
    blocks.push(scatterBlock(data.scatter));
    blocks.push(title("h2", "bars", tr("prevalence")));
    blocks.push(el("p", { class: "note", text: tr("prevalence_story") }));
    blocks.push(prevalenceBlock(data.prevalence));
  }
  blocks.push(cvBlock(data.metrics));
  return el("section", {}, header.concat(blocks));
}

function heatmapBlock(heatmap) {
  const table = el("table", { class: "heat" });
  const head = el("tr", {}, [el("th", { text: "" })]);
  heatmap.columns.forEach((column) => head.append(el("th", { text: named("feature", column) })));
  table.append(el("thead", {}, [head]));
  const body = el("tbody");
  heatmap.columns.forEach((rowName, rowIndex) => {
    const row = el("tr", {}, [el("th", { text: named("feature", rowName) })]);
    heatmap.matrix[rowIndex].forEach((value) => {
      const cell = el("td", { text: value == null ? "" : Number(value).toFixed(2) });
      if (value != null) {
        cell.style.background = heatColor(value);
        cell.style.color = Math.abs(value) > 0.62 ? "#FFFFFF" : "#0F172A";
      }
      row.append(cell);
    });
    body.append(row);
  });
  table.append(body);
  return el("div", {}, [
    el("div", { class: "card chart-scroll" }, [table]),
    el("p", { class: "note", text: `${pearsonNote(heatmap.pearson)} ${tr("heat_meaning")} ${tr("disorder_code")}` })
  ]);
}

function heatColor(value) {
  const amount = Math.max(0, Math.min(1, Math.abs(value)));
  const start = [248, 250, 252];
  const end = value < 0 ? [185, 28, 28] : [30, 58, 138];
  const mixed = start.map((channel, index) => Math.round(channel + (end[index] - channel) * amount));
  return `rgb(${mixed.join(",")})`;
}

function pearsonNote(value) {
  if (value == null || Number.isNaN(Number(value))) return tr("pearson_na");
  const shown = Number(value).toFixed(2);
  if (Math.abs(value) < 0.1) return tr("pearson_weak", { value: shown });
  if (value < 0) return tr("pearson_neg", { value: shown });
  return tr("pearson_pos", { value: shown });
}

function scatterBlock(scatter) {
  const svg = scatterSvg(scatter.points);
  const parts = CLASS_ORDER.filter((label) => scatter.medians[label]).map((label) => tr("scatter_item", {
    label: named("class", label),
    hours: Number(scatter.medians[label].hours).toFixed(1),
    stress: Math.round(scatter.medians[label].stress)
  }));
  let caption = tr("scatter_median", { parts: parts.join("; ") });
  if (scatter.overlap) caption += tr("scatter_overlap", { count: scatter.overlap });
  return el("div", {}, [
    el("div", { class: "card chart-scroll" }, [svg]),
    classLegend(),
    el("p", { class: "note", text: caption })
  ]);
}

function classLegend() {
  return el("div", { class: "legend" }, CLASS_ORDER.map((label) => {
    const swatch = el("span", { class: "swatch" });
    swatch.style.background = COLORS[label];
    return el("span", { class: `legend-${TONES[label]}` }, [swatch, named("class", label)]);
  }));
}

function scatterSvg(points) {
  const ns = "http://www.w3.org/2000/svg";
  const width = 720;
  const height = 380;
  const pad = { left: 54, right: 16, top: 16, bottom: 42 };
  const sleeps = points.map((point) => point.sleep);
  const stresses = points.map((point) => point.stress);
  const xMin = Math.min(...sleeps) - 0.2;
  const xMax = Math.max(...sleeps) + 0.2;
  const yMin = Math.min(...stresses) - 0.4;
  const yMax = Math.max(...stresses) + 0.4;
  const xScale = (value) => pad.left + ((value - xMin) / (xMax - xMin)) * (width - pad.left - pad.right);
  const yScale = (value) => height - pad.bottom - ((value - yMin) / (yMax - yMin)) * (height - pad.top - pad.bottom);
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("width", "100%");
  svg.setAttribute("role", "img");
  const axis = document.createElementNS(ns, "path");
  axis.setAttribute("d", `M ${pad.left} ${pad.top} V ${height - pad.bottom} H ${width - pad.right}`);
  axis.setAttribute("fill", "none");
  axis.setAttribute("stroke", "#94A3B8");
  svg.append(axis);
  points.forEach((point) => {
    const dot = document.createElementNS(ns, "circle");
    dot.setAttribute("cx", xScale(point.sleep));
    dot.setAttribute("cy", yScale(point.stress));
    dot.setAttribute("r", "6");
    dot.setAttribute("fill", COLORS[point.label] || "#2563EB");
    dot.setAttribute("fill-opacity", "0.55");
    dot.setAttribute("tabindex", "0");
    const title = document.createElementNS(ns, "title");
    title.textContent = `${named("class", point.label)}, ${point.sleep} h, ${tr("stress")} ${point.stress}`;
    dot.append(title);
    svg.append(dot);
  });
  const xLabel = document.createElementNS(ns, "text");
  xLabel.setAttribute("x", width / 2);
  xLabel.setAttribute("y", height - 8);
  xLabel.setAttribute("text-anchor", "middle");
  xLabel.setAttribute("fill", "#0F172A");
  xLabel.textContent = tr("hours_axis");
  svg.append(xLabel);
  const yLabel = document.createElementNS(ns, "text");
  yLabel.setAttribute("x", 16);
  yLabel.setAttribute("y", 20);
  yLabel.setAttribute("fill", "#0F172A");
  yLabel.textContent = tr("stress");
  svg.append(yLabel);
  return svg;
}

function prevalenceBlock(prevalence) {
  const note = prevalence.note;
  let caption = tr("prev_empty");
  if (note.kind === "zero") caption = tr("prev_zero");
  if (note.kind === "stable" || note.kind === "any") {
    caption = tr(note.kind === "stable" ? "prev_stable" : "prev_any", {
      job: named("job", note.job),
      percent: note.percent,
      count: note.count,
      total: note.total
    });
  }
  return el("div", {}, [
    el("div", { class: "card chart-scroll" }, [prevalenceSvg(prevalence.groups)]),
    classLegend(),
    el("p", { class: "note", text: caption })
  ]);
}

function prevalenceSvg(groups) {
  const ns = "http://www.w3.org/2000/svg";
  const occupations = [...new Set(groups.map((row) => row.occupation))];
  const groupWidth = 92;
  const width = Math.max(640, occupations.length * groupWidth + 70);
  const height = 340;
  const pad = { left: 48, right: 12, top: 12, bottom: 110 };
  const plotHeight = height - pad.top - pad.bottom;
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("width", String(width));
  svg.setAttribute("role", "img");
  occupations.forEach((occupation, index) => {
    const origin = pad.left + index * groupWidth;
    CLASS_ORDER.forEach((label, series) => {
      const row = groups.find((item) => item.occupation === occupation && item.label === label);
      const percent = row ? row.percent : 0;
      const barHeight = (percent / 100) * plotHeight;
      const rect = document.createElementNS(ns, "rect");
      rect.setAttribute("x", origin + series * 24);
      rect.setAttribute("y", pad.top + plotHeight - barHeight);
      rect.setAttribute("width", "20");
      rect.setAttribute("height", Math.max(barHeight, 0));
      rect.setAttribute("fill", COLORS[label]);
      const title = document.createElementNS(ns, "title");
      title.textContent = `${named("job", occupation)} ${named("class", label)} ${percent.toFixed(1)}%`;
      rect.append(title);
      svg.append(rect);
    });
    const text = document.createElementNS(ns, "text");
    text.setAttribute("x", origin + 28);
    text.setAttribute("y", height - pad.bottom + 18);
    text.setAttribute("transform", `rotate(40 ${origin + 28} ${height - pad.bottom + 18})`);
    text.setAttribute("fill", "#0F172A");
    text.setAttribute("font-size", "13");
    text.textContent = named("job", occupation);
    svg.append(text);
  });
  return svg;
}

function cvBlock(metrics) {
  const scores = [
    ["accuracy", "check", tr("accuracy")],
    ["precision_macro", "star", tr("precision")],
    ["recall_macro", "shield", tr("recall")],
    ["f1_macro", "pulse", tr("f1")]
  ];
  const table = el("table");
  table.append(el("thead", {}, [el("tr", {}, [
    el("th", { text: tr("class_header") }),
    el("th", { text: tr("precision") }),
    el("th", { text: tr("recall") }),
    el("th", { text: tr("f1") })
  ])]));
  const body = el("tbody");
  CLASS_ORDER.forEach((label) => {
    const row = metrics.per_class[label];
    body.append(el("tr", {}, [
      el("td", { text: named("class", label) }),
      el("td", { text: meanStd(row.precision) }),
      el("td", { text: meanStd(row.recall) }),
      el("td", { text: meanStd(row.f1) })
    ]));
  });
  table.append(body);
  const counts = CLASS_ORDER.map((label) => `${named("class", label)} ${metrics.class_counts[label] || 0}`).join(", ");
  return el("section", {}, [
    title("h2", "check", tr("cv")),
    el("p", { class: "note", text: tr("cv_caption", { folds: metrics.folds, count: metrics.row_count }) }),
    el("div", { class: "metrics" }, scores.map(([key, iconName, label]) => metric(iconName, label, meanStd(metrics[key])))),
    el("div", { class: "card chart-scroll" }, [table]),
    el("p", { class: "note", text: tr("counts_line", {
      counts,
      duplicates: metrics.duplicate_feature_rows,
      relabeled: metrics.bmi_relabeled
    }) }),
    metrics.caveat ? el("p", { class: "banner-warn", text: tr("caveat") }) : null
  ]);
}

function meanStd(stats) {
  return `${Number(stats.mean).toFixed(3)} ± ${Number(stats.std).toFixed(3)}`;
}

async function fetchEda() {
  if (!state.filters) return;
  const token = ++edaToken;
  try {
    const response = await fetch("/api/eda", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state.filters)
    });
    const body = await response.json();
    if (token !== edaToken) return;
    state.eda = body;
  } catch (_error) {
    if (token !== edaToken) return;
    state.eda = null;
  }
  if (state.page === "eda") {
    const main = document.querySelector(".main");
    if (main) main.replaceWith(renderMain());
  }
}

function paintFailure() {
  document.getElementById("app").replaceChildren(el("p", { class: "banner-warn loading", text: tr("load_failed") }));
}

window.addEventListener("hashchange", () => {
  const page = location.hash.replace("#", "");
  if (!PAGES.includes(page) || page === state.page) return;
  showPage(page);
});

async function boot() {
  restoreSession();
  const hashed = location.hash.replace("#", "");
  state.page = PAGES.includes(hashed) ? hashed : "home";
  if (state.page === "assess" && !canAccessDeepAssess()) {
    state.page = "screen";
    state.notice = { kind: "warn", text: tr("assess_locked") };
  }
  document.getElementById("app").replaceChildren(el("p", { class: "loading", text: tr("loading") }));
  try {
    const response = await fetch("/api/meta");
    if (!response.ok) throw new Error("meta");
    state.meta = await response.json();
  } catch (_error) {
    paintFailure();
    return;
  }
  state.filters = {
    genders: state.meta.filter_genders.slice(),
    occupations: state.meta.filter_occupations.slice(),
    age_min: state.meta.age_min,
    age_max: state.meta.age_max
  };
  render();
  fetchEda();
}

boot();
