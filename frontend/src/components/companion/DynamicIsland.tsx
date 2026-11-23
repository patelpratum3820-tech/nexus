import React, { useState, useRef, useEffect } from 'react';
import { ExpressiveEyes } from './ExpressiveEyes';
import { Mic, Sparkles, Terminal, Activity, X, Maximize2, Cpu } from 'lucide-react';
import { CompanionEyeState } from '../../types';

interface DynamicIslandProps {
  onOpenMain?: () => void;
  activeTask?: string | null;
  cpuPercent?: number;
}

export const DynamicIsland: React.FC<DynamicIslandProps> = ({
  onOpenMain,
  activeTask = null,
  cpuPercent = 12
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [mousePos, setMousePos] = useState<{ x: number; y: number } | null>(null);
  const [eyeState, setEyeState] = useState<CompanionEyeState>('idle');
  const [voiceQuery, setVoiceQuery] = useState('');
  const clickTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Update eye states based on mode
  useEffect(() => {
    if (isListening) {
      setEyeState('listening');
    } else if (activeTask) {
      setEyeState('processing');
    } else {
      setEyeState('idle');
    }
  }, [isListening, activeTask]);

  const handleMouseMove = (e: React.MouseEvent) => {
    setMousePos({ x: e.clientX, y: e.clientY });
  };

  const handleClick = () => {
    // Distinguish single-click from double-click
    if (clickTimeoutRef.current) {
      clearTimeout(clickTimeoutRef.current);
      clickTimeoutRef.current = null;
      // Double click: Open Main Application
      if (onOpenMain) onOpenMain();
    } else {
      clickTimeoutRef.current = setTimeout(() => {
        // Single click: Toggle voice / quick action mode
        setIsListening(prev => !prev);
        setIsExpanded(true);
        clickTimeoutRef.current = null;
      }, 260);
    }
  };

  return (
    <div
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => {
        setIsHovered(false);
        setMousePos(null);
      }}
      className={`relative select-none transition-all duration-300 ease-out flex items-center justify-between rounded-full glass-pill backdrop-blur-2xl border border-surface-border hover:border-lavender/40 px-3 py-1.5 shadow-2xl cursor-pointer ${
        isExpanded ? 'w-80 h-28 rounded-2xl p-4' : isHovered ? 'w-64 h-11' : 'w-48 h-10'
      }`}
      onClick={handleClick}
    >
      {/* Dynamic island content when collapsed */}
      {!isExpanded && (
        <div className="flex items-center justify-between w-full h-full">
          <div className="flex items-center gap-2.5">
            <ExpressiveEyes state={eyeState} lookTarget={mousePos} size="sm" />
            <span className="text-xs font-medium tracking-wide text-nexus-text/90">
              {activeTask ? 'Processing...' : isHovered ? 'NEXUS Companion' : 'NEXUS'}
            </span>
          </div>

          <div className="flex items-center gap-2 text-nexus-muted">
            {isHovered && (
              <div className="flex items-center gap-1.5 text-[10px] text-lavender bg-lavender/10 px-2 py-0.5 rounded-full border border-lavender/20">
                <Cpu className="w-2.5 h-2.5" />
                <span>{cpuPercent}%</span>
              </div>
            )}
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsListening(prev => !prev);
                setIsExpanded(true);
              }}
              className="p-1 hover:text-lavender transition-colors rounded-full hover:bg-white/5"
              title="Activate Voice Assistant"
            >
              <Mic className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* Dynamic island content when expanded */}
      {isExpanded && (
        <div className="flex flex-col justify-between w-full h-full" onClick={(e) => e.stopPropagation()}>
          <div className="flex items-center justify-between border-b border-white/5 pb-2">
            <div className="flex items-center gap-2">
              <ExpressiveEyes state={eyeState} lookTarget={mousePos} size="sm" />
              <span className="text-xs font-semibold text-lavender">
                {isListening ? 'Listening for command...' : 'Desktop Assistant'}
              </span>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={() => {
                  if (onOpenMain) onOpenMain();
                  setIsExpanded(false);
                }}
                className="p-1 text-nexus-muted hover:text-nexus-text hover:bg-white/5 rounded"
                title="Open Main Workspace"
              >
                <Maximize2 className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => {
                  setIsExpanded(false);
                  setIsListening(false);
                }}
                className="p-1 text-nexus-muted hover:text-nexus-text hover:bg-white/5 rounded"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Voice query or active task */}
          <div className="py-1">
            {isListening ? (
              <div className="flex items-center gap-2 text-xs text-nexus-text">
                <div className="w-2 h-2 rounded-full bg-red-400 animate-ping" />
                <input
                  type="text"
                  placeholder="Speak or type a quick directive..."
                  value={voiceQuery}
                  onChange={(e) => setVoiceQuery(e.target.value)}
                  className="bg-transparent border-none text-xs text-nexus-text focus:outline-none w-full"
                  autoFocus
                />
              </div>
            ) : (
              <p className="text-[11px] text-nexus-muted">
                {activeTask ? `Active task: ${activeTask}` : 'Single click: Voice | Double click: Open Main Workspace'}
              </p>
            )}
          </div>

          <div className="flex items-center justify-between text-[10px] text-nexus-muted/80 pt-1">
            <span className="flex items-center gap-1">
              <Activity className="w-3 h-3 text-lavender" /> Local-first (Offline)
            </span>
            <span>CPU: {cpuPercent}%</span>
          </div>
        </div>
      )}
    </div>
  );
};
