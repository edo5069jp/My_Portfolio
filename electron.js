const { app, BrowserWindow } = require('electron');
const puppeteer = require('puppeteer');

let mainWindow;

async function getBacklogLine(url) {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto(url);

  // バックログの特定の行を取得するロジックを実装してください
  const specificLine = await page.evaluate(() => {
    const element = document.querySelector('h2 > a[href="#"]');
    return element.textContent.trim();
  });

  await browser.close();

  return specificLine;
}

function createWindow() {
  mainWindow = new BrowserWindow({ width: 800, height: 600 });

  mainWindow.webContents.on('did-finish-load', async () => {
    const url = 'http://backlog-url'; // バックログのURLに置き換えてください
    const specificLine = await getBacklogLine(url);

    const backlogLineElement = mainWindow.webContents.executeJavaScript(
      `document.getElementById('backlog-line').textContent = '${specificLine}';`
    );
  });

  mainWindow.loadFile('index.html');
}

app.whenReady().then(createWindow);
