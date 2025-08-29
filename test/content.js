// 対象のPOST送信先（ベースURL比較：クエリや#は無視）
const TARGETS = [
  "https://acs.dev2.devcabu.jp/chukai/m102/kojin",
  "https://acs.kabu.co.jp/chukai/m102/kojin"
];

const STORAGE_KEY = "enabled";
let ENABLED = false;

function baseOf(u) {
  try {
    const x = new URL(u, location.href);
    return (x.origin + x.pathname).replace(/\/+$/,"");
  } catch { return ""; }
}
const TARGET_BASES = TARGETS.map(baseOf);

function isTargetActionURL(u) {
  const b = baseOf(u);
  return TARGET_BASES.includes(b);
}

function isTargetForm(form) {
  if (!form) return false;
  const method = (form.getAttribute("method") || form.method || "get").toLowerCase();
  if (method !== "post") return false;
  const actionRaw = form.getAttribute("action") || form.action || "";
  return isTargetActionURL(actionRaw);
}

function cancel(e) {
  e.preventDefault();
  e.stopImmediatePropagation();
  e.stopPropagation();
}

function findInteractiveInPath(path) {
  for (const el of path) {
    if (!el || !el.matches) continue;
    if (el.matches("a, button, input[type='submit'], input[type='button'], input[type='image']")) {
      return el;
    }
  }
  return null;
}

function findFormFromPath(path, fallbackTarget) {
  for (const el of path) {
    if (el && el.tagName === "FORM") return el;
    if (el && el.closest) {
      const f = el.closest("form");
      if (f) return f;
    }
  }
  return fallbackTarget?.closest?.("form") || null;
}

function shouldBlockFromEvent(e) {
  if (!ENABLED) return false;
  const path = typeof e.composedPath === "function" ? e.composedPath() : [];
  const node = findInteractiveInPath(path) || e.target?.closest?.("a, button, input[type='submit'], input[type='button'], input[type='image']");
  const form = findFormFromPath(path, node);
  return !!(form && isTargetForm(form));
}

// ——— Listeners（キャプチャ）———
const clickHandler = (e) => { if (shouldBlockFromEvent(e)) cancel(e); };
const submitHandler = (e) => { if (ENABLED && isTargetForm(e.target)) cancel(e); };

["pointerdown","mousedown","mouseup","touchstart","click","auxclick"].forEach(type => {
  document.addEventListener(type, clickHandler, true);
});
document.addEventListener("submit", submitHandler, true);

// ——— プログラム的 submit() の直呼び対策 ———
const _submit = HTMLFormElement.prototype.submit;
HTMLFormElement.prototype.submit = function(...args) {
  if (ENABLED && isTargetForm(this)) return; // 無音キャンセル
  return _submit.apply(this, args);
};

if (HTMLFormElement.prototype.requestSubmit) {
  const _requestSubmit = HTMLFormElement.prototype.requestSubmit;
  HTMLFormElement.prototype.requestSubmit = function(...args) {
    if (ENABLED && isTargetForm(this)) return;
    return _requestSubmit.apply(this, args);
  };
}

// ——— ON/OFF反映 ———
(async function init() {
  const { [STORAGE_KEY]: v } = await chrome.storage.local.get(STORAGE_KEY);
  ENABLED = Boolean(v);
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area === "local" && STORAGE_KEY in changes) {
      ENABLED = Boolean(changes[STORAGE_KEY].newValue);
    }
  });
})();
