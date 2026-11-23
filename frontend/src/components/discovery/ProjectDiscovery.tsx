import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  CheckCircle2,
  HelpCircle,
  ArrowRight,
  RefreshCw,
  FileText,
  AlertCircle,
  Plus,
  ShieldCheck
} from 'lucide-react';
import { api } from '../../services/api';
import { DiscoverySession, DiscoveryQuestion, ProjectSpecification } from '../../types';

export const ProjectDiscovery: React.FC = () => {
  const [session, setSession] = useState<DiscoverySession | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<DiscoveryQuestion | null>(null);
  const [selectedChoices, setSelectedChoices] = useState<string[]>([]);
  const [customText, setCustomText] = useState('');
  const [initialPrompt, setInitialPrompt] = useState('I want to build an e-commerce app and website.');
  const [projectTitle, setProjectTitle] = useState('My Next E-Commerce');
  const [specification, setSpecification] = useState<ProjectSpecification | null>(null);
  const [isApproved, setIsApproved] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const startSession = async () => {
    setIsLoading(true);
    try {
      const s = await api.discovery.start(projectTitle, initialPrompt);
      setSession(s);
      setCurrentQuestion(s.current_question || null);
      setSelectedChoices([]);
      setCustomText('');
      setSpecification(null);
      setIsApproved(false);
    } finally {
      setIsLoading(false);
    }
  };

  const submitAnswer = async (isConfirmed: boolean = true) => {
    if (!session || !currentQuestion) return;

    let answerVal: any = selectedChoices;
    if (currentQuestion.type === 'choice') {
      answerVal = selectedChoices[0] || customText || 'Not sure';
    } else if (currentQuestion.type === 'text') {
      answerVal = customText;
    } else if (selectedChoices.length === 0 && customText) {
      answerVal = [customText];
    }

    setIsLoading(true);
    try {
      const res = await api.discovery.submitAnswer(
        session.session_id,
        currentQuestion.id,
        currentQuestion.text,
        currentQuestion.type,
        answerVal,
        isConfirmed
      );

      if (res.status === 'completed' && res.specification) {
        setSpecification(res.specification);
        setCurrentQuestion(null);
      } else if (res.next_question) {
        setCurrentQuestion(res.next_question);
        setSelectedChoices([]);
        setCustomText('');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleOption = (opt: string) => {
    if (currentQuestion?.type === 'choice') {
      setSelectedChoices([opt]);
    } else {
      setSelectedChoices(prev =>
        prev.includes(opt) ? prev.filter(x => x !== opt) : [...prev, opt]
      );
    }
  };

  const handleApprove = () => {
    setIsApproved(true);
    // Create new project from confirmed spec
    if (specification) {
      api.projects.create(specification.title, specification.initial_goal, specification);
    }
  };

  return (
    <div className="h-full overflow-y-auto p-6 max-w-4xl mx-auto space-y-6">
      {/* Title & Vision Banner */}
      <div className="space-y-1.5 pb-4 border-b border-surface-border">
        <div className="flex items-center gap-2 text-lavender">
          <Sparkles className="w-5 h-5" />
          <h1 className="text-lg font-semibold text-nexus-text">Project Discovery Engine</h1>
        </div>
        <p className="text-xs text-nexus-muted leading-relaxed">
          NEXUS identifies missing requirements through adaptive, contextual inquiry rather than static questionnaires.
          Every answer distinguishes between confirmed technical decisions and flexible assumptions.
        </p>
      </div>

      {/* Start Session Input (if no active session) */}
      {!session && (
        <div className="bg-surface-elevated/80 border border-surface-border rounded-2xl p-6 space-y-4">
          <h2 className="text-sm font-semibold text-nexus-text">Initialize Discovery Session</h2>
          <div className="space-y-3">
            <div>
              <label className="text-xs text-nexus-muted block mb-1">Project Working Title</label>
              <input
                type="text"
                value={projectTitle}
                onChange={(e) => setProjectTitle(e.target.value)}
                className="w-full bg-obsidian-300 border border-surface-border rounded-lg px-3 py-2 text-xs text-nexus-text focus:outline-none focus:border-lavender"
              />
            </div>
            <div>
              <label className="text-xs text-nexus-muted block mb-1">Initial Vision / User Prompt</label>
              <textarea
                rows={3}
                value={initialPrompt}
                onChange={(e) => setInitialPrompt(e.target.value)}
                placeholder="Describe what you want to build (e.g. 'I want to build an e-commerce app and website')"
                className="w-full bg-obsidian-300 border border-surface-border rounded-lg px-3 py-2 text-xs text-nexus-text focus:outline-none focus:border-lavender resize-none"
              />
            </div>
          </div>
          <button
            onClick={startSession}
            disabled={isLoading}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-lavender text-obsidian-400 font-semibold text-xs hover:bg-lavender-light transition-all shadow-md disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4" />
            <span>Begin Adaptive Discovery</span>
          </button>
        </div>
      )}

      {/* Active Adaptive Question View */}
      {session && currentQuestion && (
        <div className="bg-surface-elevated/80 border border-surface-border rounded-2xl p-6 space-y-5 animate-in fade-in duration-200">
          <div className="flex items-center justify-between text-xs text-nexus-muted pb-2 border-b border-surface-border">
            <span className="capitalize text-lavender font-mono">Category: {currentQuestion.category}</span>
            <span>Question {currentQuestion.type === 'multiselect' ? '(Multi-Select)' : '(Single-Choice)'}</span>
          </div>

          <h3 className="text-base font-semibold text-nexus-text leading-snug">
            {currentQuestion.text}
          </h3>

          {/* Options */}
          <div className="space-y-2.5">
            {currentQuestion.options?.map((opt) => {
              const isSelected = selectedChoices.includes(opt);
              return (
                <div
                  key={opt}
                  onClick={() => handleToggleOption(opt)}
                  className={`p-3.5 rounded-xl border text-xs cursor-pointer transition-all duration-150 flex items-center justify-between ${
                    isSelected
                      ? 'bg-lavender/15 border-lavender text-nexus-text shadow-[0_0_15px_rgba(157,140,255,0.1)]'
                      : 'bg-obsidian-300/80 border-surface-border text-nexus-muted hover:text-nexus-text hover:bg-obsidian-300'
                  }`}
                >
                  <span>{opt}</span>
                  {isSelected && <CheckCircle2 className="w-4 h-4 text-lavender shrink-0" />}
                </div>
              );
            })}
          </div>

          {/* Custom text or Not sure */}
          {currentQuestion.allow_custom && (
            <div className="pt-2">
              <input
                type="text"
                placeholder="Other specific requirement or custom answer..."
                value={customText}
                onChange={(e) => setCustomText(e.target.value)}
                className="w-full bg-obsidian-300 border border-surface-border rounded-lg px-3 py-2 text-xs text-nexus-text focus:outline-none focus:border-lavender"
              />
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-between pt-4 border-t border-surface-border">
            <div className="flex items-center gap-2">
              <button
                onClick={() => submitAnswer(false)}
                className="px-3 py-2 rounded-lg text-xs text-nexus-muted hover:text-nexus-text hover:bg-white/5 border border-surface-border"
                title="Mark as assumption rather than permanent requirement"
              >
                Accept as Assumption
              </button>
              <button
                onClick={() => submitAnswer(false)}
                className="px-3 py-2 rounded-lg text-xs text-nexus-muted hover:text-nexus-text hover:bg-white/5"
              >
                Not sure / Skip
              </button>
            </div>

            <button
              onClick={() => submitAnswer(true)}
              className="flex items-center gap-2 px-5 py-2 rounded-xl bg-lavender text-obsidian-400 font-semibold text-xs hover:bg-lavender-light transition-all"
            >
              <span>Confirm Decision</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* Generated Project Specification View */}
      {specification && (
        <div className="bg-surface-elevated/80 border border-surface-border rounded-2xl p-6 space-y-6 animate-in fade-in duration-300">
          <div className="flex items-center justify-between pb-3 border-b border-surface-border">
            <div className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-lavender" />
              <h2 className="text-base font-semibold text-nexus-text">Structured Project Specification</h2>
            </div>
            <span className={`text-xs px-3 py-1 rounded-full border ${isApproved ? 'bg-emerald-400/10 text-emerald-400 border-emerald-400/20' : 'bg-amber-400/10 text-amber-400 border-amber-400/20'}`}>
              {isApproved ? 'Approved for Implementation' : 'Pending User Approval'}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Confirmed Requirements */}
            <div className="bg-obsidian-300/80 border border-surface-border rounded-xl p-4 space-y-3">
              <h3 className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5 uppercase tracking-wider">
                <CheckCircle2 className="w-3.5 h-3.5" /> Confirmed Decisions ({specification.confirmed_decisions.length})
              </h3>
              <div className="space-y-2">
                {specification.confirmed_decisions.map((cd, i) => (
                  <div key={i} className="text-xs p-2 bg-obsidian-400/60 rounded border border-white/5 space-y-0.5">
                    <p className="text-nexus-muted font-medium">{cd.question}</p>
                    <p className="text-nexus-text font-mono text-[11px] text-lavender">
                      {Array.isArray(cd.decision) ? cd.decision.join(', ') : cd.decision}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Assumptions */}
            <div className="bg-obsidian-300/80 border border-surface-border rounded-xl p-4 space-y-3">
              <h3 className="text-xs font-semibold text-amber-400 flex items-center gap-1.5 uppercase tracking-wider">
                <AlertCircle className="w-3.5 h-3.5" /> Tracked Assumptions ({specification.assumptions.length})
              </h3>
              <div className="space-y-2">
                {specification.assumptions.length === 0 ? (
                  <p className="text-xs text-nexus-dim italic">No unconfirmed assumptions remaining.</p>
                ) : (
                  specification.assumptions.map((as, i) => (
                    <div key={i} className="text-xs p-2 bg-obsidian-400/60 rounded border border-white/5 space-y-0.5">
                      <p className="text-nexus-muted font-medium">{as.question}</p>
                      <p className="text-nexus-text text-[11px] text-amber-300/90">{String(as.decision)}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Architecture Plan */}
          <div className="bg-obsidian-300/80 border border-surface-border rounded-xl p-4 space-y-2">
            <h3 className="text-xs font-semibold text-lavender uppercase tracking-wider">
              Recommended Architecture
            </h3>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-nexus-muted block">Frontend:</span>
                <span className="text-nexus-text font-mono text-[11px]">{specification.recommended_architecture.frontend}</span>
              </div>
              <div>
                <span className="text-nexus-muted block">Backend:</span>
                <span className="text-nexus-text font-mono text-[11px]">{specification.recommended_architecture.backend}</span>
              </div>
              <div>
                <span className="text-nexus-muted block">Database:</span>
                <span className="text-nexus-text font-mono text-[11px]">{specification.recommended_architecture.database}</span>
              </div>
              <div>
                <span className="text-nexus-muted block">State Model:</span>
                <span className="text-nexus-text font-mono text-[11px]">{specification.recommended_architecture.state_management}</span>
              </div>
            </div>
          </div>

          {/* Approval Action */}
          <div className="flex items-center justify-between pt-3 border-t border-surface-border">
            <button
              onClick={startSession}
              className="flex items-center gap-1.5 text-xs text-nexus-muted hover:text-nexus-text"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Start New Discovery
            </button>

            {!isApproved ? (
              <button
                onClick={handleApprove}
                className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-obsidian-400 font-semibold text-xs transition-all shadow-lg shadow-emerald-500/20"
              >
                <ShieldCheck className="w-4 h-4" />
                <span>Approve Specification</span>
              </button>
            ) : (
              <div className="flex items-center gap-2 text-xs text-emerald-400 font-medium">
                <CheckCircle2 className="w-4 h-4" />
                <span>Specification Approved & Saved</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
