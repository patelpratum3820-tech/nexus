import React, { useState, useEffect } from 'react';
import {
  FolderGit2,
  Plus,
  ExternalLink,
  Calendar,
  CheckCircle2,
  Clock,
  ArrowRight
} from 'lucide-react';
import { api } from '../../services/api';
import { Project } from '../../types';

interface ProjectListProps {
  onSelectProject: (p: Project) => void;
  onStartDiscovery: () => void;
}

export const ProjectList: React.FC<ProjectListProps> = ({ onSelectProject, onStartDiscovery }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [projectName, setProjectName] = useState('');
  const [projectDesc, setProjectDesc] = useState('');

  const loadProjects = async () => {
    const list = await api.projects.list();
    setProjects(list);
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectName) return;
    await api.projects.create(projectName, projectDesc);
    setProjectName('');
    setProjectDesc('');
    setShowCreateModal(false);
    loadProjects();
  };

  return (
    <div className="h-full overflow-y-auto p-6 max-w-5xl mx-auto space-y-6 select-none">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-surface-border">
        <div>
          <div className="flex items-center gap-2 text-lavender">
            <FolderGit2 className="w-5 h-5" />
            <h1 className="text-lg font-semibold text-nexus-text">Managed Software Projects</h1>
          </div>
          <p className="text-xs text-nexus-muted pt-1">
            Local projects, architectural specifications, confirmed requirements, and roadmap stages.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onStartDiscovery}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-obsidian-300 hover:bg-obsidian-400 text-nexus-text border border-surface-border text-xs font-medium transition-all"
          >
            <span>Run Discovery</span>
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-lavender text-obsidian-400 font-semibold text-xs hover:bg-lavender-light transition-all shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>New Project</span>
          </button>
        </div>
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {projects.length === 0 ? (
          <div className="col-span-2 text-center py-12 border border-dashed border-surface-border rounded-2xl space-y-3">
            <FolderGit2 className="w-8 h-8 mx-auto text-nexus-dim" />
            <p className="text-xs text-nexus-muted">No managed projects yet.</p>
            <button
              onClick={onStartDiscovery}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-lavender/20 text-lavender border border-lavender/30 text-xs font-semibold"
            >
              Start Adaptive Discovery
            </button>
          </div>
        ) : (
          projects.map((p) => (
            <div
              key={p.id}
              onClick={() => onSelectProject(p)}
              className="bg-surface-elevated/80 border border-surface-border hover:border-lavender/40 rounded-xl p-5 space-y-3 transition-all cursor-pointer group"
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono uppercase tracking-wider text-lavender px-2 py-0.5 rounded bg-lavender/10 border border-lavender/20">
                  {p.status}
                </span>
                <ArrowRight className="w-4 h-4 text-nexus-dim group-hover:text-lavender group-hover:translate-x-1 transition-all" />
              </div>

              <div>
                <h3 className="text-sm font-semibold text-nexus-text group-hover:text-lavender transition-colors">
                  {p.name}
                </h3>
                <p className="text-xs text-nexus-muted pt-1 line-clamp-2 leading-relaxed">
                  {p.description || 'No initial description provided.'}
                </p>
              </div>

              <div className="flex items-center justify-between text-[11px] text-nexus-dim pt-2 border-t border-white/5">
                <span className="flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5" /> Created {new Date(p.created_at || Date.now()).toLocaleDateString()}
                </span>
                {p.spec && (
                  <span className="text-emerald-400 font-medium">Spec Attached</span>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <form
            onSubmit={handleCreate}
            className="bg-obsidian-100 border border-surface-border rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl"
          >
            <h2 className="text-sm font-semibold text-nexus-text flex items-center gap-2">
              <Plus className="w-4 h-4 text-lavender" /> Initialize New Project
            </h2>

            <div className="space-y-3">
              <div>
                <label className="text-xs text-nexus-muted block mb-1">Project Name</label>
                <input
                  type="text"
                  placeholder="e.g. Nexus Core or Local Media Vault"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  className="w-full bg-obsidian-300 border border-surface-border rounded-lg px-3 py-2 text-xs text-nexus-text focus:outline-none focus:border-lavender"
                  required
                />
              </div>

              <div>
                <label className="text-xs text-nexus-muted block mb-1">Description / Goals</label>
                <textarea
                  rows={3}
                  placeholder="Briefly state the goal of this software project..."
                  value={projectDesc}
                  onChange={(e) => setProjectDesc(e.target.value)}
                  className="w-full bg-obsidian-300 border border-surface-border rounded-lg px-3 py-2 text-xs text-nexus-text focus:outline-none focus:border-lavender resize-none"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 rounded-lg text-xs font-medium text-nexus-muted hover:text-nexus-text hover:bg-white/5"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 rounded-lg text-xs font-medium bg-lavender text-obsidian-400 font-semibold hover:bg-lavender-light"
              >
                Create Project
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
