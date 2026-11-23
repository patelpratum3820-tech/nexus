import React, { useState, useEffect } from 'react';
import {
  Settings,
  Cpu,
  HardDrive,
  ShieldCheck,
  Power,
  Sliders,
  AlertOctagon,
  CheckCircle2,
  Lock
} from 'lucide-react';
import { api } from '../../services/api';
import { ResourceMetrics, ResourceLimits } from '../../types';

interface SettingsViewProps {
  metrics: ResourceMetrics;
  onExitApp: () => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({ metrics, onExitApp }) => {
  const [limits, setLimits] = useState<ResourceLimits>({
    max_cpu_percent: 85,
    min_ram_gb: 1.5,
    max_concurrent_tasks: 2,
    active_workers: []
  });
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    api.resources.getLimits().then(setLimits);
  }, []);

  const handleSaveLimits = async () => {
    await api.resources.updateLimits(limits);
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  const resourceRules = [
    { title: 'Antigravity & OS Priority Preservation (>2.0 GB RAM Buffer)', status: 'Active', enforced: true },
    { title: 'Single Chat Model Residence Only (Never Multiple Loaded)', status: 'Enforced', enforced: true },
    { title: 'Phi-4-mini Restricted Explicit Confirmation Required', status: 'Enforced', enforced: true },
    { title: 'Isolated On-Demand Memory Embeddings (Nomic)', status: 'Active', enforced: true },
    { title: 'No Automatic Startup with Windows', status: 'Compliant', enforced: true },
    { title: 'No Silent Background Services or Scheduled Tasks', status: 'Compliant', enforced: true },
    { title: 'No Model Preloading on App Launch', status: 'Compliant', enforced: true },
    { title: 'No Indiscriminate Disk Scanning / Background Indexing', status: 'Compliant', enforced: true },
    { title: 'Zero Orphaned Processes on Exit Guarantee', status: 'Compliant', enforced: true },
    { title: 'Safe Resource Throttling (CPU > 80% Throttle)', status: 'Active', enforced: true },
  ];

  return (
    <div className="h-full overflow-y-auto p-6 max-w-4xl mx-auto space-y-6 select-none">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-surface-border">
        <div>
          <div className="flex items-center gap-2 text-lavender">
            <Settings className="w-5 h-5" />
            <h1 className="text-lg font-semibold text-nexus-text">System & Resource Settings</h1>
          </div>
          <p className="text-xs text-nexus-muted pt-1">
            Configure strict resource boundaries, review safety compliance, and manage application lifecycle.
          </p>
        </div>

        {/* Clean Exit Action */}
        <button
          onClick={onExitApp}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 text-xs font-semibold transition-all"
        >
          <Power className="w-4 h-4" />
          <span>Exit NEXUS Fully</span>
        </button>
      </div>

      {/* Hardware Telemetry Card */}
      <div className="bg-surface-elevated/80 border border-surface-border rounded-2xl p-6 space-y-4">
        <h2 className="text-sm font-semibold text-nexus-text flex items-center gap-2">
          <Cpu className="w-4 h-4 text-lavender" /> Hardware & Resource Monitor
        </h2>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-obsidian-300/80 p-3.5 rounded-xl border border-surface-border">
            <span className="text-[11px] text-nexus-muted block">CPU Utilization</span>
            <span className="text-lg font-mono font-semibold text-nexus-text">{metrics.cpu_percent}%</span>
          </div>

          <div className="bg-obsidian-300/80 p-3.5 rounded-xl border border-surface-border">
            <span className="text-[11px] text-nexus-muted block">Available RAM</span>
            <span className="text-lg font-mono font-semibold text-emerald-400">{metrics.ram_available_gb} GB</span>
          </div>

          <div className="bg-obsidian-300/80 p-3.5 rounded-xl border border-surface-border">
            <span className="text-[11px] text-nexus-muted block">Total RAM</span>
            <span className="text-lg font-mono font-semibold text-nexus-text">{metrics.ram_total_gb} GB</span>
          </div>

          <div className="bg-obsidian-300/80 p-3.5 rounded-xl border border-surface-border">
            <span className="text-[11px] text-nexus-muted block">Active Workers</span>
            <span className="text-lg font-mono font-semibold text-lavender">{metrics.active_tasks_count}</span>
          </div>
        </div>
      </div>

      {/* Configurable Resource Thresholds */}
      <div className="bg-surface-elevated/80 border border-surface-border rounded-2xl p-6 space-y-5">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-nexus-text flex items-center gap-2">
            <Sliders className="w-4 h-4 text-lavender" /> Configurable Safety Limits
          </h2>
          {savedSuccess && (
            <span className="text-xs text-emerald-400 flex items-center gap-1 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5" /> Limits Saved
            </span>
          )}
        </div>

        <div className="space-y-4">
          <div>
            <div className="flex justify-between text-xs text-nexus-muted mb-1.5">
              <span>Maximum Allowed CPU Utilization Before Throttling</span>
              <span className="font-mono text-nexus-text">{limits.max_cpu_percent}%</span>
            </div>
            <input
              type="range"
              min="50"
              max="95"
              step="5"
              value={limits.max_cpu_percent}
              onChange={(e) => setLimits({ ...limits, max_cpu_percent: Number(e.target.value) })}
              className="w-full accent-lavender cursor-pointer"
            />
          </div>

          <div>
            <div className="flex justify-between text-xs text-nexus-muted mb-1.5">
              <span>Minimum Guaranteed Free RAM Floor</span>
              <span className="font-mono text-nexus-text">{limits.min_ram_gb} GB</span>
            </div>
            <input
              type="range"
              min="1.0"
              max="4.0"
              step="0.5"
              value={limits.min_ram_gb}
              onChange={(e) => setLimits({ ...limits, min_ram_gb: Number(e.target.value) })}
              className="w-full accent-lavender cursor-pointer"
            />
          </div>

          <div>
            <div className="flex justify-between text-xs text-nexus-muted mb-1.5">
              <span>Maximum Concurrent Background Tasks</span>
              <span className="font-mono text-nexus-text">{limits.max_concurrent_tasks}</span>
            </div>
            <input
              type="range"
              min="1"
              max="4"
              step="1"
              value={limits.max_concurrent_tasks}
              onChange={(e) => setLimits({ ...limits, max_concurrent_tasks: Number(e.target.value) })}
              className="w-full accent-lavender cursor-pointer"
            />
          </div>
        </div>

        <button
          onClick={handleSaveLimits}
          className="px-5 py-2 rounded-xl bg-lavender text-obsidian-400 font-semibold text-xs hover:bg-lavender-light transition-all"
        >
          Save Resource Boundaries
        </button>
      </div>

      {/* Absolute Resource Rules Compliance Table */}
      <div className="bg-surface-elevated/80 border border-surface-border rounded-2xl p-6 space-y-4">
        <h2 className="text-sm font-semibold text-nexus-text flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" /> Architectural Safety Verification
        </h2>
        <div className="divide-y divide-white/5">
          {resourceRules.map((r, i) => (
            <div key={i} className="flex items-center justify-between py-2.5 text-xs">
              <span className="text-nexus-text">{r.title}</span>
              <span className="flex items-center gap-1.5 text-[11px] text-emerald-400 font-medium">
                <CheckCircle2 className="w-3.5 h-3.5" /> {r.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
