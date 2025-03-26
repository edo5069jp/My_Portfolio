chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.sync.set({
    disabledDomains: ["example.com"], // ここは常時無効化するドメイン
    isEnabled: true // デフォルトは有効
  });
});

chrome.action.onClicked.addListener((tab) => {
  chrome.storage.sync.get(["isEnabled", "disabledDomains"], (data) => {
    const disabledDomains = data.disabledDomains || [];
    const currentDomain = new URL(tab.url).hostname;
    const isTargetSite = disabledDomains.includes(currentDomain);
    
    if (isTargetSite) {
      console.log("対象サイトなのでON/OFF不可:", currentDomain);
      return; // 対象サイトは変更不可
    }

    const newState = !data.isEnabled;

    chrome.storage.sync.set({ isEnabled: newState }, () => {
      console.log("拡張機能の状態:", newState ? "有効" : "無効");

      const iconPath = newState ? "icons/on.png" : "icons/off.png";
      chrome.action.setIcon({ path: iconPath });

      // `content.js` に状態変更を通知
      chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: updateContentScript,
        args: [newState]
      });
    });
  });
});

function updateContentScript(isEnabled) {
  chrome.runtime.sendMessage({ isEnabled });
}
