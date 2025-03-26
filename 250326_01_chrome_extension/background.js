chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.sync.set({
    disabledDomains: ["example.com"], // ここは常時無効化するドメイン
    isEnabled: true // デフォルトは有効
  });
});

chrome.action.onClicked.addListener((tab) => {
  chrome.storage.sync.get(["isEnabled"], (data) => {
    const newState = !data.isEnabled;

    chrome.storage.sync.set({ isEnabled: newState }, () => {
      console.log("拡張機能の状態:", newState ? "有効" : "無効");

      // アイコン変更
      const iconPath = newState ? "icons/on.png" : "icons/off.png";
      chrome.action.setIcon({ path: iconPath });

      // `content.js` に変更通知を送る
      chrome.tabs.sendMessage(tab.id, { isEnabled: newState });
    });
  });
});
