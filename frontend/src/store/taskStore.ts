import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Task, TaskFilter, TaskStats } from '@/types/task';
import { Project } from '@/types/api';

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
    }),
    {
      name: 'task-storage',
      partialize: (state) => ({ filter: state.filter }),
    }
  )
);