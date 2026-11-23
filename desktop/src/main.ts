import { app, BrowserWindow, ipcMain, screen } from 'electron';
import path from 'path';
import { ProcessManager } from './processManager';

let mainWindow: BrowserWindow | null = null;
let companionWindow: BrowserWindow | null = null;
let isExplicitQuitting = false;
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
    // If explicit exit requested, allow window to close and destroy
    if (isExplicitQuitting) {
      return;
    }

    // If companion is active and enabled, hide to companion instead of destroying window
    if (companionWindow && !companionWindow.isDestroyed()) {
      event.preventDefault();
      mainWindow?.hide();
      console.log('[Main] Main window hidden to Dynamic Island companion.');
    } else {
      // If companion is unavailable, full exit
      isExplicitQuitting = true;
      app.quit();
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
  if (isExplicitQuitting) return;
  console.log('[Main] Explicit app exit requested by user.');
  isExplicitQuitting = true;
  await processMgr.stopAll();
  app.quit();
});

ipcMain.on('app:minimize', () => {
  mainWindow?.minimize();
});

ipcMain.on('companion:toggle', () => {
  if (mainWindow && !mainWindow.isDestroyed()) {
    if (mainWindow.isMinimized()) {
      mainWindow.restore();
    }
    if (!mainWindow.isVisible()) {
      mainWindow.show();
    }
    mainWindow.focus();
  } else {
    createMainWindow();
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
  isExplicitQuitting = true;
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
