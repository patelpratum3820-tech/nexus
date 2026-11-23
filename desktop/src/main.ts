import { app, BrowserWindow, ipcMain, screen } from 'electron';
import path from 'path';
import { ProcessManager } from './processManager';

let mainWindow: BrowserWindow | null = null;
let companionWindow: BrowserWindow | null = null;
const processMgr = new ProcessManager();

const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;
const ROOT_DIR = path.resolve(__dirname, '..', '..');

async function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 960,
    minHeight: 640,
    backgroundColor: '#0B0C10',
    frame: true,
    titleBarStyle: 'default',
    title: 'NEXUS — Local-First Personal AI OS',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
    show: false,
  });

  if (isDev) {
    await mainWindow.loadURL('http://localhost:5173');
  } else {
    await mainWindow.loadFile(path.join(ROOT_DIR, 'frontend', 'dist', 'index.html'));
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow?.show();
  });

  mainWindow.on('close', (event) => {
    // If companion is disabled or full exit requested, quit app
    if (!companionWindow || companionWindow.isDestroyed()) {
      app.quit();
    } else {
      // Allow minimizing to companion if companion enabled
      // but ensure user can choose full exit
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function createCompanionWindow() {
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width } = primaryDisplay.workAreaSize;

  companionWindow = new BrowserWindow({
    width: 260,
    height: 60,
    x: Math.round((width - 260) / 2),
    y: 20,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    resizable: false,
    skipTaskbar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    show: false,
  });

  const companionUrl = isDev
    ? 'http://localhost:5173/#companion'
    : `file://${path.join(ROOT_DIR, 'frontend', 'dist', 'index.html')}#companion`;

  companionWindow.loadURL(companionUrl);

  companionWindow.once('ready-to-show', () => {
    companionWindow?.show();
  });

  companionWindow.on('closed', () => {
    companionWindow = null;
  });
}

// IPC Handlers
ipcMain.handle('system:health', async () => {
  try {
    const res = await fetch('http://127.0.0.1:8765/api/system/health');
    return await res.json();
  } catch (err: any) {
    return { status: 'offline', error: err.message };
  }
});

ipcMain.handle('system:metrics', async () => {
  try {
    const res = await fetch('http://127.0.0.1:8765/api/resources/metrics');
    return await res.json();
  } catch (err: any) {
    return { status: 'offline', error: err.message };
  }
});

ipcMain.on('app:exit', async () => {
  console.log('[Main] Explicit app exit requested by user.');
  await processMgr.stopAll();
  app.quit();
});

ipcMain.on('app:minimize', () => {
  mainWindow?.minimize();
});

ipcMain.on('companion:toggle', () => {
  if (mainWindow) {
    if (mainWindow.isMinimized()) {
      mainWindow.restore();
    }
    mainWindow.show();
    mainWindow.focus();
  }
});

ipcMain.on('companion:action', (_event, { action, payload }) => {
  // Broadcast companion events to main window
  mainWindow?.webContents.send('companion:event', { action, payload });
});

// App Lifecycle
app.whenReady().then(async () => {
  console.log('[Main] NEXUS Desktop Shell starting...');
  // 1. Supervise backend process
  await processMgr.startBackend(ROOT_DIR);
  // 2. Create windows
  await createMainWindow();
  createCompanionWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

// Clean exit handlers
app.on('before-quit', async () => {
  await processMgr.stopAll();
});

app.on('window-all-closed', async () => {
  await processMgr.stopAll();
  app.quit();
});

process.on('SIGINT', async () => {
  await processMgr.stopAll();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  await processMgr.stopAll();
  process.exit(0);
});
