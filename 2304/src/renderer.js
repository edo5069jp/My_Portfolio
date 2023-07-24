const { ipcRenderer } = window.electron;


const container = document.getElementById('container');
const list = document.getElementById('list');

// 送信するデータ
const data = {
  containerText: container,
  listText: list,
};

// main.jsに値を送信
ipcRenderer.send('message-from-renderer', data);