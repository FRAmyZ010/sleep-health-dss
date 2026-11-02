const I18N = window.SLEEP_I18N;
const CLASS_ORDER = ["None", "Insomnia", "Sleep Apnea"];
const COLORS = { None: "#047857", Insomnia: "#C2410C", "Sleep Apnea": "#B91C1C" };
const TONES = { None: "low", Insomnia: "medium", "Sleep Apnea": "high" };
const PROFILE_FIELDS = [
  "Gender", "Age", "Occupation", "BMI Category", "Sleep Duration", "Quality of Sleep",
  "Physical Activity Level", "Stress Level", "Daily Steps", "Systolic_BP", "Diastolic_BP", "Heart Rate"
];
const SESSION_KEY = "sleep-health-web";

const state = {
  lang: "en",
  page: "home",
  meta: null,
  form: {
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
    systolic: "120",
    diastolic: "80",
    heart: "72"
  },
  result: null,
  notice: null,
  step: 0,
  busy: false,
  filters: null,
  eda: null
};

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
const PAGES = ["home", "assess", "result", "eda"];
const NAV_ICONS = { home: "home", assess: "clipboard", result: "list", eda: "bars" };
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
  Systolic_BP: "up",
  Diastolic_BP: "down",
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

function saveSession() {
  sessionStorage.setItem(SESSION_KEY, JSON.stringify({
    lang: state.lang,
    page: state.page,
    form: state.form,
    result: state.result,
    notice: state.notice,
    step: state.step
  }));
}

function restoreSession() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(SESSION_KEY) || "null");
    if (!saved || !I18N.TEXT[saved.lang]) return;
    state.lang = saved.lang;
    state.page = PAGES.includes(saved.page) ? saved.page : "home";
    state.form = Object.assign(state.form, saved.form || {});
    state.result = saved.result || null;
    state.notice = saved.notice || null;
    state.step = Number.isInteger(saved.step) ? saved.step : 0;
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
    Systolic_BP: ["มม.ปรอท", "mmHg"],
    Diastolic_BP: ["มม.ปรอท", "mmHg"],
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
  if (item.code === "bp_order" || item.code === "weight_range" || item.code === "height_range" || item.code === "server") {
    return tr(item.code === "server" ? "server_error" : item.code);
  }
  return item.message || tr("score_failed");
}

function showPage(page) {
  state.page = page;
  if (location.hash !== `#${page}`) location.hash = page;
  saveSession();
  render();
  if (page === "eda") fetchEda();
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
  const page = state.page === "home" ? renderHome() : state.page === "result" ? renderResult() : state.page === "eda" ? renderEda() : renderAssess();
  return el("main", { class: "main" }, [
    el("div", { class: "topbar" }, [el("span", { text: tr("language") }), language]),
    page
  ]);
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
      card("user", "home_step_you_title", "home_step_you"),
      card("moon", "home_step_sleep_title", "home_step_sleep"),
      card("heart", "home_step_heart_title", "home_step_heart"),
      card("check", "home_step_review_title", "home_step_review")
    ]),
    title("h2", "table", tr("home_data_title")),
    el("p", { class: "lede", text: tr("home_data") }),
    title("h2", "shield", tr("home_scope_title")),
    el("p", { class: "lede", text: tr("home_scope") }),
    el("div", { class: "grid-2 landing-actions" }, [
      el("button", {
        type: "button",
        class: "primary",
        onclick: () => showPage("assess")
      }, [icon("clipboard"), el("span", { text: tr("home_start") })]),
      el("button", {
        type: "button",
        class: "secondary",
        onclick: () => showPage("eda")
      }, [icon("bars"), el("span", { text: tr("home_explore") })])
    ])
  ]);
}

function field(iconName, label, control, help) {
  return el("label", { class: "field" }, [
    el("span", { class: "field-label" }, [icon(iconName), el("span", { text: label })]),
    control,
    help ? el("span", { class: "field-help", text: help }) : null
  ]);
}

function numberField(iconName, label, key, min, max, step, help) {
  const input = el("input", {
    type: "number", id: key, min, max, step, value: state.form[key], inputmode: "decimal"
  });
  input.addEventListener("input", () => {
    state.form[key] = input.value;
    if (key === "weight" || key === "height") updateBmi();
    refreshGuide();
    saveSession();
  });
  return field(iconName, label, input, help);
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
    bubble.textContent = input.value;
    refreshGuide();
    saveSession();
  });
  return field(iconName, label, el("div", { class: "slider-row" }, [input, bubble]), help);
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
  systolic: "Systolic_BP",
  diastolic: "Diastolic_BP",
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
    meter("systolic", tr("systolic"), limits.Systolic_BP),
    meter("diastolic", tr("diastolic"), limits.Diastolic_BP),
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

function resultStory(result) {
  const profile = result.profile;
  return tr("result_story", {
    age: profile.Age,
    gender: named("gender", profile.Gender),
    job: named("job", profile.Occupation),
    bmi: result.body.bmi_display,
    category: named("bmi", result.body.category),
    sleep: Number(profile["Sleep Duration"]).toFixed(1),
    quality: profile["Quality of Sleep"],
    stress: profile["Stress Level"],
    sys: profile.Systolic_BP,
    dia: profile.Diastolic_BP,
    hr: profile["Heart Rate"],
    label: named("class", result.label),
    risk: named("risk", result.risk_level)
  });
}

function renderAssess() {
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
        selectField("briefcase", tr("occupation"), "occupation", state.meta.occupations, "job", tr("occupation_help")),
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
      el("div", { class: "card grid-2" }, [
        numberField("moon", tr("sleep_duration"), "sleep", limits["Sleep Duration"][0], limits["Sleep Duration"][1], "0.1"),
        sliderField("star", tr("quality"), "quality", limits["Quality of Sleep"][0], limits["Quality of Sleep"][1], tr("quality_help")),
        numberField("pulse", tr("activity"), "activity", limits["Physical Activity Level"][0], limits["Physical Activity Level"][1], "1"),
        sliderField("bolt", tr("stress"), "stress", limits["Stress Level"][0], limits["Stress Level"][1], tr("stress_help")),
        numberField("steps", tr("steps"), "steps", limits["Daily Steps"][0], limits["Daily Steps"][1], "100")
      ])
    ]);
  } else if (step === 2) {
    body = el("div", {}, [
      title("h2", "heart", tr("cardio")),
      el("div", { class: "card grid-3" }, [
        numberField("up", tr("systolic"), "systolic", limits.Systolic_BP[0], limits.Systolic_BP[1], "1", tr("bp_help")),
        numberField("down", tr("diastolic"), "diastolic", limits.Diastolic_BP[0], limits.Diastolic_BP[1], "1"),
        numberField("heart", tr("heart_rate"), "heart", limits["Heart Rate"][0], limits["Heart Rate"][1], "1")
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
  const rows = [
    [tr("gender"), named("gender", state.form.gender)],
    [tr("age"), state.form.age],
    [tr("occupation"), named("job", state.form.occupation)],
    [tr("weight"), `${Number(state.form.weight).toFixed(1)} ${tr("kg")}`],
    [tr("height"), `${Number(state.form.height).toFixed(1)} ${tr("cm")}`],
    [tr("bmi_short"), reading ? `${reading.display} · ${named("bmi", reading.category)}` : "—"],
    [tr("sleep_duration"), pretty("Sleep Duration", state.form.sleep)],
    [tr("quality"), pretty("Quality of Sleep", state.form.quality)],
    [tr("activity"), pretty("Physical Activity Level", state.form.activity)],
    [tr("stress"), pretty("Stress Level", state.form.stress)],
    [tr("steps"), pretty("Daily Steps", state.form.steps)],
    [tr("systolic"), pretty("Systolic_BP", state.form.systolic)],
    [tr("diastolic"), pretty("Diastolic_BP", state.form.diastolic)],
    [tr("heart_rate"), pretty("Heart Rate", state.form.heart)]
  ];
  return el("div", { class: "card review" }, rows.map(([label, value]) => el("div", { class: "review-row" }, [
    el("span", { text: label }),
    el("strong", { text: value })
  ])));
}

function noticeNode() {
  if (!state.notice) return null;
  const notice = state.notice;
  let title = notice.title || "";
  if (notice.code === "saved") {
    title = tr("saved", {
      bmi: notice.bmi,
      category: named("bmi", notice.category),
      label: named("class", notice.label),
      risk: named("risk", notice.risk)
    });
  } else if (notice.code === "failed") title = tr("score_failed");
  else if (notice.code === "offline") title = tr("load_failed");
  const lines = notice.code === "failed" && notice.client
    ? stepErrors(state.step).concat(state.result ? [tr("kept_result")] : [])
    : (notice.lines || []);
  const tone = notice.code === "saved" && notice.risk ? `banner-tone banner-${notice.risk.toLowerCase()}` : "";
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
    ["Systolic_BP", "systolic", "Diastolic_BP", "diastolic", "Heart Rate", "heart"]
      .reduce((pairs, item, index, list) => {
        if (index % 2 === 0) pairs.push([item, list[index + 1]]);
        return pairs;
      }, [])
      .forEach(([feature, key]) => pushRange(errors, feature, key));
    if (Number.isFinite(Number(state.form.systolic)) && Number.isFinite(Number(state.form.diastolic)) && Number(state.form.systolic) <= Number(state.form.diastolic)) {
      errors.push(tr("bp_order"));
    }
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
    Systolic_BP: Number(state.form.systolic),
    Diastolic_BP: Number(state.form.diastolic),
    "Heart Rate": Number(state.form.heart)
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
      state.result = body;
      state.notice = {
        kind: "ok",
        code: "saved",
        bmi: body.body.bmi_display,
        category: body.body.category,
        label: body.label,
        risk: body.risk_level
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
  const advice = I18N.ADVICE[state.lang][result.label];
  const body = result.body;
  const maxImportance = Math.max(...result.importances.map((item) => item.importance), 0.01);
  return el("section", {}, [
    title("h1", "list", tr("page_result")),
    el("p", { class: "lede", text: tr("result_caption") }),
    el("div", { class: "card story-card" }, [
      title("h2", "decision", tr("visit_title")),
      el("p", { class: "story", text: resultStory(result) }),
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
    el("div", { class: `risk risk-${result.risk_level.toLowerCase()}` }, [
      icon(CLASS_ICONS[result.label] || RISK_ICONS[result.risk_level]),
      el("div", {}, [
        el("p", { class: "risk-kicker", text: tr("risk_word", { level: named("risk", result.risk_level) }) }),
        el("p", { class: "risk-title", text: named("class", result.label) })
      ])
    ]),
    title("h2", "bars", tr("probabilities")),
    el("div", { class: "card bars" }, CLASS_ORDER.map((label) => barRow(
      named("class", label),
      result.probabilities[label],
      `${(result.probabilities[label] * 100).toFixed(1)}%`,
      COLORS[label],
      CLASS_ICONS[label],
      true
    ))),
    title("h2", "pulse", tr("importance")),
    el("p", { class: "note", text: tr("importance_caption") }),
    el("div", { class: "card bars" }, result.importances.map((item) => barRow(
      named("feature", item.feature),
      item.importance / maxImportance,
      `${(item.importance * 100).toFixed(1)}%`,
      "#2563EB",
      FEATURE_ICONS[item.feature]
    ))),
    title("h2", "compare", tr("comparison")),
    el("p", { class: "note", text: tr("comparison_caption") }),
    result.factors && result.factors.length
      ? el("ul", { class: "card actions" }, result.factors.map((factor) => el("li", { text: factorText(factor) })))
      : el("p", { class: "banner-info", text: tr("no_factors") }),
    reduceRisk(result, advice),
    result.support_notes && result.support_notes.length
      ? el("div", {}, [
        title("h2", "alert", tr("outside")),
        el("div", { class: "stack" }, result.support_notes.map((note) => el("p", { class: "banner-warn", text: noteText(note) })))
      ])
      : null,
    title("h2", "table", tr("submitted")),
    profileTable(result.profile)
  ]);
}

function reduceRisk(result, advice) {
  const tone = TONES[result.label] || "low";
  return el("section", { class: `card reduce-risk tone-${tone}` }, [
    title("h2", RISK_ICONS[result.risk_level] || "shield", tr("reduce_title")),
    el("p", { class: "lede", text: tr("reduce_lead", {
      label: named("class", result.label),
      risk: named("risk", result.risk_level)
    }) }),
    el("p", { text: advice.decision }),
    el("ol", { class: "actions" }, advice.actions.map((action) => el("li", { text: action })))
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
