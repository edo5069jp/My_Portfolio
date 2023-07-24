// preload.js

const { contextBridge, ipcRenderer } = require('electron');

// IPC通信の関数をレンダラープロセスで使用可能にする
contextBridge.exposeInMainWorld('electron', {
  ipcRenderer: ipcRenderer
});
