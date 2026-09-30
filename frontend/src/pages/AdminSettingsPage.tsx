import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, Input, Button, Badge, Select, SelectTrigger, SelectValue, SelectContent, SelectItem, Tabs, TabsList, TabsTrigger, TabsContent, Label, Switch, Textarea, Separator } from '@/components/ui';
import { 
  Settings, Save, Loader2, CheckCircle, AlertCircle,
  Brain, Database, Shield, Bell, Globe, Palette, Workflow
} from 'lucide-react';
import { api } from '@/services/api';

export function AdminSettingsPage() {
  const [settings, setSettings] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [selectedTenant, setSelectedTenant] = useState<string>('');

  const fetchSettings = async () => {
    if (!selectedTenant) {
      setSettings({});
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const data = await api.getTenantSettings(selectedTenant);
      setSettings(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al cargar configuración');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, [selectedTenant]);

  const handleSave = async (section: string, data: any) => {
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await api.updateTenantSettings(selectedTenant, data);
      setSettings(prev => ({ ...prev, ...data }));
      setSuccess('Configuración guardada correctamente');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al guardar');
    } finally {
      setSaving(false);
    }
  };

  const updateField = (section: string, field: string, value: any) => {
    const newSettings = { ...settings, [field]: value };
    setSettings(newSettings);
  };

  if (!selectedTenant) {
    return (
      <div className="max-w-7xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Configuración</h1>
          <p className="text-slate-500 dark:text-slate-400">Configuración del sistema por tenant</p>
        </div>
        <Card>
          <CardContent className="py-12 text-center">
            <Settings className="h-12 w-12 mx-auto text-slate-300 dark:text-slate-600 mb-3" />
            <p className="text-slate-500 dark:text-slate-400">Selecciona un tenant para gestionar su configuración</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Configuración</h1>
          <p className="text-slate-500 dark:text-slate-400">Configuración del tenant: {selectedTenant}</p>
        </div>
        <Button onClick={fetchSettings} disabled={loading} variant="outline">
          <Loader2 className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Recargar
        </Button>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 text-red-700 dark:text-red-300 text-sm flex items-center justify-between">
          <span>{error}</span>
          <Button variant="ghost" size="sm" onClick={() => setError(null)}><AlertCircle className="h-4 w-4" /></Button>
        </div>
      )}
      {success && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3 text-green-700 dark:text-green-300 text-sm flex items-center justify-between">
          <span>{success}</span>
          <Button variant="ghost" size="sm" onClick={() => setSuccess(null)}><CheckCircle className="h-4 w-4" /></Button>
        </div>
      )}

      <Tabs defaultValue="ai" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="ai"><Brain className="h-4 w-4 mr-2" />IA</TabsTrigger>
          <TabsTrigger value="data"><Database className="h-4 w-4 mr-2" />Datos</TabsTrigger>
          <TabsTrigger value="security"><Shield className="h-4 w-4 mr-2" />Seguridad</TabsTrigger>
          <TabsTrigger value="notifications"><Bell className="h-4 w-4 mr-2" />Notificaciones</TabsTrigger>
        </TabsList>

        <TabsContent value="ai" className="space-y-6">
          <Card>
            <CardHeader><CardTitle>Configuración de IA</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label>Proveedor IA</Label>
                  <Select value={settings.ai_provider || 'ollama'} onValueChange={v => updateField('ai', 'ai_provider', v)}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ollama">Ollama (Local)</SelectItem>
                      <SelectItem value="openai">OpenAI</SelectItem>
                      <SelectItem value="azure_openai">Azure OpenAI</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label>Modelo Chat</Label>
                  <Input value={settings.ai_chat_model || 'phi3:3.8b'} onChange={e => updateField('ai', 'ai_chat_model', e.target.value)} />
                </div>
                <div className="space-y-1.5">
                  <Label>Modelo Embeddings</Label>
                  <Input value={settings.ai_embed_model || 'nomic-embed-text'} onChange={e => updateField('ai', 'ai_embed_model', e.target.value)} />
                </div>
                <div className="space-y-1.5">
                  <Label>Temperatura</Label>
                  <Input type="number" step="0.1" min="0" max="2" value={settings.ai_temperature || 0.1} onChange={e => updateField('ai', 'ai_temperature', parseFloat(e.target.value))} />
                </div>
                <div className="space-y-1.5">
                  <Label>Max Tokens</Label>
                  <Input type="number" min="1" max="8192" value={settings.ai_max_tokens || 2048} onChange={e => updateField('ai', 'ai_max_tokens', parseInt(e.target.value))} />
                </div>
                <div className="space-y-1.5">
                  <Label>Confianza Auto-crear (%)</Label>
                  <Input type="number" min="0" max="100" value={settings.ai_confidence_auto_create || 95} onChange={e => updateField('ai', 'ai_confidence_auto_create', parseInt(e.target.value))} />
                </div>
                <div className="space-y-1.5">
                  <Label>Confianza Sugerir (%)</Label>
                  <Input type="number" min="0" max="100" value={settings.ai_confidence_suggest || 80} onChange={e => updateField('ai', 'ai_confidence_suggest', parseInt(e.target.value))} />
                </div>
              </div>
              <Button onClick={() => handleSave('ai', { 
                ai_provider: settings.ai_provider,
                ai_chat_model: settings.ai_chat_model,
                ai_embed_model: settings.ai_embed_model,
                ai_temperature: settings.ai_temperature,
                ai_max_tokens: settings.ai_max_tokens,
                ai_confidence_auto_create: settings.ai_confidence_auto_create,
                ai_confidence_suggest: settings.ai_confidence_suggest,
              })} disabled={saving}>
                {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null} Guardar IA
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="data" className="space-y-6">
          <Card>
            <CardHeader><CardTitle>Retención de Datos</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-3">
                <div className="space-y-1.5">
                  <Label>Emails (días)</Label>
                  <Input type="number" min="1" value={settings.email_retention_days || 365} onChange={e => updateField('data', 'email_retention_days', parseInt(e.target.value))} />
                </div>
                <div className="space-y-1.5">
                  <Label>Tareas (días)</Label>
                  <Input type="number" min="1" value={settings.task_retention_days || 1095} onChange={e => updateField('data', 'task_retention_days', parseInt(e.target.value))} />
                </div>
                <div className="space-y-1.5">
                  <Label>Audit Logs (días)</Label>
                  <Input type="number" min="1" value={settings.audit_log_retention_days || 2555} onChange={e => updateField('data', 'audit_log_retention_days', parseInt(e.target.value))} />
                </div>
                <div className="space-y-1.5">
                  <Label>Adjuntos (días)</Label>
                  <Input type="number" min="1" value={settings.attachment_retention_days || 365} onChange={e => updateField('data', 'attachment_retention_days', parseInt(e.target.value))} />
                </div>
              </div>
              <Button onClick={() => handleSave('data', {
                email_retention_days: settings.email_retention_days,
                task_retention_days: settings.task_retention_days,
                audit_log_retention_days: settings.audit_log_retention_days,
                attachment_retention_days: settings.attachment_retention_days,
              })} disabled={saving}>
                {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null} Guardar Retención
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="space-y-6">
          <Card>
            <CardHeader><CardTitle>Seguridad</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Label>Requerir MFA</Label>
                    <p className="text-sm text-slate-500">Autenticación de dos factores obligatoria</p>
                  </div>
                  <Switch checked={settings.require_mfa || false} onCheckedChange={v => updateField('security', 'require_mfa', v)} />
                </div>
                <div className="space-y-1.5">
                  <Label>Timeout de sesión (minutos)</Label>
                  <Input type="number" min="5" max="1440" value={settings.session_timeout_minutes || 480} onChange={e => updateField('security', 'session_timeout_minutes', parseInt(e.target.value))} />
                </div>
                <div className="space-y-1.5">
                  <Label>Longitud mínima de contraseña</Label>
                  <Input type="number" min="6" max="128" value={settings.password_min_length || 8} onChange={e => updateField('security', 'password_min_length', parseInt(e.target.value))} />
                </div>
                <div className="space-y-1.5">
                  <Label>Dominios permitidos (JSON array)</Label>
                  <Textarea value={settings.allowed_domains_json || '[]'} onChange={e => updateField('security', 'allowed_domains_json', e.target.value)} rows={3} placeholder='["empresa.com", "otro.com"]' />
                </div>
                <div className="space-y-1.5">
                  <Label>IP Whitelist (JSON array)</Label>
                  <Textarea value={settings.ip_whitelist_json || '[]'} onChange={e => updateField('security', 'ip_whitelist_json', e.target.value)} rows={3} placeholder='["192.168.1.0/24", "10.0.0.1"]' />
                </div>
              </div>
              <Button onClick={() => handleSave('security', {
                require_mfa: settings.require_mfa,
                session_timeout_minutes: settings.session_timeout_minutes,
                password_min_length: settings.password_min_length,
                allowed_domains_json: settings.allowed_domains_json,
                ip_whitelist_json: settings.ip_whitelist_json,
              })} disabled={saving}>
                {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null} Guardar Seguridad
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications" className="space-y-6">
          <Card>
            <CardHeader><CardTitle>Notificaciones</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label>Briefing Diario</Label>
                  <div className="flex items-center gap-4">
                    <Switch checked={settings.daily_briefing_enabled || true} onCheckedChange={v => updateField('notifications', 'daily_briefing_enabled', v)} />
                    <Input type="number" min="0" max="23" value={settings.daily_briefing_hour || 8} onChange={e => updateField('notifications', 'daily_briefing_hour', parseInt(e.target.value))} className="w-24" placeholder="Hora (0-23)" />
                  </div>
                </div>
                <div className="space-y-1.5">
                  <Label>Fin de Día</Label>
                  <div className="flex items-center gap-4">
                    <Switch checked={settings.end_of_day_enabled || true} onCheckedChange={v => updateField('notifications', 'end_of_day_enabled', v)} />
                    <Input type="number" min="0" max="23" value={settings.end_of_day_hour || 18} onChange={e => updateField('notifications', 'end_of_day_hour', parseInt(e.target.value))} className="w-24" placeholder="Hora (0-23)" />
                  </div>
                </div>
              </div>
              <Button onClick={() => handleSave('notifications', {
                daily_briefing_enabled: settings.daily_briefing_enabled,
                daily_briefing_hour: settings.daily_briefing_hour,
                end_of_day_enabled: settings.end_of_day_enabled,
                end_of_day_hour: settings.end_of_day_hour,
              })} disabled={saving}>
                {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null} Guardar Notificaciones
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}