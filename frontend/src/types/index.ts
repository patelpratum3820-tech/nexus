export type NavigationTab = 'chat' | 'projects' | 'discovery' | 'memory' | 'tasks' | 'files' | 'settings';

export interface Project {
  id: string;
  name: string;
  description: string;
  status: 'planning' | 'active' | 'paused' | 'completed';
  spec?: ProjectSpecification;
  created_at?: string;
  updated_at?: string;
}

export interface DiscoveryQuestion {
  id: string;
  text: string;
  type: 'choice' | 'multiselect' | 'text' | 'skip';
  options?: string[];
  allow_custom?: boolean;
  allow_not_sure?: boolean;
  category: string;
}

export interface DiscoverySession {
  session_id: string;
  title: string;
  initial_prompt: string;
  flow_type: string;
  total_questions_estimated: number;
  current_question?: DiscoveryQuestion;
  status: 'in_progress' | 'completed';
}

export interface ConfirmedDecision {
  question: string;
  decision: any;
  type: string;
}

export interface ProjectSpecification {
  title: string;
  initial_goal: string;
  confirmed_decisions: ConfirmedDecision[];
  assumptions: ConfirmedDecision[];
  recommended_architecture: {
    frontend: string;
    backend: string;
    database: string;
    state_management: string;
  };
  status: 'pending_user_approval' | 'approved';
  next_steps: string[];
}

export interface MemoryItem {
  id: string;
  category: 'personal_preference' | 'project_decision' | 'conversation_context' | 'confirmed_decision' | 'technical_doc' | 'task_history';
  project_id?: string;
  key: string;
  content: string;
  source: string;
  confidence: number;
  is_active: number;
  created_at?: string;
  updated_at?: string;
}

export interface ResourceMetrics {
  cpu_percent: number;
  ram_used_gb: number;
  ram_total_gb: number;
  ram_available_gb: number;
  ram_load_percent: number;
  status: 'normal' | 'constrained' | 'critical';
  active_tasks_count: number;
  can_start_heavy_task: boolean;
  timestamp: number;
}

export interface ResourceLimits {
  max_cpu_percent: number;
  min_ram_gb: number;
  max_concurrent_tasks: number;
  active_workers: string[];
}

export type CompanionEyeState = 'idle' | 'blink' | 'look_left' | 'look_right' | 'listening' | 'processing' | 'happy';
