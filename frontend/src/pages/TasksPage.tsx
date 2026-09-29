import { useState } from 'react';
import { useTasks } from '@/hooks/useTasks';
import { Task, TaskStatus } from '@/types/task';
import { Card, CardContent, Button, Input, Badge, Separator } from '@/components/ui';
import { Plus, Search, Filter, ChevronDown, CheckCircle, PauseCircle, XCircle, AlertTriangle, Flag } from 'lucide-react';
import { formatDate, getStatusColor, getPriorityColor, classNames } from '@/utils/formatters';

const statusOptions: { value: TaskStatus; label: string }[] = [
  { value: 'pending', label: 'Pendientes' },
  { value: 'in_progress', label: 'En marcha' },
  { value: 'blocked', label: 'Bloqueadas' },
  { value: 'waiting_response', label: 'Esperando respuesta' },
  { value: 'requires_decision', label: 'Requiere decisión' },
  { value: 'completed', label: 'Completadas' },
  { value: 'cancelled', label: 'Canceladas' },
];

const priorityOptions: { value: string; label: string }[] = [
  { value: '', label: 'Todas las prioridades' },
  { value: 'critical', label: 'Crítica' },
  { value: 'high', label: 'Alta' },
  { value: 'medium', label: 'Media' },
  { value: 'low', label: 'Baja' },
];

export function TasksPage() {
  const { tasks, projects, filter, isLoading, createTask, updateTask, completeTask, startFocus, setFilter, fetchTasks } = useTasks();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<TaskStatus[]>(filter.status || ['pending', 'in_progress', 'blocked']);
  const [selectedPriority, setSelectedPriority] = useState('');
  const [newTask, setNewTask] = useState({ title: '', description: '', priority: 'medium' as const, project_id: '' });

  const filteredTasks = tasks.filter((task) => {
    if (searchQuery && !task.title.toLowerCase().includes(searchQuery.toLowerCase()) && 
        !task.description?.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    if (selectedStatus.length > 0 && !selectedStatus.includes(task.status)) {
      return false;
    }
    if (selectedPriority && task.priority !== selectedPriority) {
      return false;
    }
    return true;
  });

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTask.title.trim()) return;
    try {
      await createTask(newTask);
      setShowCreateModal(false);
      setNewTask({ title: '', description: '', priority: 'medium', project_id: '' });
    } catch (err) {
      console.error('Failed to create task:', err);
    }
  };

  const handleStatusChange = (task: Task, newStatus: TaskStatus) => {
    if (newStatus === 'completed') {
      completeTask(task.id);
    } else if (newStatus === 'in_progress') {
      startFocus(task);
    } else {
      updateTask(task.id, { status: newStatus });
    }
  };

  const getStatusIcon = (status: TaskStatus) => {
    switch (status) {
      case 'completed': return <CheckCircle className="h-4 w-4" />;
      case 'in_progress': return <PauseCircle className="h-4 w-4" />;
      case 'blocked': return <AlertTriangle className="h-4 w-4" />;
      case 'waiting_response': return <Flag className="h-4 w-4" />;
      case 'requires_decision': return <AlertTriangle className="h-4 w-4" />;
      case 'cancelled': return <XCircle className="h-4 w-4" />;
      default: return <Flag className="h-4 w-4" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Pendientes</h1>
          <p className="text-slate-500 dark:text-slate-400">Gestiona y organiza tus tareas</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="h-4 w-4" />
          Nueva tarea
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="py-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="Buscar tareas..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2">
              <select
                value={selectedPriority}
                onChange={(e) => setSelectedPriority(e.target.value)}
                className="input w-auto"
              >
                {priorityOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
              <div className="relative">
                <Button variant="secondary" className="gap-2">
                  <Filter className="h-4 w-4" />
                  Estado
                  <ChevronDown className="h-4 w-4" />
                </Button>
                <div className="absolute right-0 top-full mt-1 w-48 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 shadow-lg py-1 z-50">
                  {statusOptions.map((opt) => (
                    <label key={opt.value} className="flex items-center gap-2 px-3 py-2 hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedStatus.includes(opt.value)}
                        onChange={(e) => setSelectedStatus(e.target.checked 
                          ? [...selectedStatus, opt.value] 
                          : selectedStatus.filter(s => s !== opt.value)
                        )}
                        className="rounded border-slate-300 text-primary-600 focus:ring-primary-500"
                      />
                      <span className="text-sm text-slate-700 dark:text-slate-300">{opt.label}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tasks List */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-8 text-center text-slate-500 dark:text-slate-400">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent mx-auto mb-2" />
              Cargando tareas...
            </div>
          ) : filteredTasks.length === 0 ? (
            <div className="p-8 text-center text-slate-500 dark:text-slate-400">
              <Flag className="h-12 w-12 mx-auto text-slate-300 dark:text-slate-600 mb-3" />
              <h3 className="font-medium text-slate-900 dark:text-slate-100 mb-1">No hay tareas</h3>
              <p className="text-sm">Intenta cambiar los filtros o crea una nueva tarea</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-200 dark:divide-slate-700">
              {filteredTasks.map((task) => (
                <div key={task.id} className="p-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                  <div className="flex items-start gap-4">
                    {/* Status selector */}
                    <select
                      value={task.status}
                      onChange={(e) => handleStatusChange(task, e.target.value as TaskStatus)}
                      className={`mt-1 px-2 py-1 rounded text-xs font-medium border ${getStatusColor(task.status)}`}
                    >
                      {statusOptions.map((opt) => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>

                    {/* Task content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start gap-3">
                        <div className="flex-1 min-w-0">
                          <h3 className="font-medium text-slate-900 dark:text-slate-100 truncate">{task.title}</h3>
                          {task.description && (
                            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">{task.description}</p>
                          )}
                        </div>
                        <div className="flex items-center gap-2 flex-wrap">
                          {task.priority && (
                            <Badge className={getPriorityColor(task.priority)}>{task.priority}</Badge>
                          )}
                          {task.deadline_at && (
                            <Badge variant={new Date(task.deadline_at) < new Date() ? 'destructive' : 'warning'}>
                              {formatDate(task.deadline_at)}
                            </Badge>
                          )}
                          {task.estimated_minutes && (
                            <Badge variant="muted">{task.estimated_minutes} min</Badge>
                          )}
                          {task.project && (
                            <Badge variant="primary">{task.project.name}</Badge>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-1">
                      {task.status !== 'completed' && task.status !== 'cancelled' && (
                        <Button variant="ghost" size="sm" onClick={() => startFocus(task)} title="Enfocar">
                          <Flag className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Task Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <Card className="w-full max-w-md">
            <CardContent className="py-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Nueva tarea</h2>
                <Button variant="ghost" size="sm" onClick={() => setShowCreateModal(false)}>
                  <X className="h-5 w-5" />
                </Button>
              </div>
              <form onSubmit={handleCreateTask} className="space-y-4">
                <Input
                  label="Título"
                  value={newTask.title}
                  onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
                  placeholder="¿Qué necesitas hacer?"
                  required
                  autoFocus
                />
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Descripción</label>
                  <textarea
                    value={newTask.description}
                    onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
                    rows={3}
                    className="input resize-none"
                    placeholder="Detalles adicionales..."
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Prioridad</label>
                    <select
                      value={newTask.priority}
                      onChange={(e) => setNewTask({ ...newTask, priority: e.target.value as 'low' | 'medium' | 'high' | 'critical' })}
                      className="input"
                    >
                      <option value="low">Baja</option>
                      <option value="medium">Media</option>
                      <option value="high">Alta</option>
                      <option value="critical">Crítica</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Proyecto</label>
                    <select
                      value={newTask.project_id}
                      onChange={(e) => setNewTask({ ...newTask, project_id: e.target.value || '' })}
                      className="input"
                    >
                      <option value="">Sin proyecto</option>
                      {projects.map((p) => (
                        <option key={p.id} value={p.id}>{p.name}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <Button variant="secondary" type="button" onClick={() => setShowCreateModal(false)}>Cancelar</Button>
                  <Button type="submit">Crear tarea</Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}