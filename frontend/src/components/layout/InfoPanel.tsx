import React from 'react';
import {
  Activity,
  Cpu,
  Layers,
  Sparkles,
  ShieldCheck,
  ChevronRight,
  HardDrive,
  Workflow
} from 'lucide-react';
import { Project, ResourceMetrics } from '../../types';

interface InfoPanelProps {
  isOpen: boolean;
  onToggle: () => void;
  activeProject: Project | null;
  metrics: ResourceMetrics;
  activeTask: string | null;
}

export const InfoPanel: React.FC<InfoPanelProps> = ({
  isOpen,
  onToggle,
  activeProject,
  metrics,
  activeTask
}) => {
  if (!isOpen) {
    return (
      <button
        onClick={onToggle}
        className="fixed right-0 top-1/2 -translate-y-1/2 bg-obsidian-200 border-l border-y border-surface-border text-nexus-muted hover:text-lavender px-1 py-4 rounded-l-md transition-colors"
        title="Open Info Panel"
      >
        <Activity className="w-4 h-4" />
      </button>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'critical': return 'text-red-400 bg-red-400/10 border-red-500/20';
      case 'constrained': return 'text-amber-400 bg-amber-400/10 border-amber-500/20';
      default: return 'text-emerald-400 bg-emerald-400/10 border-emerald-500/20';
    }
  };

  return (
    <aside className="w-72 h-full border-l border-surface-border bg-obsidian-200/95 flex flex-col justify-between overflow-y-auto p-4 select-none transition-all duration-300">
      <div className="space-y-5">
        {/* Panel Header */}
        <div className="flex items-center justify-between pb-3 border-b border-surface-border">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-nexus-muted">
            <Layers className="w-3.5 h-3.5 text-lavender" />
            <span>Workspace Context</span>
          </div>
          <button
            onClick={onToggle}
            className="p-1 text-nexus-muted hover:text-nexus-text hover:bg-white/5 rounded"
            title="Collapse Panel"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* Real-time Resource Usage */}
        <div className="bg-surface-elevated/70 border border-surface-border rounded-xl p-3.5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-nexus-text flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-lavender" /> System Resources
            </span>
            <span className={`text-[10px] px-2 py-0.5 rounded-full border ${getStatusColor(metrics.status)} capitalize`}>
              {metrics.status}
            </span>
          </div>

          {/* CPU Bar */}
          <div className="space-y-1">
            <div className="flex justify-between text-[11px] text-nexus-muted">
              <span>CPU Usage</span>
              <span className="font-mono text-nexus-text">{metrics.cpu_percent}%</span>
            </div>
            <div className="w-full h-1.5 bg-obsidian-400 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-300 ${
                  metrics.cpu_percent > 80 ? 'bg-red-400' : 'bg-lavender'
                }`}
                style={{ width: `${Math.min(100, metrics.cpu_percent)}%` }}
              />
            </div>
          </div>

          {/* RAM Bar */}
          <div className="space-y-1">
            <div className="flex justify-between text-[11px] text-nexus-muted">
              <span>RAM Used</span>
              <span className="font-mono text-nexus-text">{metrics.ram_used_gb} / {metrics.ram_total_gb} GB</span>
            </div>
            <div className="w-full h-1.5 bg-obsidian-400 rounded-full overflow-hidden">
              <div
                className="h-full bg-violet-400 transition-all duration-300"
                style={{ width: `${metrics.ram_load_percent}%` }}
              />
            </div>
          </div>
        </div>

        {/* Current Project Info */}
        <div className="bg-surface-elevated/70 border border-surface-border rounded-xl p-3.5 space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-medium text-nexus-text">
            <HardDrive className="w-3.5 h-3.5 text-lavender" /> Active Project
          </div>
          {activeProject ? (
            <div className="space-y-1.5">
              <p className="text-xs font-semibold text-nexus-text">{activeProject.name}</p>
              <p className="text-[11px] text-nexus-muted line-clamp-2">{activeProject.description || 'No description'}</p>
              <div className="flex items-center gap-2 pt-1">
                <span className="text-[10px] px-2 py-0.5 rounded bg-lavender/10 text-lavender border border-lavender/20 uppercase">
                  {activeProject.status}
                </span>
              </div>
            </div>
          ) : (
            <p className="text-[11px] text-nexus-dim">No active project selected</p>
          )}
        </div>

        {/* Active Task Status */}
        <div className="bg-surface-elevated/70 border border-surface-border rounded-xl p-3.5 space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-medium text-nexus-text">
            <Workflow className="w-3.5 h-3.5 text-lavender" /> Task Execution
          </div>
          {activeTask ? (
            <div className="flex items-center gap-2 text-xs text-lavender">
              <div className="w-2 h-2 rounded-full bg-lavender animate-ping" />
              <span>{activeTask}</span>
            </div>
          ) : (
            <p className="text-[11px] text-nexus-dim">No tasks currently running</p>
          )}
        </div>

        {/* Model Status (Phase 1 Simulation with Confirmed Roles) */}
        <div className="bg-surface-elevated/70 border border-surface-border rounded-xl p-3.5 space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-medium text-nexus-text">
            <Sparkles className="w-3.5 h-3.5 text-lavender" /> AI Architecture (Phase 1)
          </div>
          <div className="space-y-1">
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-nexus-muted">Engine:</span>
              <span className="text-nexus-text font-mono">Phase 1 Mock</span>
            </div>
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-nexus-muted">Default Chat:</span>
              <span className="text-emerald-400 font-medium">Gemma 3:1B</span>
            </div>
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-nexus-muted">Coding:</span>
              <span className="text-lavender font-medium">Qwen 2.5 Coder 1.5B</span>
            </div>
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-nexus-muted">Reasoning:</span>
              <span className="text-amber-400 font-medium">Phi-4-mini (Restricted)</span>
            </div>
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-nexus-muted">Embeddings:</span>
              <span className="text-nexus-text">Nomic Embed (On-Demand)</span>
            </div>
            <div className="flex items-center justify-between text-[11px] pt-1 border-t border-white/5">
              <span className="text-nexus-muted">Concurrency:</span>
              <span className="text-emerald-400 font-medium">Single Model Residence</span>
            </div>
          </div>
        </div>
      </div>

      {/* Safety & Sandbox Guarantee Footer */}
      <div className="pt-3 border-t border-surface-border/60">
        <div className="flex items-center gap-2 text-[10px] text-nexus-muted/80">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>Antigravity Priority Guard Active (&gt;2.0 GB Headroom)</span>
        </div>
      </div>
    </aside>
  );
};
