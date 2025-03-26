chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.sync.set({
    disabledDomains: ["example.com"], // 常時無効化
    isEnabled: true // 初期状態は有効
  });
});

chrome.action.onClicked.addListener((tab) => {
  chrome.storage.sync.get(["isEnabled"], (data) => {
    const newState = !data.isEnabled;

    chrome.storage.sync.set({ isEnabled: newState }, () => {
      console.log("拡張機能の状態:", newState ? "有効" : "無効");

      const iconPath = newState ? "icons/on.png" : "icons/off.png";
      chrome.action.setIcon({ path: iconPath });

      // `content.js` に状態変更を通知
      chrome.tabs.sendMessage(tab.id, { isEnabled: newState }, (response) => {
        if (chrome.runtime.lastError) {
          console.warn("content.js にメッセージを送れませんでした。");
        }
      });
    });
  });
});
