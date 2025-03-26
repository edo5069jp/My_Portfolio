chrome.storage.sync.get(["disabledDomains", "isEnabled"], (data) => {
  const disabledDomains = data.disabledDomains || [];
  const currentDomain = window.location.hostname;
  let isEnabled = data.isEnabled ?? true;

  const shouldDisable = disabledDomains.includes(currentDomain) || isEnabled;

  if (shouldDisable) {
    disablePostSubmission();
  }

  // `background.js` からのメッセージを受け取る（オンオフの切り替え）
  chrome.runtime.onMessage.addListener((message) => {
    if (disabledDomains.includes(currentDomain)) {
      return; // 常時無効化サイトは変更不可
    }

    if (message.isEnabled) {
      disablePostSubmission();
    } else {
      enablePostSubmission();
    }
  });
});

function disablePostSubmission() {
  document.addEventListener("click", preventClick, true);
  document.addEventListener("submit", preventSubmit, true);
  console.log("POST送信を無効化");
}

function enablePostSubmission() {
  document.removeEventListener("click", preventClick, true);
  document.removeEventListener("submit", preventSubmit, true);
  console.log("POST送信を有効化");
}

function preventClick(event) {
  let target = event.target.closest("a, button, input[type='submit']");
  if (target) {
    event.preventDefault();
    console.log("クリック無効化");
  }
}

function preventSubmit(event) {
  event.preventDefault();
  console.log("フォーム送信を無効化");
}
