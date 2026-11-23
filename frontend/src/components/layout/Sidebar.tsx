import React from 'react';
import {
  MessageSquare,
  FolderGit2,
  HelpCircle,
  Database,
  CheckSquare,
  Files,
  Settings,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Plus
} from 'lucide-react';
import { NavigationTab } from '../../types';

interface SidebarProps {
  activeTab: NavigationTab;
  onSelectTab: (tab: NavigationTab) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  onNewChat: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  isCollapsed,
  onToggleCollapse,
  onNewChat
}) => {
  const navItems: { id: NavigationTab; label: string; icon: React.FC<{ className?: string }> }[] = [
    { id: 'chat', label: 'Conversation', icon: MessageSquare },
    { id: 'discovery', label: 'Project Discovery', icon: Sparkles },
    { id: 'projects', label: 'Projects', icon: FolderGit2 },
    { id: 'tasks', label: 'Tasks & Workflows', icon: CheckSquare },
    { id: 'memory', label: 'Memory Store', icon: Database },
    { id: 'files', label: 'Files & Folders', icon: Files },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside
      className={`h-full flex flex-col justify-between border-r border-surface-border bg-obsidian-200 transition-all duration-300 ease-in-out select-none ${
        isCollapsed ? 'w-16' : 'w-60'
      }`}
    >
      {/* Top Branding & New Chat */}
      <div>
        {/* Brand Header */}
        <div className="flex items-center justify-between px-4 py-4 border-b border-surface-border/60">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-lavender/15 border border-lavender/30 flex items-center justify-center text-lavender font-bold text-sm shadow-[0_0_12px_rgba(157,140,255,0.2)]">
              N
            </div>
            {!isCollapsed && (
              <div>
                <h1 className="font-semibold text-sm tracking-wider text-nexus-text">NEXUS</h1>
                <p className="text-[10px] text-nexus-muted tracking-tight">Personal AI OS</p>
              </div>
            )}
          </div>
          <button
            onClick={onToggleCollapse}
            className="p-1 text-nexus-muted hover:text-nexus-text hover:bg-white/5 rounded-md transition-colors"
            title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          >
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* New Session Action */}
        <div className="p-3">
          <button
            onClick={onNewChat}
            className={`w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg border border-lavender/30 bg-lavender/10 hover:bg-lavender/20 text-lavender font-medium text-xs transition-all duration-150 shadow-sm hover:shadow-[0_0_15px_rgba(157,140,255,0.15)] ${
              isCollapsed ? 'px-0' : ''
            }`}
            title="New Conversation"
          >
            <Plus className="w-4 h-4" />
            {!isCollapsed && <span>New Conversation</span>}
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="px-2 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-lavender/15 text-lavender border border-lavender/25 shadow-sm'
                    : 'text-nexus-muted hover:text-nexus-text hover:bg-white/5'
                }`}
                title={isCollapsed ? item.label : undefined}
              >
                <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-lavender' : ''}`} />
                {!isCollapsed && <span className="truncate">{item.label}</span>}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom Status / Local-First badge */}
      <div className="p-3 border-t border-surface-border/60">
        {!isCollapsed ? (
          <div className="flex items-center justify-between text-[11px] text-nexus-muted px-2 py-1 bg-obsidian-300/80 rounded-md border border-white/5">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              Local-First
            </span>
            <span className="text-[10px] text-nexus-dim font-mono">v1.0.0</span>
          </div>
        ) : (
          <div className="flex justify-center py-1">
            <span className="w-2 h-2 rounded-full bg-emerald-400" title="Local-First Online" />
          </div>
        )}
      </div>
    </aside>
  );
};
