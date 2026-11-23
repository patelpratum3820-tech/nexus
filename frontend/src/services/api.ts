import {
  Project,
  DiscoverySession,
  DiscoveryQuestion,
  ProjectSpecification,
  MemoryItem,
  ResourceMetrics,
  ResourceLimits
} from '../types';

const API_BASE = 'http://127.0.0.1:8765/api';

async function safeFetch<T>(url: string, options?: RequestInit, fallback?: T): Promise<T> {
  try {
    const res = await fetch(url, options);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    if (fallback !== undefined) return fallback;
    throw err;
  }
}

export const api = {
  system: {
    getHealth: () =>
      safeFetch<{ status: string; service: string; version: string; pid: number }>(
        `${API_BASE}/system/health`,
        undefined,
        { status: 'healthy', service: 'NEXUS Simulation', version: '1.0.0-phase1', pid: 0 }
      ),
    shutdown: () =>
      fetch(`${API_BASE}/system/shutdown`, { method: 'POST' }).then(r => r.json()),
  },

  resources: {
    getMetrics: (): Promise<ResourceMetrics> =>
      safeFetch<ResourceMetrics>(
        `${API_BASE}/resources/metrics`,
        undefined,
        {
          cpu_percent: 12.4,
          ram_used_gb: 5.6,
          ram_total_gb: 15.7,
          ram_available_gb: 10.1,
          ram_load_percent: 36,
          status: 'normal',
          active_tasks_count: 0,
          can_start_heavy_task: true,
          timestamp: Date.now() / 1000
        }
      ),
    getLimits: (): Promise<ResourceLimits> =>
      safeFetch<ResourceLimits>(
        `${API_BASE}/resources/limits`,
        undefined,
        { max_cpu_percent: 85, min_ram_gb: 1.5, max_concurrent_tasks: 2, active_workers: [] }
      ),
    updateLimits: (limits: Partial<ResourceLimits>) =>
      fetch(`${API_BASE}/resources/limits`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(limits)
      }).then(r => r.json())
  },

  discovery: {
    start: (title: string, initialPrompt: string, projectId?: string): Promise<DiscoverySession> =>
      safeFetch<DiscoverySession>(`${API_BASE}/discovery/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, initial_prompt: initialPrompt, project_id: projectId })
      }),
    submitAnswer: (
      sessionId: string,
      questionId: string,
      questionText: string,
      answerType: string,
      answerValue: any,
      isConfirmed: boolean = true
    ) =>
      safeFetch<any>(`${API_BASE}/discovery/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          question_id: questionId,
          question_text: questionText,
          answer_type: answerType,
          answer_value: answerValue,
          is_confirmed: isConfirmed
        })
      }),
    getSpec: (sessionId: string): Promise<ProjectSpecification> =>
      safeFetch<ProjectSpecification>(`${API_BASE}/discovery/spec/${sessionId}`)
  },

  memory: {
    list: (category?: string, projectId?: string, query?: string): Promise<MemoryItem[]> => {
      const params = new URLSearchParams();
      if (category) params.append('category', category);
      if (projectId) params.append('project_id', projectId);
      if (query) params.append('query', query);
      return safeFetch<MemoryItem[]>(`${API_BASE}/memory/list?${params.toString()}`, undefined, []);
    },
    add: (item: { category: string; key: string; content: string; project_id?: string; source?: string }) =>
      safeFetch<any>(`${API_BASE}/memory/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(item)
      }),
    delete: (id: string) =>
      safeFetch<any>(`${API_BASE}/memory/${id}`, { method: 'DELETE' })
  },

  projects: {
    list: (): Promise<Project[]> => safeFetch<Project[]>(`${API_BASE}/projects/list`, undefined, []),
    create: (name: string, description: string, initialSpec?: any): Promise<Project> =>
      safeFetch<Project>(`${API_BASE}/projects/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description, initial_spec: initialSpec })
      }),
    approve: (id: string) =>
      safeFetch<any>(`${API_BASE}/projects/${id}/approve`, { method: 'POST' })
  },

  ai: {
    getStatus: () => safeFetch<any>(`${API_BASE}/ai/status`),
    chat: (messages: { role: string; content: string }[], modelName?: string) =>
      safeFetch<any>(`${API_BASE}/ai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages, model_name: modelName })
      }),
    getHardware: () => safeFetch<any>(`${API_BASE}/ai/hardware`),
    getModels: () => safeFetch<any[]>(`${API_BASE}/ai/models`, undefined, [])
  }
};
