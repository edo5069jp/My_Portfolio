const MENU_ID = "toggle-post-disable";
const STORAGE_KEY = "enabled";

// DNR ルールID
const RULES = [
  {
    id: 10001,
    priority: 1,
    action: { type: "block" },
    condition: {
      regexFilter: "^https:\\/\\/acs\\.dev2\\.devcabu\\.jp\\/chukai\\/m102\\/kojin\\/?(?:\\?.*)?$",
      resourceTypes: ["main_frame", "sub_frame", "xmlhttprequest", "ping", "other"],
      requestMethods: ["post"]
    }
  },
  {
    id: 10002,
    priority: 1,
    action: { type: "block" },
    condition: {
      regexFilter: "^https:\\/\\/acs\\.kabu\\.co\\.jp\\/chukai\\/m102\\/kojin\\/?(?:\\?.*)?$",
      resourceTypes: ["main_frame", "sub_frame", "xmlhttprequest", "ping", "other"],
      requestMethods: ["post"]
    }
  }
];

async function setIcon(enabled) {
  const path = enabled ? "icon_enabled.png" : "icon_disabled.png";
  await chrome.action.setIcon({ path: {16:path,32:path,48:path,128:path} });
}

async function getEnabled() {
  const { [STORAGE_KEY]: v } = await chrome.storage.local.get(STORAGE_KEY);
  return Boolean(v);
}

async function applyDnr(enabled) {
  if (enabled) {
    await chrome.declarativeNetRequest.updateDynamicRules({
      addRules: RULES,
      removeRuleIds: []
    });
  } else {
    await chrome.declarativeNetRequest.updateDynamicRules({
      addRules: [],
      removeRuleIds: RULES.map(r => r.id)
    });
  }
}

async function setEnabled(value) {
  const v = Boolean(value);
  await chrome.storage.local.set({ [STORAGE_KEY]: v });
  await setIcon(v);
  await applyDnr(v);
  // メニューのチェックを反映
  try {
    await chrome.contextMenus.update(MENU_ID, { checked: v });
  } catch {}
}

async function initContextMenu() {
  const enabled = await getEnabled();
  chrome.contextMenus.create({
    id: MENU_ID,
    title: "ポスト送信無効on/off",
    type: "checkbox",
    checked: enabled,
    contexts: ["action"]
  });
}

chrome.runtime.onInstalled.addListener(async () => {
  // 初期値: OFF（値未設定ならfalse）
  const enabled = await getEnabled();
  await setIcon(enabled);
  await applyDnr(enabled);
  await initContextMenu();
});

chrome.runtime.onStartup.addListener(async () => {
  const enabled = await getEnabled();
  await setIcon(enabled);
  await applyDnr(enabled);
});

chrome.contextMenus.onClicked.addListener(async (info) => {
  if (info.menuItemId !== MENU_ID) return;
  // checkbox の新状態が info.checked に来る
  await setEnabled(info.checked);
});
