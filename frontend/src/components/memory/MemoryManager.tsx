import React, { useState, useEffect } from 'react';
import {
  Database,
  Search,
  Plus,
  Trash2,
  Edit2,
  ShieldAlert,
  Tag,
  Clock,
  CheckCircle,
  FileText
} from 'lucide-react';
import { api } from '../../services/api';
import { MemoryItem } from '../../types';

export const MemoryManager: React.FC = () => {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [newKey, setNewKey] = useState('');
  const [newContent, setNewContent] = useState('');
  const [newCategory, setNewCategory] = useState<MemoryItem['category']>('personal_preference');
  const [conflictNotice, setConflictNotice] = useState<string | null>(null);

  const categories = [
    { id: 'all', label: 'All Tiers' },
    { id: 'personal_preference', label: 'Personal Preferences' },
    { id: 'project_decision', label: 'Project Decisions' },
    { id: 'confirmed_decision', label: 'Confirmed Decisions' },
    { id: 'technical_doc', label: 'Technical Documentation' },
    { id: 'task_history', label: 'Task History' },
    { id: 'conversation_context', label: 'Conversation Context' },
  ];

  const loadMemories = async () => {
    const cat = selectedCategory === 'all' ? undefined : selectedCategory;
    const data = await api.memory.list(cat, undefined, searchQuery);
    setMemories(data);
  };

  useEffect(() => {
    loadMemories();
  }, [selectedCategory, searchQuery]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKey || !newContent) return;

    const res = await api.memory.add({
      category: newCategory,
      key: newKey,
      content: newContent,
      source: 'user_explicit'
    });

    if (res.conflict_resolved) {
      setConflictNotice(`Previous value for "${newKey}" was archived to resolve conflict.`);
      setTimeout(() => setConflictNotice(null), 5000);
    }

    setNewKey('');
    setNewContent('');
    setShowAddModal(false);
    loadMemories();
  };

  const handleDelete = async (id: string) => {
    await api.memory.delete(id);
    loadMemories();
  };

  return (
    <div className="h-full overflow-y-auto p-6 max-w-5xl mx-auto space-y-6 select-none">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-surface-border">
        <div>
          <div className="flex items-center gap-2 text-lavender">
            <Database className="w-5 h-5" />
            <h1 className="text-lg font-semibold text-nexus-text">Multi-Tier Memory Engine</h1>
          </div>
          <p className="text-xs text-nexus-muted pt-1">
            Strict isolation between personal preferences, confirmed decisions, and technical documentation.
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-lavender text-obsidian-400 font-semibold text-xs hover:bg-lavender-light transition-all shadow-sm"
        >
          <Plus className="w-4 h-4" />
          <span>Add Explicit Memory</span>
        </button>
      </div>

      {/* Conflict Notice Toast */}
      {conflictNotice && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-amber-400/10 border border-amber-400/30 text-amber-300 text-xs">
          <ShieldAlert className="w-4 h-4 shrink-0" />
          <span>{conflictNotice}</span>
        </div>
      )}

      {/* Category Tabs & Search Bar */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-3">
        {/* Category Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto w-full md:w-auto pb-1">
          {categories.map((c) => (
            <button
              key={c.id}
              onClick={() => setSelectedCategory(c.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
                selectedCategory === c.id
                  ? 'bg-lavender/20 text-lavender border border-lavender/30'
                  : 'text-nexus-muted hover:text-nexus-text hover:bg-white/5 border border-transparent'
              }`}
            >
              {c.label}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative w-full md:w-64">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-nexus-muted" />
          <input
            type="text"
            placeholder="Search memory keys or contents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-surface-elevated border border-surface-border rounded-xl pl-9 pr-3 py-1.5 text-xs text-nexus-text focus:outline-none focus:border-lavender"
          />
        </div>
      </div>

      {/* Memory Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {memories.length === 0 ? (
          <div className="col-span-2 text-center py-12 border border-dashed border-surface-border rounded-2xl">
            <Database className="w-8 h-8 mx-auto text-nexus-dim mb-2" />
            <p className="text-xs text-nexus-muted">No memory entries found in this tier.</p>
          </div>
        ) : (
          memories.map((m) => (
            <div
              key={m.id}
              className="bg-surface-elevated/80 border border-surface-border hover:border-surface-border-active rounded-xl p-4 space-y-2.5 transition-all"
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono uppercase tracking-wider text-lavender px-2 py-0.5 rounded bg-lavender/10 border border-lavender/20">
                  {m.category.replace('_', ' ')}
                </span>
                <button
                  onClick={() => handleDelete(m.id)}
                  className="p-1 text-nexus-dim hover:text-red-400 transition-colors"
                  title="Delete memory"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>

              <div>
                <h3 className="text-xs font-semibold text-nexus-text font-mono">{m.key}</h3>
                <p className="text-xs text-nexus-muted pt-1 leading-relaxed">{m.content}</p>
              </div>

              <div className="flex items-center justify-between text-[10px] text-nexus-dim pt-2 border-t border-white/5">
                <span className="flex items-center gap-1">
                  <Tag className="w-3 h-3" /> Source: {m.source}
                </span>
                <span className="flex items-center gap-1">
                  <CheckCircle className="w-3 h-3 text-emerald-400" /> Confidence: {Math.round(m.confidence * 100)}%
                </span>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Add Memory Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <form
            onSubmit={handleAdd}
            className="bg-obsidian-100 border border-surface-border rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl"
          >
            <h2 className="text-sm font-semibold text-nexus-text flex items-center gap-2">
              <Plus className="w-4 h-4 text-lavender" /> Add Memory Item
            </h2>

            <div className="space-y-3">
              <div>
                <label className="text-xs text-nexus-muted block mb-1">Memory Tier / Category</label>
                <select
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value as any)}
                  className="w-full bg-obsidian-300 border border-surface-border rounded-lg px-3 py-2 text-xs text-nexus-text focus:outline-none focus:border-lavender"
                >
                  <option value="personal_preference">Personal Preference</option>
                  <option value="project_decision">Project Decision</option>
                  <option value="confirmed_decision">Confirmed Decision</option>
                  <option value="technical_doc">Technical Documentation</option>
                  <option value="task_history">Task History</option>
                  <option value="conversation_context">Conversation Context</option>
                </select>
              </div>

              <div>
                <label className="text-xs text-nexus-muted block mb-1">Key Identifier</label>
                <input
                  type="text"
                  placeholder="e.g. preferred_color_palette or default_database"
                  value={newKey}
                  onChange={(e) => setNewKey(e.target.value)}
                  className="w-full bg-obsidian-300 border border-surface-border rounded-lg px-3 py-2 text-xs text-nexus-text focus:outline-none focus:border-lavender"
                  required
                />
              </div>

              <div>
                <label className="text-xs text-nexus-muted block mb-1">Content / Rule Value</label>
                <textarea
                  rows={3}
                  placeholder="Describe the exact decision or preference..."
                  value={newContent}
                  onChange={(e) => setNewContent(e.target.value)}
                  className="w-full bg-obsidian-300 border border-surface-border rounded-lg px-3 py-2 text-xs text-nexus-text focus:outline-none focus:border-lavender resize-none"
                  required
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 rounded-lg text-xs font-medium text-nexus-muted hover:text-nexus-text hover:bg-white/5"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 rounded-lg text-xs font-medium bg-lavender text-obsidian-400 font-semibold hover:bg-lavender-light"
              >
                Save Memory
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
