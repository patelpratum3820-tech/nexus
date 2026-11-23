import { contextBridge, ipcRenderer } from 'electron';

export interface NexusIPCBridge {
  system: {
    getHealth: () => Promise<any>;
    getMetrics: () => Promise<any>;
    exitApp: () => void;
    minimizeApp: () => void;
    toggleCompanion: () => void;
  };
  companion: {
    onStateChange: (callback: (state: any) => void) => void;
    sendAction: (action: string, payload?: any) => void;
  };
}

contextBridge.exposeInMainWorld('nexusAPI', {
  system: {
    getHealth: () => ipcRenderer.invoke('system:health'),
    getMetrics: () => ipcRenderer.invoke('system:metrics'),
    exitApp: () => ipcRenderer.send('app:exit'),
    minimizeApp: () => ipcRenderer.send('app:minimize'),
    toggleCompanion: () => ipcRenderer.send('companion:toggle'),
  },
  companion: {
    onStateChange: (callback: (state: any) => void) => {
      ipcRenderer.on('companion:state-update', (_event, state) => callback(state));
    },
    sendAction: (action: string, payload?: any) => {
      ipcRenderer.send('companion:action', { action, payload });
    }
  }
});
