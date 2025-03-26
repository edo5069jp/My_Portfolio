let currentState = null; // 現在の状態を保持

chrome.storage.sync.get(["disabledDomains", "isEnabled"], (data) => {
  const disabledDomains = data.disabledDomains || [];
  const currentDomain = window.location.hostname;
  let isEnabled = data.isEnabled ?? true;

  // 修正: shouldDisable の判定を修正
  const shouldDisable = disabledDomains.includes(currentDomain) ? true : !isEnabled;
  currentState = shouldDisable;

  if (shouldDisable) {
    disablePostSubmission();
  } else {
    enablePostSubmission();
  }
});

chrome.runtime.onMessage.addListener((message) => {
  console.log("受信したメッセージ:", message);

  if (disabledDomains.includes(currentDomain)) {
    console.log("対象サイトなのでON/OFF不可:", currentDomain);
    return;
  }

  // 修正: currentState を明示的に確認
  if (message.isEnabled && currentState !== false) {
    enablePostSubmission();
    currentState = false;
  } else if (!message.isEnabled && currentState !== true) {
    disablePostSubmission();
    currentState = true;
  }
});

function disablePostSubmission() {
  console.log("【適用】POST送信ボタンを無効化");

  document.addEventListener("click", preventClick, true);
  document.addEventListener("submit", preventSubmit, true);
}

function enablePostSubmission() {
  console.log("【解除】POST送信ボタンを有効化");

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

function isPostButton(element) {
  if (element.tagName === "INPUT" && element.type === "submit") return true;
  if (element.tagName === "BUTTON" && element.type === "submit") return true;

  let form = element.closest("form");
  if (form && form.method.toLowerCase() === "post") {
    if (element.tagName === "BUTTON" && element.type !== "button") return true;
  }

  return false;
}
