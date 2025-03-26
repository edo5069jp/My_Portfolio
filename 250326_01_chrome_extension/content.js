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
      return; // 常時無効化ドメインは変更不可
    }

    if (message.isEnabled) {
      disablePostSubmission();
    } else {
      enablePostSubmission();
    }
  });
});

function disablePostSubmission() {
  console.log("POST送信ボタンを無効化");
  document.addEventListener("click", preventClick, true);
  document.addEventListener("submit", preventSubmit, true);
}

function enablePostSubmission() {
  console.log("POST送信ボタンを有効化（元に戻す）");
  document.removeEventListener("click", preventClick, true);
  document.removeEventListener("submit", preventSubmit, true);
}

function preventClick(event) {
  let target = event.target;
  if (isPostButton(target)) {
    event.preventDefault();
    console.log("POST送信を無効化", target);
  }
}

function preventSubmit(event) {
  event.preventDefault();
  console.log("フォーム送信を無効化");
}

// POST送信をするボタンかどうかを判別
function isPostButton(element) {
  if (element.tagName === "INPUT" && element.type === "submit") return true;
  if (element.tagName === "BUTTON" && element.type === "submit") return true;

  let form = element.closest("form");
  if (form && form.method.toLowerCase() === "post") {
    if (element.tagName === "BUTTON" && element.type !== "button") return true;
  }

  return false;
}
