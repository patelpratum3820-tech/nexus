import React, { useState, useEffect } from 'react';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import { InfoPanel } from './components/layout/InfoPanel';
import { ConversationWorkspace } from './components/chat/ConversationWorkspace';
import { ProjectDiscovery } from './components/discovery/ProjectDiscovery';
import { ProjectList } from './components/projects/ProjectList';
import { MemoryManager } from './components/memory/MemoryManager';
import { SettingsView } from './components/settings/SettingsView';
import { DynamicIsland } from './components/companion/DynamicIsland';
import { NavigationTab, Project, ResourceMetrics } from './types';
import { api } from './services/api';

export const App: React.FC = () => {
  // Check if loaded inside standalone companion window
  const isCompanionMode = window.location.hash === '#companion';

  const [activeTab, setActiveTab] = useState<NavigationTab>('chat');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isInfoPanelOpen, setIsInfoPanelOpen] = useState(true);
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [activeTask, setActiveTask] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<ResourceMetrics>({
    cpu_percent: 12.0,
    ram_used_gb: 5.6,
    ram_total_gb: 15.7,
    ram_available_gb: 10.1,
    ram_load_percent: 36,
    status: 'normal',
    active_tasks_count: 0,
    can_start_heavy_task: true,
    timestamp: Date.now() / 1000
  });

  // Low-frequency resource sampling (every 5 seconds)
  useEffect(() => {
    let isMounted = true;
    const fetchMetrics = async () => {
      try {
        const m = await api.resources.getMetrics();
        if (isMounted) setMetrics(m);
      } catch (_) {}
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleExit = async () => {
    // If running in Electron shell
    if ((window as any).nexusAPI) {
      (window as any).nexusAPI.system.exitApp();
    } else {
      await api.system.shutdown();
      window.close();
    }
  };

  const handleMinimize = () => {
    if ((window as any).nexusAPI) {
      (window as any).nexusAPI.system.minimizeApp();
    }
  };

  // If in standalone companion window
  if (isCompanionMode) {
    return (
      <div className="w-full h-screen flex items-center justify-center p-1 bg-transparent">
        <DynamicIsland
          onOpenMain={() => {
            if ((window as any).nexusAPI) {
              (window as any).nexusAPI.system.toggleCompanion();
            }
          }}
          cpuPercent={metrics.cpu_percent}
          activeTask={activeTask}
        />
      </div>
    );
  }

  return (
    <div className="w-screen h-screen flex flex-col bg-obsidian text-nexus-text overflow-hidden select-none">
      {/* Top Application Header */}
      <Header
        onMinimize={handleMinimize}
        onExit={handleExit}
        onOpenCompanion={() => {}}
        isCompanionVisible={true}
        cpuPercent={metrics.cpu_percent}
        activeTask={activeTask}
      />

      {/* Main 3-Part Desktop Workspace */}
      <div className="flex-1 flex overflow-hidden">
        {/* A. Left Sidebar */}
        <Sidebar
          activeTab={activeTab}
          onSelectTab={setActiveTab}
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={() => setIsSidebarCollapsed(prev => !prev)}
          onNewChat={() => setActiveTab('chat')}
        />

        {/* B. Central Workspace */}
        <main className="flex-1 h-full overflow-hidden bg-obsidian-300/40 relative">
          {activeTab === 'chat' && (
            <ConversationWorkspace
              onStartDiscovery={() => setActiveTab('discovery')}
              onOpenProjects={() => setActiveTab('projects')}
              activeProject={activeProject}
            />
          )}

          {activeTab === 'discovery' && (
            <ProjectDiscovery />
          )}

          {activeTab === 'projects' && (
            <ProjectList
              onSelectProject={(p) => {
                setActiveProject(p);
                setActiveTab('chat');
              }}
              onStartDiscovery={() => setActiveTab('discovery')}
            />
          )}

          {activeTab === 'memory' && (
            <MemoryManager />
          )}

          {activeTab === 'settings' && (
            <SettingsView
              metrics={metrics}
              onExitApp={handleExit}
            />
          )}

          {(activeTab === 'tasks' || activeTab === 'files') && (
            <div className="h-full flex items-center justify-center text-center p-6">
              <div className="space-y-2">
                <h3 className="text-sm font-semibold text-nexus-text capitalize">{activeTab} Workspace</h3>
                <p className="text-xs text-nexus-muted max-w-sm">
                  This modular workspace is prepared in the architectural foundation and scheduled for Phase 3/4.
                </p>
              </div>
            </div>
          )}
        </main>

        {/* C. Right Info Panel */}
        <InfoPanel
          isOpen={isInfoPanelOpen}
          onToggle={() => setIsInfoPanelOpen(prev => !prev)}
          activeProject={activeProject}
          metrics={metrics}
          activeTask={activeTask}
        />
      </div>
    </div>
  );
};
