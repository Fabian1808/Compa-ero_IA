import { useEffect, useState } from 'react';
import { api } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle, Button, Badge, Input } from '@/components/ui';
import { Mail, Clock, RefreshCw, Send, X, Edit, Eye, Loader2 } from 'lucide-react';
import { formatRelativeTime, formatDate } from '@/utils/formatters';

interface FollowUp {
  id: string;
  contact_email: string;
  contact_name: string | null;
  subject: string;
  sent_at: string;
  expected_reply_by: string | null;
  status: string;
  reminder_at: string | null;
  draft_response: string | null;
}

export function FollowupsPage() {
  const [followups, setFollowups] = useState<FollowUp[]>([]);
  const [loading, setLoading] = useState(false);
  const [detecting, setDetecting] = useState(false);
  const [showDraft, setShowDraft] = useState<{ id: string; draft: string } | null>(null);
  const [editingDraft, setEditingDraft] = useState<{ id: string; content: string } | null>(null);

  useEffect(() => {
    fetchFollowups();
  }, []);

  const fetchFollowups = async () => {
    setLoading(true);
    try {
      const response = await api.getFollowups();
      setFollowups(response.data || []);
    } catch (err) {
      console.error('Failed to fetch followups:', err);
    } finally {
      setLoading(false);
    }
  };

  const detectFollowups = async () => {
    setDetecting(true);
    try {
      await api.detectFollowups();
      await fetchFollowups();
    } catch (err) {
      console.error('Failed to detect followups:', err);
    } finally {
      setDetecting(false);
    }
  };

  const prepareFollowup = async (followup: FollowUp) => {
    try {
      const response = await api.prepareFollowup(followup.id);
      if (response.data?.draft) {
        setShowDraft({ id: followup.id, draft: response.data.draft.body });
        setEditingDraft({ id: followup.id, content: response.data.draft.body });
      }
    } catch (err) {
      console.error('Failed to prepare followup:', err);
    }
  };

  const saveDraft = async (followupId: string) => {
    if (!editingDraft || editingDraft.id !== followupId) return;
    try {
      // In a real app, this would update the draft in the backend
      console.log('Saving draft for', followupId, editingDraft.content);
      setEditingDraft(null);
    } catch (err) {
      console.error('Failed to save draft:', err);
    }
  };

  const dismissFollowup = async (followupId: string) => {
    try {
      await api.dismissFollowup(followupId);
      setFollowups(prev => prev.filter(f => f.id !== followupId));
    } catch (err) {
      console.error('Failed to dismiss followup:', err);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft_prepared': return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
      case 'pending': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
      case 'reminder_sent': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400';
      case 'completed': return 'bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-300';
      case 'dismissed': return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
      default: return 'bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-300';
    }
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      'pending': 'Pendiente',
      'reminder_sent': 'Recordatorio enviado',
      'draft_prepared': 'Borrador listo',
      'sent': 'Enviado',
      'completed': 'Completado',
      'dismissed': 'Descartado',
    };
    return labels[status] || status;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Seguimientos</h1>
          <p className="text-slate-500 dark:text-slate-400">Correos que necesitan respuesta</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" onClick={detectFollowups} loading={detecting}>
            <RefreshCw className="h-4 w-4" />
            Detectar seguimientos
          </Button>
        </div>
      </div>

      {followups.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Mail className="h-16 w-16 mx-auto text-slate-300 dark:text-slate-600 mb-4" />
            <h3 className="text-lg font-medium text-slate-900 dark:text-slate-100 mb-2">No hay seguimientos pendientes</h3>
            <p className="text-slate-500 dark:text-slate-400 mb-4">Todos tus correos han sido respondidos</p>
            <Button variant="secondary" onClick={detectFollowups} loading={detecting}>
              <RefreshCw className="h-4 w-4" />
              Buscar seguimientos automáticamente
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
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Asunto</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Contacto</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Enviado</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Estado</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                  {followups.map((followup) => (
                    <tr key={followup.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                      <td className="px-4 py-3">
                        <div className="font-medium text-slate-900 dark:text-slate-100 truncate max-w-xs">{followup.subject}</div>
                        <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                          {followup.expected_reply_by && (
                            <span className="text-amber-600 dark:text-amber-400">
                              Respuesta esperada: {formatDate(followup.expected_reply_by)}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="font-medium text-slate-900 dark:text-slate-100">
                          {followup.contact_name || followup.contact_email}
                        </div>
                        <div className="text-xs text-slate-500 dark:text-slate-400">{followup.contact_email}</div>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-600 dark:text-slate-400">
                        {formatRelativeTime(followup.sent_at)}
                      </td>
                      <td className="px-4 py-3">
                        <Badge className={getStatusColor(followup.status)}>
                          {getStatusLabel(followup.status)}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          {followup.status === 'draft_prepared' && (
                            <>
                              <Button variant="secondary" size="sm" onClick={() => prepareFollowup(followup)}>
                                <Send className="h-4 w-4" />
                                Enviar
                              </Button>
                            </>
                          )}
                          {followup.status === 'pending' && (
                            <Button variant="secondary" size="sm" onClick={() => prepareFollowup(followup)}>
                              <Edit className="h-4 w-4" />
                              Preparar
                            </Button>
                          )}
                          <Button variant="ghost" size="sm" onClick={() => dismissFollowup(followup.id)} className="text-red-600 hover:text-red-700">
                            <X className="h-4 w-4" />
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

      {/* Draft Modal */}
      {editingDraft && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <Card className="w-full max-w-2xl max-h-[80vh] flex flex-col">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                Borrador de seguimiento
                <Button variant="ghost" size="sm" onClick={() => setEditingDraft(null)}>
                  <X className="h-5 w-5" />
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 overflow-hidden flex flex-col">
              <textarea
                value={editingDraft.content}
                onChange={(e) => setEditingDraft({ ...editingDraft, content: e.target.value })}
                className="flex-1 input resize-none font-mono text-sm"
                rows={20}
                placeholder="Edita el borrador antes de enviar..."
              />
              <div className="flex justify-end gap-2 mt-4 pt-4 border-t border-slate-200 dark:border-slate-700">
                <Button variant="secondary" onClick={() => setEditingDraft(null)}>Cancelar</Button>
                <Button onClick={() => saveDraft(editingDraft.id)}>
                  <Send className="h-4 w-4" />
                  Guardar y enviar
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}