import { useCallback, useEffect } from 'react';
import { api } from '@/services/api';
import { useTaskStore } from '@/store/taskStore';
import type { Task, TaskFilter, CreateTaskData } from '@/types/task';

export function useTasks() {
  const {
    tasks,
    currentTask,
    projects,
    filter,
    stats,
    isLoading,
    error,
    setTasks,
    addTask,
    updateTask,
    removeTask,
    setCurrentTask,
    setProjects,
    setFilter,
    setStats,
    setLoading,
    setError,
    createProject,
    updateProject,
    deleteProject,
    getProjectProgress,
  } = useTaskStore();

  const fetchTasks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getTasks({
        status: filter.status,
        project_id: filter.project_id,
        priority: filter.priority,
        limit: 100,
      });
      setTasks(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch tasks');
    } finally {
      setLoading(false);
    }
  }, [filter, setTasks, setLoading, setError]);

  const fetchStats = useCallback(async () => {
    try {
      const data = await api.getTaskStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  }, [setStats]);

  const fetchProjects = useCallback(async () => {
    try {
      const data = await api.getProjects({ limit: 100 });
      setProjects(data);
    } catch (err) {
      console.error('Failed to fetch projects:', err);
    }
  }, [setProjects]);

  const createTask = useCallback(async (data: CreateTaskData) => {
    setLoading(true);
    setError(null);
    try {
      const newTask = await api.createTask(data);
      addTask(newTask);
      await fetchStats();
      return newTask;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create task');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [addTask, fetchStats, setLoading, setError]);

  const updateTaskById = useCallback(async (id: string, data: Partial<Task>) => {
    setError(null);
    try {
      const updated = await api.updateTask(id, data);
      updateTask(id, updated);
      return updated;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update task');
      throw err;
    }
  }, [updateTask, setError]);

  const completeTaskById = useCallback(async (id: string, actualMinutes?: number) => {
    setError(null);
    try {
      const completed = await api.completeTask(id, actualMinutes);
      updateTask(id, completed);
      await fetchStats();
      return completed;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to complete task');
      throw err;
    }
  }, [updateTask, fetchStats, setError]);

  const startFocus = useCallback(async (task: Task) => {
    setError(null);
    try {
      await api.startTask(task.id);
      setCurrentTask(task);
      const updated = await api.updateTask(task.id, { status: 'in_progress' });
      updateTask(task.id, updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start focus');
      throw err;
    }
  }, [setCurrentTask, updateTask, setError]);

  const endFocus = useCallback(() => {
    setCurrentTask(null);
  }, [setCurrentTask]);

  const recommendNext = useCallback(async (availableMinutes?: number) => {
    setError(null);
    try {
      const recommendation = await api.recommendNextTask(availableMinutes);
      return recommendation;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get recommendation');
      throw err;
    }
  }, [setError]);

  useEffect(() => {
    fetchTasks();
    fetchStats();
    fetchProjects();
  }, [fetchTasks, fetchStats, fetchProjects]);

  return {
    tasks,
    currentTask,
    projects,
    filter,
    stats,
    isLoading,
    error,
    fetchTasks,
    fetchProjects,
    createProject,
    updateProject,
    deleteProject,
    getProjectProgress,
    createTask,
    updateTask: updateTaskById,
    completeTask: completeTaskById,
    startFocus,
    endFocus,
    recommendNext,
    setFilter,
  };
}