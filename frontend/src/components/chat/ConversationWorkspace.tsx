import React, { useState } from 'react';
import {
  Send,
  Sparkles,
  Bot,
  User,
  Terminal,
  ArrowRight,
  ShieldAlert,
  Code2,
  FolderGit2
} from 'lucide-react';
import { api } from '../../services/api';
import { Project } from '../../types';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

interface ConversationWorkspaceProps {
  onStartDiscovery: () => void;
  onOpenProjects: () => void;
  activeProject: Project | null;
}

export const ConversationWorkspace: React.FC<ConversationWorkspaceProps> = ({
  onStartDiscovery,
  onOpenProjects,
  activeProject
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'init-1',
      role: 'assistant',
      content:
        'Welcome to NEXUS — your local-first personal AI operating system workspace.\n\n' +
        'In Phase 1, the core architecture, resource manager, multi-tier memory, and project discovery engine are active. ' +
        'Local AI inference is running in zero-resource simulation mode to protect your hardware until Phase 2.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const handleSend = async () => {
    if (!input.trim() || isTyping) return;

    const userMsg: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    try {
      const chatHistory = [...messages, userMsg].map((m) => ({
        role: m.role,
        content: m.content
      }));

      const res = await api.ai.chat(chatHistory);

      const aiMsg: Message = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: res.reply || 'Acknowledged in local memory.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      const errMsg: Message = {
        id: `err-${Date.now()}`,
        role: 'system',
        content: `Simulation notice: ${err.message}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const suggestions = [
    { text: 'I want to build an e-commerce app and website', action: onStartDiscovery },
    { text: 'What is the current hardware & resource usage?', action: () => setInput('What is the current resource status?') },
    { text: 'Review stored architectural decisions and memory', action: () => setInput('Show active project decisions and memory tiers.') }
  ];

  return (
    <div className="h-full flex flex-col justify-between overflow-hidden relative select-none">
      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 max-w-4xl mx-auto w-full">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex items-start gap-3.5 ${
              m.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {m.role !== 'user' && (
              <div className="w-8 h-8 rounded-xl bg-lavender/15 border border-lavender/30 flex items-center justify-center text-lavender shrink-0 shadow-sm">
                <Bot className="w-4 h-4" />
              </div>
            )}

            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 text-xs leading-relaxed space-y-1 shadow-md ${
                m.role === 'user'
                  ? 'bg-lavender text-obsidian-400 font-medium'
                  : m.role === 'system'
                  ? 'bg-amber-500/10 border border-amber-500/20 text-amber-300 font-mono'
                  : 'bg-surface-elevated/90 border border-surface-border text-nexus-text'
              }`}
            >
              <div className="whitespace-pre-wrap">{m.content}</div>
              <div
                className={`text-[9px] pt-1 text-right ${
                  m.role === 'user' ? 'text-obsidian-300' : 'text-nexus-dim'
                }`}
              >
                {m.timestamp}
              </div>
            </div>

            {m.role === 'user' && (
              <div className="w-8 h-8 rounded-xl bg-surface-elevated border border-surface-border flex items-center justify-center text-nexus-muted shrink-0">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}

        {isTyping && (
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-lavender/15 border border-lavender/30 flex items-center justify-center text-lavender shrink-0">
              <Bot className="w-4 h-4" />
            </div>
            <div className="bg-surface-elevated border border-surface-border rounded-2xl px-4 py-2.5 text-xs text-nexus-muted flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-lavender animate-pulse" />
              <span className="w-1.5 h-1.5 rounded-full bg-lavender animate-pulse delay-75" />
              <span className="w-1.5 h-1.5 rounded-full bg-lavender animate-pulse delay-150" />
            </div>
          </div>
        )}
      </div>

      {/* Suggestion Pills & Input Area */}
      <div className="p-4 max-w-4xl mx-auto w-full space-y-3">
        {messages.length < 3 && (
          <div className="flex items-center gap-2 overflow-x-auto pb-1">
            {suggestions.map((s, i) => (
              <button
                key={i}
                onClick={s.action}
                className="text-left text-[11px] px-3 py-1.5 rounded-xl bg-surface-elevated hover:bg-surface-hover text-nexus-muted hover:text-nexus-text border border-surface-border transition-all whitespace-nowrap flex items-center gap-1.5"
              >
                <Sparkles className="w-3 h-3 text-lavender" />
                <span>{s.text}</span>
              </button>
            ))}
          </div>
        )}

        {/* Command D+ Style Obsidian Input Box */}
        <div className="bg-surface-elevated/95 border border-surface-border focus-within:border-lavender/50 rounded-2xl p-2.5 flex items-end gap-2 shadow-2xl transition-all">
          <textarea
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Instruct NEXUS, manage a project, or type a requirement..."
            className="flex-1 bg-transparent border-none text-xs text-nexus-text placeholder-nexus-dim px-2 py-1.5 focus:outline-none resize-none max-h-32"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isTyping}
            className="p-2 rounded-xl bg-lavender text-obsidian-400 hover:bg-lavender-light disabled:opacity-30 transition-all shrink-0"
            title="Send Message"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
