import { useEffect, useState } from 'react';
import { api } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle, Button, Badge, Input } from '@/components/ui';
import { Flag, Clock, CheckCircle, XCircle, Plus, Edit, Trash2, Loader2 } from 'lucide-react';
import { formatRelativeTime, formatDate } from '@/utils/formatters';

interface Commitment {
  id: string;
  description: string;
  committed_at: string;
  due_date: string | null;
  status: 'pending' | 'confirmed' | 'completed' | 'cancelled' | 'expired';
  confidence_score: number;
  source_email_id: string | null;
  related_task_id: string | null;
  created_at: string;
}

export function CommitmentsPage() {
  const [commitments, setCommitments] = useState<Commitment[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingCommitment, setEditingCommitment] = useState<Commitment | null>(null);
  const [newCommitment, setNewCommitment] = useState({ description: '', due_date: '', confidence_score: 100 });

  useEffect(() => {
    fetchCommitments();
  }, []);

  const fetchCommitments = async () => {
    setLoading(true);
    try {
      const response = await api.get('/commitments');
      setCommitments(response.data || []);
    } catch (err) {
      console.error('Failed to fetch commitments:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCommitment.description.trim()) return;
    try {
      await api.post('/commitments', {
        description: newCommitment.description,
        due_date: newCommitment.due_date || null,
        confidence_score: newCommitment.confidence_score,
      });
      setShowCreateModal(false);
      setNewCommitment({ description: '', due_date: '', confidence_score: 100 });
      fetchCommitments();
    } catch (err) {
      console.error('Failed to create commitment:', err);
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingCommitment) return;
    try {
      await api.patch(`/commitments/${editingCommitment.id}`, {
        description: editingCommitment.description,
        due_date: editingCommitment.due_date || null,
        status: editingCommitment.status,
      });
      setEditingCommitment(null);
      fetchCommitments();
    } catch (err) {
      console.error('Failed to update commitment:', err);
    }
  };

  const completeCommitment = async (id: string) => {
    try {
      await api.post(`/commitments/${id}/complete`);
      fetchCommitments();
    } catch (err) {
      console.error('Failed to complete commitment:', err);
    }
  };

  const deleteCommitment = async (id: string) => {
    if (!confirm('¿Eliminar este compromiso?')) return;
    try {
      await api.delete(`/commitments/${id}`);
      fetchCommitments();
    } catch (err) {
      console.error('Failed to delete commitment:', err);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
      case 'confirmed': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400';
      case 'completed': return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
      case 'cancelled': return 'bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-300';
      case 'expired': return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
      default: return 'bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-300';
    }
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      'pending': 'Pendiente',
      'confirmed': 'Confirmado',
      'completed': 'Completado',
      'cancelled': 'Cancelado',
      'expired': 'Expirado',
    };
    return labels[status] || status;
  };

  const isOverdue = (dueDate: string | null) => {
    if (!dueDate) return false;
    return new Date(dueDate) < new Date();
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Compromisos</h1>
          <p className="text-slate-500 dark:text-slate-400">Tus promesas y compromisos adquiridos</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="h-4 w-4" />
          Nuevo compromiso
        </Button>
      </div>

      {commitments.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Flag className="h-16 w-16 mx-auto text-slate-300 dark:text-slate-600 mb-4" />
            <h3 className="text-lg font-medium text-slate-900 dark:text-slate-100 mb-2">No hay compromisos</h3>
            <p className="text-slate-500 dark:text-slate-400 mb-4">Registra tus promesas para no olvidarlas</p>
            <Button onClick={() => setShowCreateModal(true)}>
              <Plus className="h-4 w-4" />
              Crear primer compromiso
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Compromiso</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Fecha límite</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Estado</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Confianza</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                  {commitments.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                      <td className="px-4 py-3">
                        <div className="font-medium text-slate-900 dark:text-slate-100">{c.description}</div>
                        <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                          Creado {formatRelativeTime(c.committed_at)}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        {c.due_date ? (
                          <div className={`font-medium ${isOverdue(c.due_date) ? 'text-red-600 dark:text-red-400' : 'text-slate-900 dark:text-slate-100'}`}>
                            {formatDate(c.due_date)}
                            {isOverdue(c.due_date) && <span className="ml-2 text-red-600 dark:text-red-400">(Vencido)</span>}
                          </div>
                        ) : (
                          <span className="text-slate-400 dark:text-slate-500">Sin fecha</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <Badge className={getStatusColor(c.status)}>{getStatusLabel(c.status)}</Badge>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-600 dark:text-slate-400">{c.confidence_score}%</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          {c.status !== 'completed' && c.status !== 'cancelled' && (
                            <Button variant="secondary" size="sm" onClick={() => completeCommitment(c.id)}>
                              <CheckCircle className="h-4 w-4" />
                            </Button>
                          )}
                          <Button variant="ghost" size="sm" onClick={() => setEditingCommitment(c)}>
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => deleteCommitment(c.id)} className="text-red-600 hover:text-red-700">
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Create/Edit Modal */}
      {(showCreateModal || editingCommitment) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <Card className="w-full max-w-md">
            <CardContent className="py-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">{editingCommitment ? 'Editar compromiso' : 'Nuevo compromiso'}</h2>
                <Button variant="ghost" size="sm" onClick={() => { setShowCreateModal(false); setEditingCommitment(null); }}>
                  <X className="h-5 w-5" />
                </Button>
              </div>
              <form onSubmit={editingCommitment ? handleUpdate : handleCreate} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Compromiso</label>
                  <textarea
                    value={editingCommitment?.description || newCommitment.description}
                    onChange={(e) => editingCommitment 
                      ? setEditingCommitment({ ...editingCommitment, description: e.target.value })
                      : setNewCommitment({ ...newCommitment, description: e.target.value })}
                    rows={3}
                    className="input resize-none"
                    placeholder="¿Qué te comprometiste a hacer?"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Fecha límite</label>
                  <Input
                    type="date"
                    value={editingCommitment?.due_date || newCommitment.due_date}
                    onChange={(e) => editingCommitment
                      ? setEditingCommitment({ ...editingCommitment, due_date: e.target.value })
                      : setNewCommitment({ ...newCommitment, due_date: e.target.value })}
                    min={new Date().toISOString().split('T')[0]}
                  />
                </div>
                {editingCommitment && (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Estado</label>
                    <select
                      value={editingCommitment.status}
                      onChange={(e) => setEditingCommitment({ ...editingCommitment, status: e.target.value as any })}
                      className="input"
                    >
                      <option value="pending">Pendiente</option>
                      <option value="confirmed">Confirmado</option>
                      <option value="completed">Completado</option>
                      <option value="cancelled">Cancelado</option>
                    </select>
                  </div>
                )} 
                <div className="flex justify-end gap-2 pt-2">
                  <Button variant="secondary" type="button" onClick={() => { setShowCreateModal(false); setEditingCommitment(null); }}>Cancelar</Button>
                  <Button type="submit">{editingCommitment ? 'Guardar' : 'Crear'}</Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}