const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
let mainWindow;
let fileNames = [];

function createWindow() {
  mainWindow = new BrowserWindow({
    autoHideMenuBar: true,
    width: 400,
    height: 400,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
  });

  mainWindow.loadFile('index.html');

    // renderer.jsからのメッセージを受け取る
  ipcMain.on('message-from-renderer', (event, data) => {
    // 受け取ったデータをmain.jsで使用
    const preventDefault = (e) => {
      e.preventDefault();
      e.stopPropagation();
    };

    const container = data.container;
    const list = data.list;
    container.addEventListener('dragover', (e) => {
      preventDefault(e);
    });

    container.addEventListener('drop', (e) => {
      preventDefault(e);

      for (const file of e.dataTransfer.files) {
        const child = document.createElement('li');

        child.textContent = file.path;
        list.appendChild(child);
      }
    });

    ipcMain.on('copyToClipboard', () => {
      const fileList = fileNames.join('\n');
      clipboard.writeText(fileList);
    });
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});