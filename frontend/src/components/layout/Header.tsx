import React, { useState } from 'react';
import { Minus, X, AlertTriangle, Sparkles, ExternalLink } from 'lucide-react';
import { DynamicIsland } from '../companion/DynamicIsland';

interface HeaderProps {
  onMinimize: () => void;
  onExit: () => void;
  onOpenCompanion: () => void;
  isCompanionVisible: boolean;
  cpuPercent?: number;
  activeTask?: string | null;
}

export const Header: React.FC<HeaderProps> = ({
  onMinimize,
  onExit,
  onOpenCompanion,
  isCompanionVisible,
  cpuPercent = 12,
  activeTask = null
}) => {
  const [showExitConfirm, setShowExitConfirm] = useState(false);

  return (
    <>
      <header className="h-14 border-b border-surface-border bg-obsidian-200/90 backdrop-blur-md flex items-center justify-between px-4 select-none shrink-0 z-30">
        {/* Left: Window Status / Breadcrumb */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-lavender animate-pulse" />
            <span className="text-xs font-semibold tracking-wide text-nexus-text">NEXUS WORKSPACE</span>
          </div>
          <span className="text-nexus-dim text-xs">/</span>
          <span className="text-[11px] text-nexus-muted">Local-First Operating System</span>
        </div>

        {/* Center: Dynamic Island Desktop Companion Widget */}
        <div className="flex items-center justify-center">
          <DynamicIsland
            onOpenMain={() => {}}
            cpuPercent={cpuPercent}
            activeTask={activeTask}
          />
        </div>

        {/* Right: Window Controls & Full Exit */}
        <div className="flex items-center gap-2">
          <button
            onClick={onMinimize}
            className="p-1.5 text-nexus-muted hover:text-nexus-text hover:bg-white/5 rounded-md transition-colors"
            title="Minimize NEXUS"
          >
            <Minus className="w-4 h-4" />
          </button>

          <button
            onClick={() => setShowExitConfirm(true)}
            className="p-1.5 text-nexus-muted hover:text-red-400 hover:bg-red-400/10 rounded-md transition-colors"
            title="Fully Exit NEXUS"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Explicit Clean Exit Confirmation Dialog */}
      {showExitConfirm && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-obsidian-100 border border-surface-border rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-3 text-amber-400">
              <AlertTriangle className="w-6 h-6" />
              <h2 className="text-sm font-semibold text-nexus-text">Fully Exit NEXUS?</h2>
            </div>
            <p className="text-xs text-nexus-muted leading-relaxed">
              Exiting will cleanly terminate the Python core backend, close SQLite connections,
              stop all active workers, and dismiss the Dynamic Island companion.
              No hidden processes or background services will remain running.
            </p>
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setShowExitConfirm(false)}
                className="px-4 py-2 rounded-lg text-xs font-medium text-nexus-muted hover:text-nexus-text hover:bg-white/5 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setShowExitConfirm(false);
                  onExit();
                }}
                className="px-4 py-2 rounded-lg text-xs font-medium bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/30 transition-colors"
              >
                Terminate & Exit
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
