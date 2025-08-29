const MENU_ID = "toggle-post-disable";
const STORAGE_KEY = "enabled";

async function setIcon(enabled) {
  const path = enabled ? "icon_enabled.png" : "icon_disabled.png";
  await chrome.action.setIcon({
    path: { 16: path, 32: path, 48: path, 128: path }
  });
}

async function getEnabled() {
  const { [STORAGE_KEY]: v } = await chrome.storage.local.get(STORAGE_KEY);
  return Boolean(v);
}

async function setEnabled(value) {
  await chrome.storage.local.set({ [STORAGE_KEY]: Boolean(value) });
  await setIcon(Boolean(value));
}

chrome.runtime.onInstalled.addListener(async () => {
  // 初期値: OFF
  const current = await getEnabled();
  if (current === false) {
    await setEnabled(false);
  } else {
    await setIcon(current);
  }

  chrome.contextMenus.create({
    id: MENU_ID,
    title: "ポスト送信無効on/off",
    contexts: ["action"]
  });
});

chrome.runtime.onStartup.addListener(async () => {
  await setIcon(await getEnabled());
});

chrome.contextMenus.onClicked.addListener(async (info) => {
  if (info.menuItemId !== MENU_ID) return;
  const now = await getEnabled();
  await setEnabled(!now);
});
