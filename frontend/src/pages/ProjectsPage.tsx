import { useState } from 'react';
import { useTasks } from '@/hooks/useTasks';
import { Project, ProjectStatus } from '@/types/api';
import { Card, CardContent, CardHeader, CardTitle, Button, Input, Badge } from '@/components/ui';
import { Plus, FolderKanban, Edit, Trash2, CheckCircle, PauseCircle, Archive, X } from 'lucide-react';
import { formatDate, getPriorityColor } from '@/utils/formatters';
import { useI18n } from '@/i18n/I18nProvider';

const statusOptions: { value: ProjectStatus; label: string }[] = [
  { value: 'active', label: 'Activo' },
  { value: 'on_hold', label: 'En pausa' },
  { value: 'completed', label: 'Completado' },
  { value: 'archived', label: 'Archivado' },
];

export function ProjectsPage() {
  const { t } = useI18n();
  const { projects, fetchProjects, createProject, updateProject, deleteProject, getProjectProgress } = useTasks();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [newProject, setNewProject] = useState({ name: '', description: '', color: '#3B82F6' });
  const [progressMap, setProgressMap] = useState<Record<string, { total: number; completed: number }>>({});

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProject.name.trim()) return;
    try {
      await createProject(newProject);
      setShowCreateModal(false);
      setNewProject({ name: '', description: '', color: '#3B82F6' });
    } catch (err) {
      console.error('Failed to create project:', err);
    }
  };

  const handleUpdateProject = async (e: React.FormEvent, projectId: string) => {
    e.preventDefault();
    if (!editingProject) return;
    try {
      await updateProject(projectId, {
        name: editingProject.name,
        description: editingProject.description,
        color: editingProject.color,
        status: editingProject.status,
      });
      setEditingProject(null);
    } catch (err) {
      console.error('Failed to update project:', err);
    }
  };

  const handleDeleteProject = async (projectId: string) => {
    if (!confirm('¿Estás seguro de que quieres eliminar este proyecto?')) return;
    try {
      await deleteProject(projectId);
    } catch (err) {
      console.error('Failed to delete project:', err);
    }
  };

  const loadProgress = async (projectId: string) => {
    try {
      const progress = await getProjectProgress(projectId);
      setProgressMap(prev => ({ ...prev, [projectId]: { total: progress.total_tasks, completed: progress.completed_tasks } }));
    } catch (err) {
      console.error('Failed to load progress:', err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{t('pages.projects.title')}</h1>
          <p className="text-slate-500 dark:text-slate-400">{t('pages.projects.subtitle')}</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="h-4 w-4" />
          {t('pages.projects.new')}
        </Button>
      </div>

      {/* Projects Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {projects.map((project) => {
          const progress = progressMap[project.id];
          const progressPercent = progress && progress.total > 0 ? Math.round((progress.completed / progress.total) * 100) : project.progress;

          return (
            <Card key={project.id} className="h-full hover:shadow-md transition-shadow" style={{ borderLeft: `4px solid ${project.color}` }}>
              <CardContent className="p-4 h-full flex flex-col">
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-slate-900 dark:text-slate-100 truncate">{project.name}</h3>
                    {project.description && (
                      <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">{project.description}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-1">
                    <Button variant="ghost" size="sm" onClick={() => setEditingProject(project)}>
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => handleDeleteProject(project.id)} className="text-red-600 hover:text-red-700">
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                {/* Progress */}
                <div className="mb-3">
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-slate-500 dark:text-slate-400">{t('pages.projects.progress')}</span>
                    <span className="font-medium text-slate-900 dark:text-slate-100">{progressPercent}%</span>
                  </div>
                  <div className="h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-300"
                      style={{ width: `${progressPercent}%`, backgroundColor: project.color }}
                    />
                  </div>
                  {progress && (
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                      {progress.completed} de {progress.total} tareas completadas
                    </p>
                  )}
                </div>

                {/* Status */}
                <div className="flex items-center justify-between mt-auto pt-3 border-t border-slate-200 dark:border-slate-700">
                  <Badge variant={project.status === 'active' ? 'success' : project.status === 'completed' ? 'muted' : 'warning'}>
                    {statusOptions.find(s => s.value === project.status)?.label || project.status}
                  </Badge>
                  <div className="w-4 h-4 rounded-full" style={{ backgroundColor: project.color }} />
                </div>
              </CardContent>
            </Card>
          );
        })}
        
        {projects.length === 0 && (
          <Card className="col-span-full">
            <CardContent className="py-12 text-center">
              <FolderKanban className="h-12 w-12 mx-auto text-slate-300 dark:text-slate-600 mb-3" />
              <h3 className="font-medium text-slate-900 dark:text-slate-100 mb-1">{t('pages.projects.empty')}</h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">{t('pages.projects.emptyHint')}</p>
              <Button onClick={() => setShowCreateModal(true)}>
                <Plus className="h-4 w-4" />
                Crear proyecto
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Create Project Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <Card className="w-full max-w-md">
            <CardContent className="py-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">{t('pages.projects.new')}</h2>
                <Button variant="ghost" size="sm" onClick={() => setShowCreateModal(false)}>
                  <X className="h-5 w-5" />
                </Button>
              </div>
              <form onSubmit={handleCreateProject} className="space-y-4">
                <Input
                  label="Nombre"
                  value={newProject.name}
                  onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                  placeholder="Nombre del proyecto"
                  required
                  autoFocus
                />
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{t('pages.projects.fields.description')}</label>
                  <textarea
                    value={newProject.description}
                    onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                    rows={2}
                    className="input resize-none"
                    placeholder="Descripción opcional..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{t('pages.projects.fields.color')}</label>
                  <input
                    type="color"
                    value={newProject.color}
                    onChange={(e) => setNewProject({ ...newProject, color: e.target.value })}
                    className="h-10 w-full rounded-lg border border-slate-300 dark:border-slate-600 cursor-pointer"
                  />
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <Button variant="secondary" type="button" onClick={() => setShowCreateModal(false)}>{t('common.cancel')}</Button>
                  <Button type="submit">{t('pages.projects.create')}</Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Edit Project Modal */}
      {editingProject && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <Card className="w-full max-w-md">
            <CardContent className="py-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">{t('pages.projects.edit')}</h2>
                <Button variant="ghost" size="sm" onClick={() => setEditingProject(null)}>
                  <X className="h-5 w-5" />
                </Button>
              </div>
              <form onSubmit={(e) => handleUpdateProject(e, editingProject.id)} className="space-y-4">
                <Input
                  label="Nombre"
                  value={editingProject.name}
                  onChange={(e) => setEditingProject({ ...editingProject, name: e.target.value })}
                  required
                />
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Descripción</label>
                  <textarea
                    value={editingProject.description || ''}
                    onChange={(e) => setEditingProject({ ...editingProject!, description: e.target.value })}
                    rows={2}
                    className="input resize-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Color</label>
                  <input
                    type="color"
                    value={editingProject.color}
                    onChange={(e) => setEditingProject({ ...editingProject!, color: e.target.value })}
                    className="h-10 w-full rounded-lg border border-slate-300 dark:border-slate-600 cursor-pointer"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{t('pages.projects.fields.status')}</label>
                  <select
                    value={editingProject.status}
                    onChange={(e) => setEditingProject({ ...editingProject!, status: e.target.value as ProjectStatus })}
                    className="input"
                  >
                    {statusOptions.map((opt) => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <Button variant="secondary" type="button" onClick={() => setEditingProject(null)}>Cancelar</Button>
                  <Button type="submit">{t('pages.projects.saveChanges')}</Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}