import { spawn, ChildProcess, exec } from 'child_process';
import path from 'path';

export class ProcessManager {
  private backendProcess: ChildProcess | null = null;
  private backendPid: number | null = null;
  private isShuttingDown: boolean = false;

  public startBackend(baseDir: string): Promise<boolean> {
    return new Promise((resolve) => {
      const pythonExecutable = 'python';
      const args = ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8765'];

      console.log(`[ProcessManager] Spawning NEXUS Backend: ${pythonExecutable} ${args.join(' ')}`);

      this.backendProcess = spawn(pythonExecutable, args, {
        cwd: path.join(baseDir, 'backend'),
        env: { ...process.env, PYTHONUNBUFFERED: '1' },
        stdio: ['ignore', 'pipe', 'pipe']
      });

      if (this.backendProcess.pid) {
        this.backendPid = this.backendProcess.pid;
        console.log(`[ProcessManager] Backend running with PID: ${this.backendPid}`);
      }

      this.backendProcess.stdout?.on('data', (data) => {
        const msg = data.toString();
        // Check if server is ready
        if (msg.includes('Application startup complete') || msg.includes('Uvicorn running')) {
          resolve(true);
        }
      });

      this.backendProcess.stderr?.on('data', (data) => {
        const err = data.toString();
        if (err.includes('Application startup complete') || err.includes('Uvicorn running')) {
          resolve(true);
        }
      });

      this.backendProcess.on('exit', (code) => {
        console.log(`[ProcessManager] Backend process exited with code ${code}`);
        this.backendProcess = null;
        this.backendPid = null;
      });

      // Fallback timeout: resolve true after 2.5s if not failed
      setTimeout(() => resolve(true), 2500);
    });
  }

  public async stopAll(): Promise<void> {
    if (this.isShuttingDown) return;
    this.isShuttingDown = true;
    console.log('[ProcessManager] Cleaning up NEXUS processes...');

    // 1. Attempt graceful HTTP shutdown
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 800);
      await fetch('http://127.0.0.1:8765/api/system/shutdown', {
        method: 'POST',
        signal: controller.signal
      }).catch(() => {});
      clearTimeout(timeout);
    } catch (_) {
      // Ignore network errors during shutdown
    }

    // 2. Terminate child process tree on Windows if still running
    if (this.backendPid) {
      const pid = this.backendPid;
      this.backendPid = null;
      if (process.platform === 'win32') {
        exec(`taskkill /F /T /PID ${pid}`, (err) => {
          if (!err) console.log(`[ProcessManager] Force terminated process tree PID ${pid}`);
        });
      } else {
        try {
          process.kill(-pid, 'SIGKILL');
        } catch (_) {}
      }
    }
  }
}
