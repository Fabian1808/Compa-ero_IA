import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Task, TaskFilter, TaskStats } from '@/types/task';
import { Project } from '@/types/api';
import { api } from '@/services/api';

/** Payload returned by `GET /projects/{id}/progress`. */
export interface ProjectProgress {
  project_id: string;
  name: string;
  progress: number;
  total_tasks: number;
  completed_tasks: number;
  in_progress_tasks: number;
  blocked_tasks: number;
}

interface TaskState {
  tasks: Task[];
  currentTask: Task | null;
  projects: Project[];
  filter: TaskFilter;
  stats: TaskStats;
  isLoading: boolean;
  error: string | null;

  // Actions
  setTasks: (tasks: Task[]) => void;
  addTask: (task: Task) => void;
  updateTask: (id: string, data: Partial<Task>) => void;
  removeTask: (id: string) => void;
  setCurrentTask: (task: Task | null) => void;
  setProjects: (projects: Project[]) => void;
  setFilter: (filter: Partial<TaskFilter>) => void;
  setStats: (stats: TaskStats) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;

  // Projects
  fetchProjects: () => Promise<void>;
  createProject: (data: Partial<Project>) => Promise<void>;
  updateProject: (id: string, data: Partial<Project>) => Promise<void>;
  deleteProject: (id: string) => Promise<void>;
  getProjectProgress: (id: string) => Promise<ProjectProgress>;
}

export const useTaskStore = create<TaskState>()(
  persist(
    (set) => ({
      tasks: [],
      currentTask: null,
      projects: [],
      filter: { status: ['pending', 'in_progress', 'blocked'] },
      stats: { completed_today: 0, pending: 0, in_progress: 0, blocked: 0 },
      isLoading: false,
      error: null,

      setTasks: (tasks) => set({ tasks }),
      addTask: (task) => set((state) => ({ tasks: [task, ...state.tasks] })),
      updateTask: (id, data) =>
        set((state) => ({
          tasks: state.tasks.map((t) => (t.id === id ? { ...t, ...data } : t)),
          currentTask: state.currentTask?.id === id ? { ...state.currentTask, ...data } : state.currentTask,
        })),
      removeTask: (id) =>
        set((state) => ({
          tasks: state.tasks.filter((t) => t.id !== id),
          currentTask: state.currentTask?.id === id ? null : state.currentTask,
        })),
      setCurrentTask: (task) => set({ currentTask: task }),
      setProjects: (projects) => set({ projects }),
      setFilter: (filter) => set((state) => ({ filter: { ...state.filter, ...filter } })),
      setStats: (stats) => set({ stats }),
      setLoading: (isLoading) => set({ isLoading }),
      setError: (error) => set({ error }),

      // Projects: the API is the source of truth, so every mutation refetches
      // the list instead of patching local state and drifting from the server.
      fetchProjects: async () => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.get<Project[]>('/projects');
          set({ projects: response.data });
        } catch (error) {
          set({ error: error instanceof Error ? error.message : 'Failed to load projects' });
        } finally {
          set({ isLoading: false });
        }
      },

      createProject: async (data) => {
        const response = await api.post<Project>('/projects', data);
        set((state) => ({ projects: [response.data, ...state.projects] }));
      },

      updateProject: async (id, data) => {
        const response = await api.patch<Project>(`/projects/${id}`, data);
        set((state) => ({
          projects: state.projects.map((p) => (p.id === id ? response.data : p)),
        }));
      },

      deleteProject: async (id) => {
        await api.delete(`/projects/${id}`);
        set((state) => ({ projects: state.projects.filter((p) => p.id !== id) }));
      },

      getProjectProgress: async (id) => {
        const response = await api.get<ProjectProgress>(`/projects/${id}/progress`);
        return response.data;
      },
    }),
    {
      name: 'task-storage',
      partialize: (state) => ({ filter: state.filter }),
    }
  )
);