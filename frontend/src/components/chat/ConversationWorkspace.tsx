import React, { useState, useEffect, useRef } from 'react';
import {
  Send,
  Sparkles,
  Bot,
  User,
  Terminal,
  ArrowRight,
  ShieldAlert,
  Code2,
  FolderGit2,
  Cpu,
  Square
} from 'lucide-react';
import { api } from '../../services/api';
import { Project } from '../../types';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  isMock?: boolean;
  tps?: number;
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
        'Phase 2.3 Gemma 3:1B integration is active. Real local AI streaming runs directly ' +
        'on your machine through Ollama on 127.0.0.1:11434 with strict hardware protection.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isMock: false
    }
  ]);
  const [input, setInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [providerStatus, setProviderStatus] = useState<any>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    api.ai.getStatus().then(setProviderStatus).catch(() => {});
  }, []);

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsGenerating(false);
  };

  const handleSend = async () => {
    if (!input.trim() || isGenerating) return;

    const userText = input.trim();
    const userMsg: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    const assistantMsgId = `ai-${Date.now()}`;
    const assistantPlaceholder: Message = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isMock: providerStatus?.is_mock_fallback ?? false
    };

    setMessages((prev) => [...prev, userMsg, assistantPlaceholder]);
    setInput('');
    setIsGenerating(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const chatHistory = [...messages, userMsg].map((m) => ({
        role: m.role,
        content: m.content
      }));

      await api.ai.streamChat(
        chatHistory,
        (chunk) => {
          if (chunk.error) {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsgId
                  ? {
                      ...m,
                      content: m.content
                        ? `${m.content}\n\n[Notice: ${chunk.error}]`
                        : `[Notice: ${chunk.error}]`
                    }
                  : m
              )
            );
            return;
          }

          if (chunk.token) {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsgId
                  ? {
                      ...m,
                      content: m.content + chunk.token,
                      isMock: chunk.provider === 'mock'
                    }
                  : m
              )
            );
          }

          if (chunk.done && chunk.tokens_per_second) {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsgId
                  ? {
                      ...m,
                      tps: chunk.tokens_per_second
                    }
                  : m
              )
            );
          }
        },
        'gemma3:1b',
        controller.signal
      );
    } catch (err: any) {
      if (err.name === 'AbortError') {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? {
                  ...m,
                  content: m.content
                    ? `${m.content}\n\n[Generation stopped by user]`
                    : '[Generation stopped by user]'
                }
              : m
          )
        );
      } else {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? {
                  ...m,
                  content: m.content
                    ? `${m.content}\n\n[Inference error: ${err.message}]`
                    : `[Inference error: ${err.message}]`
                }
              : m
          )
        );
      }
    } finally {
      setIsGenerating(false);
      abortControllerRef.current = null;
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const suggestions = [
    { text: 'What is NEXUS and what capabilities are active?', action: () => setInput('What is NEXUS and what capabilities are active?') },
    { text: 'Check current system resources and RAM headroom', action: () => setInput('What is the current resource status?') },
    { text: 'I want to build an e-commerce platform', action: onStartDiscovery }
  ];

  return (
    <div className="h-full flex flex-col justify-between overflow-hidden relative select-none">
      {/* Provider Discovery Status Banner */}
      {providerStatus && (
        <div className="px-6 pt-3 max-w-4xl mx-auto w-full">
          <div className={`flex items-center justify-between px-3 py-1.5 rounded-xl border text-[11px] ${
            providerStatus.ollama_available
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : 'bg-amber-500/10 border-amber-500/30 text-amber-300'
          }`}>
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${providerStatus.ollama_available ? 'bg-emerald-400' : 'bg-amber-400'}`} />
              <span className="font-medium">
                {providerStatus.ollama_available
                  ? `Local AI Engine: ${providerStatus.active_display_name} — Gemma 3:1B Ready`
                  : 'Engine Offline: Visible Mock Simulation Active'}
              </span>
            </div>
            <span className="text-[10px] opacity-75 font-mono">
              {providerStatus.ollama_available ? '127.0.0.1:11434 (Phase 2.3 Streaming)' : 'Mock Fallback Mode'}
            </span>
          </div>
        </div>
      )}

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
              <div className="whitespace-pre-wrap">{m.content || (isGenerating && m.role === 'assistant' ? 'Thinking...' : '')}</div>
              <div className="flex items-center justify-between text-[9px] pt-1 gap-3">
                {m.role === 'assistant' && (
                  <span className={`font-mono ${m.isMock ? 'text-amber-400' : 'text-emerald-400'}`}>
                    {m.isMock ? '🟡 mock-simulation' : '🟢 gemma3:1b (local)'}
                    {m.tps ? ` • ${m.tps} t/s` : ''}
                  </span>
                )}
                <span className={m.role === 'user' ? 'text-obsidian-300 ml-auto' : 'text-nexus-dim ml-auto'}>
                  {m.timestamp}
                </span>
              </div>
            </div>

            {m.role === 'user' && (
              <div className="w-8 h-8 rounded-xl bg-surface-elevated border border-surface-border flex items-center justify-center text-nexus-muted shrink-0">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}

        {isGenerating && (
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-lavender/15 border border-lavender/30 flex items-center justify-center text-lavender shrink-0">
              <Bot className="w-4 h-4" />
            </div>
            <div className="bg-surface-elevated border border-surface-border rounded-2xl px-4 py-2.5 text-xs text-nexus-muted flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-lavender animate-pulse" />
              <span className="w-1.5 h-1.5 rounded-full bg-lavender animate-pulse delay-75" />
              <span className="w-1.5 h-1.5 rounded-full bg-lavender animate-pulse delay-150" />
              <span className="text-[11px] text-lavender font-mono">Generating local tokens...</span>
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

        {/* Input Bar with Send / Stop Controls */}
        <div className="bg-surface-elevated/95 border border-surface-border focus-within:border-lavender/50 rounded-2xl p-2.5 flex items-end gap-2 shadow-2xl transition-all">
          <textarea
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isGenerating ? "Generation in progress..." : "Instruct NEXUS with local Gemma 3:1B..."}
            disabled={isGenerating}
            className="flex-1 bg-transparent border-none text-xs text-nexus-text placeholder-nexus-dim px-2 py-1.5 focus:outline-none resize-none max-h-32 disabled:opacity-50"
          />

          {isGenerating ? (
            <button
              onClick={handleStop}
              className="px-3 py-2 rounded-xl bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/30 text-xs font-semibold flex items-center gap-1.5 transition-all shrink-0 animate-pulse"
              title="Stop Generation"
            >
              <Square className="w-3.5 h-3.5 fill-current" />
              <span>Stop</span>
            </button>
          ) : (
            <button
              onClick={handleSend}
              disabled={!input.trim()}
              className="p-2 rounded-xl bg-lavender text-obsidian-400 hover:bg-lavender-light disabled:opacity-30 transition-all shrink-0"
              title="Send Message"
            >
              <Send className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
