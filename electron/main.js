const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn, execSync } = require('child_process');
const http = require('http');

let mainWindow;
let pythonProcess = null;

const BACKEND_PORT = 8000;
const HEALTH_URL = `http://127.0.0.1:${BACKEND_PORT}/api/v1/health`;

// Disable Chromium GPU and HTTP disk cache write warnings on Windows
app.commandLine.appendSwitch('disable-gpu-shader-disk-cache');
app.commandLine.appendSwitch('disable-http-cache');

function freePortIfOccupied(port) {
  try {
    if (process.platform === 'win32') {
      const out = execSync(`netstat -ano | findstr :${port}`, { encoding: 'utf8' });
      const lines = out.split('\n').filter(l => l.includes('LISTENING'));
      const activePyPid = pythonProcess && pythonProcess.pid ? String(pythonProcess.pid) : null;
      for (const line of lines) {
        const parts = line.trim().split(/\s+/);
        const pid = parts[parts.length - 1];
        if (pid && pid !== '0' && pid !== String(process.pid) && pid !== activePyPid) {
          console.log(`[Electron Main] Freeing port ${port} by terminating stale process PID ${pid}...`);
          try {
            execSync(`taskkill /F /PID ${pid}`);
          } catch (e) {}
        }
      }
    }
  } catch (err) {
    // Port is clear
  }
}

function startPythonBackend() {
  const venvPython = path.join(__dirname, '..', 'venv', 'Scripts', 'python.exe');
  const env = { ...process.env, PYTHONPATH: path.join(__dirname, '..', 'backend') };

  console.log('[Electron Main] Starting FastAPI Backend process...');
  pythonProcess = spawn(
    venvPython,
    ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', String(BACKEND_PORT)],
    { cwd: path.join(__dirname, '..', 'backend'), env }
  );

  pythonProcess.stdout.on('data', (data) => {
    console.log(`[Backend Log]: ${data.toString().trim()}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    const str = data.toString().trim();
    if (!str) return;
    if (str.includes('INFO:') || str.includes('WARNING:')) {
      console.log(`[Backend Log]: ${str}`);
    } else {
      console.error(`[Backend Err]: ${str}`);
    }
  });

  pythonProcess.on('close', (code) => {
    console.log(`[Electron Main] Python process exited with code ${code}`);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1100,
    height: 750,
    minWidth: 800,
    minHeight: 600,
    title: 'OSPilot - Desktop Assistant Foundation',
    backgroundColor: '#0f172a',
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  mainWindow.loadFile(path.join(__dirname, '..', 'frontend', 'index.html'));

  mainWindow.webContents.on('console-message', (event, level, message, line, sourceId) => {
    console.log(`[Renderer Log]: ${message} (line ${line})`);
  });

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });
}

// IPC Handler to check system health from frontend
ipcMain.handle('check-backend-health', () => {
  return new Promise((resolve) => {
    const req = http.get(HEALTH_URL, (res) => {
      let rawData = '';
      res.on('data', (chunk) => {
        rawData += chunk;
      });
      res.on('end', () => {
        try {
          const parsedData = JSON.parse(rawData);
          resolve({ success: true, data: parsedData });
        } catch (e) {
          resolve({ success: false, error: 'Failed to parse JSON response' });
        }
      });
    });

    req.on('error', (err) => {
      resolve({ success: false, error: err.message });
    });

    req.setTimeout(2500, () => {
      req.destroy();
      resolve({ success: false, error: 'Health check request timed out' });
    });
  });
});

// IPC Handlers for GUI Directory & File Selection Dialogs
ipcMain.handle('dialog:selectDirectory', async () => {
  if (!mainWindow) return null;
  const result = await dialog.showOpenDialog(mainWindow, {
    title: 'Select Folder to Index',
    properties: ['openDirectory', 'createDirectory']
  });
  if (result.canceled || !result.filePaths || result.filePaths.length === 0) {
    return null;
  }
  return result.filePaths[0];
});

ipcMain.handle('dialog:selectFile', async () => {
  if (!mainWindow) return null;
  const result = await dialog.showOpenDialog(mainWindow, {
    title: 'Select Document File',
    properties: ['openFile']
  });
  if (result.canceled || !result.filePaths || result.filePaths.length === 0) {
    return null;
  }
  return result.filePaths[0];
});

function checkBackendRunning() {
  return new Promise((resolve) => {
    const req = http.get(HEALTH_URL, (res) => {
      let rawData = '';
      res.on('data', (chunk) => { rawData += chunk; });
      res.on('end', () => {
        try {
          const parsedData = JSON.parse(rawData);
          resolve(parsedData && (parsedData.status === 'ok' || parsedData.status === 'online'));
        } catch (e) {
          resolve(false);
        }
      });
    });
    req.on('error', () => {
      resolve(false);
    });
    req.setTimeout(1500, () => {
      req.destroy();
      resolve(false);
    });
  });
}

function killPythonBackend() {
  if (pythonProcess) {
    console.log('[Electron Main] Terminating Python process tree...');
    try {
      pythonProcess.kill();
      if (process.platform === 'win32' && pythonProcess.pid) {
        execSync(`taskkill /F /T /PID ${pythonProcess.pid}`);
      }
    } catch (e) {}
    pythonProcess = null;
  }
}

app.whenReady().then(async () => {
  const isRunning = await checkBackendRunning();
  if (isRunning) {
    console.log('[Electron Main] FastAPI Backend is already running and responsive on port 8000.');
  } else {
    console.log('[Electron Main] Backend not responsive. Ensuring port 8000 is clean...');
    freePortIfOccupied(BACKEND_PORT);
    startPythonBackend();
  }
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  killPythonBackend();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('will-quit', () => {
  killPythonBackend();
});
