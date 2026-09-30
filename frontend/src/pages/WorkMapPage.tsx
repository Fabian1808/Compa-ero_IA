import { useState, useEffect } from 'react';
import { Card, CardContent, Badge, Tabs, TabsList, TabsTrigger, Accordion, AccordionItem, AccordionTrigger, AccordionContent, Button, Separator } from '@/components/ui';
import { 
  FolderKanban, CheckSquare, Flag, Calendar, AlertTriangle, 
  TrendingUp, TrendingDown, Clock, Target, GitBranch,
  ChevronDown, ChevronRight, AlertCircle, PlayCircle, PauseCircle
} from 'lucide-react';
import { api } from '@/services/api';

interface WorkMapNode {
  id: string;
  type: 'project' | 'task' | 'commitment' | 'meeting';
  label: string;
  data: any;
  position: { x: number; y: number };
  parent?: string;
}

interface WorkMapEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  label: string;
  style?: any;
}

interface Bottleneck {
  type: string;
  impact: string;
  suggested_action: string;
  [key: string]: any;
}

interface WorkMapData {
  nodes: WorkMapNode[];
  edges: WorkMapEdge[];
  bottlenecks: Bottleneck[];
  stats: any;
}

export function WorkMapPage() {
  const [data, setData] = useState<WorkMapData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'projects' | 'bottlenecks' | 'timeline'>('overview');
  const [expandedProjects, setExpandedProjects] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadWorkMap();
  }, []);

  const loadWorkMap = async () => {
    try {
      const result = await api.get('/workmap');
      setData(result);
    } catch (err) {
      console.error('Failed to load work map', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleProject = (projectId: string) => {
    const newExpanded = new Set(expandedProjects);
    if (newExpanded.has(projectId)) {
      newExpanded.delete(projectId);
    } else {
      newExpanded.add(projectId);
    }
    setExpandedProjects(newExpanded);
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto py-12 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent mx-auto mb-4" />
        <p className="text-slate-500 dark:text-slate-400">Cargando mapa de trabajo...</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="max-w-7xl mx-auto py-12 text-center">
        <AlertCircle className="h-12 w-12 mx-auto text-slate-300 dark:text-slate-600 mb-4" />
        <p className="text-slate-500 dark:text-slate-400">No se pudo cargar el mapa de trabajo</p>
      </div>
    );
  }

  const { nodes, edges, bottlenecks, stats } = data;
  const projects = nodes.filter(n => n.type === 'project');
  const tasks = nodes.filter(n => n.type === 'task');
  const commitments = nodes.filter(n => n.type === 'commitment');
  const meetings = nodes.filter(n => n.type === 'meeting');

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      completed: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
      pending: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
      in_progress: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
      blocked: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
      cancelled: 'bg-slate-100 text-slate-500 dark:bg-slate-700 dark:text-slate-400',
    };
    return colors[status] || colors.pending;
  };

  const getPriorityColor = (priority: string) => {
    const colors: Record<string, string> = {
      critical: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
      high: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
      medium: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
      low: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    };
    return colors[priority] || colors.medium;
  };

  const getUrgencyColor = (urgency: string) => {
    const colors: Record<string, string> = {
      critical: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
      high: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
      medium: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
      low: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      none: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
    };
    return colors[urgency] || colors.none;
  };

  const getUrgencyIcon = (urgency: string) => {
    switch (urgency) {
      case 'critical': return <AlertTriangle className="h-3 w-3 text-red-500" />;
      case 'high': return <Target className="h-3 w-3 text-orange-500" />;
      case 'medium': return <Clock className="h-3 w-3 text-yellow-500" />;
      case 'low': return <TrendingUp className="h-3 w-3 text-green-500" />;
      default: return <ChevronRight className="h-3 w-3 text-slate-400" />;
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Mapa de Trabajo</h1>
          <p className="text-slate-500 dark:text-slate-400">Visualización de proyectos, tareas, compromisos y cuellos de botella</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={loadWorkMap}>
            <TrendingUp className="h-4 w-4 mr-2" />
            Actualizar
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
        <StatCard icon={FolderKanban} label="Proyectos" value={stats.total_projects} sublabel={`${stats.active_projects} activos`} color="blue" />
        <StatCard icon={CheckSquare} label="Tareas" value={stats.total_tasks} sublabel={`${stats.pending_tasks} pendientes`} color="purple" />
        <StatCard icon={AlertCircle} label="Bloqueadas" value={stats.blocked_tasks} sublabel={`${stats.overdue_tasks} vencidas`} color="red" />
        <StatCard icon={Flag} label="Compromisos" value={stats.pending_commitments} sublabel="pendientes" color="amber" />
        <StatCard icon={Calendar} label="Reuniones" value={stats.upcoming_meetings} sublabel="próximos 7 días" color="blue" />
        <StatCard icon={AlertTriangle} label="Cuellos botella" value={stats.bottlenecks_count} sublabel="detectados" color="red" />
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Resumen</TabsTrigger>
          <TabsTrigger value="projects">Proyectos</TabsTrigger>
          <TabsTrigger value="bottlenecks">Cuellos de Botella</TabsTrigger>
          <TabsTrigger value="timeline">Próximos 7 días</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Upcoming Critical Items */}
          <Card>
            <CardContent className="pt-6">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">Próximos elementos críticos</h3>
              <div className="space-y-3">
                {[
                  ...tasks
                    .filter(t => t.data.urgency === 'critical' || t.data.urgency === 'high')
                    .sort((a, b) => {
                      const urgencyOrder = { critical: 0, high: 1, medium: 2, low: 3, none: 4 };
                      return urgencyOrder[a.data.urgency] - urgencyOrder[b.data.urgency];
                    })
                    .slice(0, 5)
                    .map(t => (
                      <TaskRow key={t.id} task={t} />
                    )),
                  ...commitments
                    .filter(c => {
                      if (!c.data.due_date) return false;
                      const days = (new Date(c.data.due_date).getTime() - Date.now()) / (1000 * 60 * 60 * 24);
                      return days <= 3;
                    })
                    .slice(0, 3)
                    .map(c => (
                      <CommitmentRow key={c.id} commitment={c} />
                    )),
                ]}
              </div>
            </CardContent>
          </Card>

          {/* Project Progress */}
          {projects.length > 0 && (
            <Card>
              <CardContent className="pt-6">
                <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">Progreso de proyectos</h3>
                <div className="space-y-4">
                  {projects.map(p => (
                    <ProjectProgressRow key={p.id} project={p} />
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Projects Tab */}
        <TabsContent value="projects" className="space-y-4">
          {projects.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <FolderKanban className="h-12 w-12 mx-auto text-slate-300 dark:text-slate-600 mb-3" />
                <p className="text-slate-500 dark:text-slate-400">No hay proyectos aún</p>
              </CardContent>
            </Card>
          ) : (
            projects.map(project => {
              const projectTasks = tasks.filter(t => t.data.project_id === project.id);
              const isExpanded = expandedProjects.has(project.id);
              return (
                <Card key={project.id} className="overflow-hidden">
                  <div className="p-4 border-b border-slate-200 dark:border-slate-700">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => toggleProject(project.id)}
                          className="p-1"
                        >
                          {isExpanded ? <ChevronDown className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
                        </Button>
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: project.data.color }} />
                        <div>
                          <h4 className="font-medium text-slate-900 dark:text-slate-100">{project.data.name}</h4>
                          <p className="text-sm text-slate-500 dark:text-slate-400">
                            {project.data.task_count} tareas • {project.data.completed_count} completadas • {project.data.progress}%
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={project.data.status === 'active' ? 'default' : 'secondary'}>
                          {project.data.status}
                        </Badge>
                        <div className="w-24 h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary-500 transition-all duration-300"
                            style={{ width: `${project.data.progress}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                          {project.data.progress}%
                        </span>
                      </div>
                    </div>
                  </div>
                  {isExpanded && (
                    <div className="p-4 space-y-2">
                      {projectTasks.length === 0 ? (
                        <p className="text-slate-500 dark:text-slate-400 text-center py-4">Sin tareas en este proyecto</p>
                      ) : (
                        projectTasks.map(task => (
                          <TaskRow key={task.id} task={task} compact />
                        ))
                      )}
                    </div>
                  )}
                </Card>
              );
            })
          )}
        </TabsContent>

        {/* Bottlenecks Tab */}
        <TabsContent value="bottlenecks" className="space-y-4">
          {bottlenecks.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <TrendingUp className="h-12 w-12 mx-auto text-green-500 mb-3" />
                <h3 className="text-lg font-medium text-slate-900 dark:text-slate-100 mb-1">¡Sin cuellos de botella!</h3>
                <p className="text-slate-500 dark:text-slate-400">Tu trabajo fluye sin obstáculos detectados</p>
              </CardContent>
            </Card>
          ) : (
            bottlenecks.map((bottleneck, index) => (
              <Card key={index} className="border-l-4 border-red-500">
                <CardContent className="pt-6">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="destructive">{bottleneck.impact?.toUpperCase() || 'ALTO'}</Badge>
                        <Badge variant="outline" className="text-xs">{bottleneck.type.replace(/_/g, ' ')}</Badge>
                      </div>
                      <p className="font-medium text-slate-900 dark:text-slate-100 mb-2">
                        {bottleneck.suggested_action}
                      </p>
                      {bottleneck.task_title && (
                        <p className="text-sm text-slate-600 dark:text-slate-400">
                          Tarea bloqueante: <span className="font-medium">{bottleneck.task_title}</span>
                        </p>
                      )}
                      {bottleneck.downstream_tasks && (
                        <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                          Bloquea: {bottleneck.downstream_tasks.join(', ')}
                        </p>
                      )}
                      {bottleneck.affected_tasks && (
                        <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                          Tareas afectadas: {bottleneck.affected_tasks.join(', ')}
                        </p>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        {/* Timeline Tab */}
        <TabsContent value="timeline" className="space-y-6">
          {/* Upcoming Meetings */}
          {meetings.length > 0 && (
            <Card>
              <CardContent className="pt-6">
                <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">Reuniones próximas</h3>
                <div className="space-y-2">
                  {meetings
                    .sort((a, b) => new Date(a.data.start_at).getTime() - new Date(b.data.start_at).getTime())
                    .map(m => (
                      <MeetingRow key={m.id} meeting={m} />
                    ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Upcoming Deadlines */}
          <Card>
            <CardContent className="pt-6">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">Próximos vencimientos</h3>
              <div className="space-y-2">
                {[
                  ...tasks
                    .filter(t => t.data.deadline && t.data.status !== 'completed')
                    .sort((a, b) => new Date(a.data.deadline).getTime() - new Date(b.data.deadline).getTime())
                    .slice(0, 10)
                    .map(t => (
                      <DeadlineRow key={t.id} item={t} type="task" />
                    )),
                  ...commitments
                    .filter(c => c.data.due_date)
                    .sort((a, b) => new Date(a.data.due_date).getTime() - new Date(b.data.due_date).getTime())
                    .slice(0, 5)
                    .map(c => (
                      <DeadlineRow key={c.id} item={c} type="commitment" />
                    )),
                ]}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

// Helper Components
function StatCard({ icon: Icon, label, value, sublabel, color }: any) {
  const colors: Record<string, string> = {
    blue: 'bg-blue-500',
    purple: 'bg-purple-500',
    red: 'bg-red-500',
    amber: 'bg-amber-500',
    green: 'bg-green-500',
  };

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-500 dark:text-slate-400">{label}</p>
            <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">{value}</p>
            <p className="text-xs text-slate-400 dark:text-slate-500">{sublabel}</p>
          </div>
          <div className={`w-12 h-12 rounded-xl ${colors[color]} flex items-center justify-center`}>
            <Icon className="h-6 w-6 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function TaskRow({ task, compact }: { task: WorkMapNode; compact?: boolean }) {
  const t = task.data;
  return (
    <div className={`flex items-center gap-3 p-2 rounded-lg ${compact ? '' : 'hover:bg-slate-50 dark:hover:bg-slate-800'}`}>
      <Badge variant="outline" className={getPriorityColor(t.priority)}>
        {t.priority}
      </Badge>
      <Badge variant="outline" className={getUrgencyColor(t.urgency)}>
        {getUrgencyIcon(t.urgency)}
        {t.urgency}
      </Badge>
      <Badge variant="outline" className={getStatusColor(t.status)}>
        {t.status}
      </Badge>
      <div className="flex-1 min-w-0">
        <p className={`text-sm font-medium ${t.is_overdue ? 'text-red-600 dark:text-red-400' : 'text-slate-900 dark:text-slate-100'} truncate`}>
          {t.title}
        </p>
        {t.deadline && (
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Vence: {new Date(t.deadline).toLocaleDateString()}
          </p>
        )}
      </div>
      {t.estimated_minutes && (
        <span className="text-xs text-slate-500 dark:text-slate-400">
          {t.estimated_minutes}min
        </span>
      )}
    </div>
  );
}

function CommitmentRow({ commitment }: { commitment: WorkMapNode }) {
  const c = commitment.data;
  const daysLeft = c.due_date ? Math.ceil((new Date(c.due_date).getTime() - Date.now()) / (1000 * 60 * 60 * 24)) : 999;
  return (
    <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800">
      <Flag className="h-5 w-5 text-amber-500" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-slate-900 dark:text-slate-100 truncate">{c.description}</p>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          {c.due_date ? `Vence en ${daysLeft} día${daysLeft !== 1 ? 's' : ''}` : 'Sin fecha'}
        </p>
      </div>
      <Badge variant={daysLeft <= 1 ? 'destructive' : daysLeft <= 3 ? 'default' : 'secondary'}>
        {c.status}
      </Badge>
    </div>
  );
}

function MeetingRow({ meeting }: { meeting: WorkMapNode }) {
  const m = meeting.data;
  return (
    <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800">
      <Calendar className="h-5 w-5 text-blue-500" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-slate-900 dark:text-slate-100 truncate">{m.subject}</p>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          {new Date(m.start_at).toLocaleString()} • {m.hours_until}h
        </p>
      </div>
      {m.is_online && <Badge variant="outline" className="text-xs"><PlayCircle className="h-3 w-3 mr-1" />Online</Badge>}
    </div>
  );
}

function DeadlineRow({ item, type }: { item: WorkMapNode; type: 'task' | 'commitment' }) {
  const d = item.data;
  const date = type === 'task' ? d.deadline : d.due_date;
  const daysLeft = date ? Math.ceil((new Date(date).getTime() - Date.now()) / (1000 * 60 * 60 * 24)) : 999;
  return (
    <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800">
      {type === 'task' ? <CheckSquare className="h-5 w-5 text-purple-500" /> : <Flag className="h-5 w-5 text-amber-500" />}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-slate-900 dark:text-slate-100 truncate">
          {type === 'task' ? d.title : d.description}
        </p>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          {date ? new Date(date).toLocaleDateString() : 'Sin fecha'}
        </p>
      </div>
      <Badge variant={daysLeft <= 0 ? 'destructive' : daysLeft <= 1 ? 'default' : daysLeft <= 3 ? 'secondary' : 'outline'}>
        {daysLeft <= 0 ? 'Vencido' : daysLeft === 1 ? 'Mañana' : `${daysLeft}d`}
      </Badge>
    </div>
  );
}

function ProjectProgressRow({ project }: { project: WorkMapNode }) {
  const p = project.data;
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: p.color }} />
          <span className="font-medium text-slate-900 dark:text-slate-100">{p.name}</span>
          <Badge variant="outline" className={getStatusColor(p.status)}>{p.status}</Badge>
        </div>
        <span className="text-sm font-medium text-slate-600 dark:text-slate-400">{p.progress}%</span>
      </div>
      <div className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
        <div
          className="h-full bg-primary-500 transition-all duration-300"
          style={{ width: `${p.progress}%` }}
        />
      </div>
      <p className="text-xs text-slate-500 dark:text-slate-400">
        {p.completed_count}/{p.task_count} tareas • {p.task_count - p.completed_count} pendientes
      </p>
    </div>
  );
}

// Add missing import
import { TabsContent } from '@/components/ui';