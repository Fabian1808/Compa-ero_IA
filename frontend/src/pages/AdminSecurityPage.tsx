import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, Tabs, TabsList, TabsTrigger, TabsContent, Badge, Select, SelectTrigger, SelectValue, SelectContent, SelectItem, Input, Button, Switch, Label, Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui';
import { 
  Shield, Lock, Key, UserCheck, AlertTriangle, 
  Loader2, CheckCircle, XCircle, Eye, EyeOff,
  Fingerprint, Smartphone, Globe
} from 'lucide-react';
import { api } from '@/services/api';

interface SecuritySettings {
  require_mfa: boolean;
  session_timeout_minutes: number;
  password_min_length: number;
  allowed_domains: string[];
  ip_whitelist: string[];
}

export function AdminSecurityPage() {
  const [settings, setSettings] = useState<SecuritySettings>({
    require_mfa: false,
    session_timeout_minutes: 480,
    password_min_length: 8,
    allowed_domains: [],
    ip_whitelist: [],
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [selectedTenant, setSelectedTenant] = useState<string>('');

  const fetchSettings = async () => {
    if (!selectedTenant) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const data = await api.getTenantSettings(selectedTenant);
      setSettings({
        require_mfa: data.require_mfa || false,
        session_timeout_minutes: data.session_timeout_minutes || 480,
        password_min_length: data.password_min_length || 8,
        allowed_domains: JSON.parse(data.allowed_domains_json || '[]'),
        ip_whitelist: JSON.parse(data.ip_whitelist_json || '[]'),
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al cargar configuración');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, [selectedTenant]);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await api.updateTenantSettings(selectedTenant, {
        require_mfa: settings.require_mfa,
        session_timeout_minutes: settings.session_timeout_minutes,
        password_min_length: settings.password_min_length,
        allowed_domains_json: JSON.stringify(settings.allowed_domains),
        ip_whitelist_json: JSON.stringify(settings.ip_whitelist),
      });
      setSuccess('Configuración de seguridad guardada');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al guardar');
    } finally {
      setSaving(false);
    }
  };

  const addDomain = () => {
    const newDomain = prompt('Nuevo dominio permitido (ej: empresa.com):');
    if (newDomain && newDomain.trim()) {
      setSettings(prev => ({ ...prev, allowed_domains: [...prev.allowed_domains, newDomain.trim()] }));
    }
  };

  const removeDomain = (domain: string) => {
    setSettings(prev => ({ ...prev, allowed_domains: prev.allowed_domains.filter(d => d !== domain) }));
  };

  const addIp = () => {
    const newIp = prompt('Nueva IP/CIDR (ej: 192.168.1.0/24):');
    if (newIp && newIp.trim()) {
      setSettings(prev => ({ ...prev, ip_whitelist: [...prev.ip_whitelist, newIp.trim()] }));
    }
  };

  const removeIp = (ip: string) => {
    setSettings(prev => ({ ...prev, ip_whitelist: prev.ip_whitelist.filter(i => i !== ip) }));
  };

  if (!selectedTenant) {
    return (
      <div className="max-w-7xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Seguridad</h1>
          <p className="text-slate-500 dark:text-slate-400">Configuración de seguridad por tenant</p>
        </div>
        <Card>
          <CardContent className="py-12 text-center">
            <Shield className="h-12 w-12 mx-auto text-slate-300 dark:text-slate-600 mb-3" />
            <p className="text-slate-500 dark:text-slate-400">Selecciona un tenant para gestionar su seguridad</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Seguridad</h1>
          <p className="text-slate-500 dark:text-slate-400">Configuración de seguridad y acceso</p>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 text-red-700 dark:text-red-300 text-sm">
          {error}
        </div>
      )}
      {success && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3 text-green-700 dark:text-green-300 text-sm">
          {success}
        </div>
      )}

      <Tabs defaultValue="access" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="access"><Lock className="h-4 w-4 mr-2" />Acceso</TabsTrigger>
          <TabsTrigger value="domains"><Globe className="h-4 w-4 mr-2" />Dominios</TabsTrigger>
          <TabsTrigger value="network"><Smartphone className="h-4 w-4 mr-2" />Red</TabsTrigger>
        </TabsList>

        <TabsContent value="access" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Autenticación</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label>Requerir MFA (Autenticación de dos factores)</Label>
                  <p className="text-sm text-slate-500">Obliga a todos los usuarios a usar 2FA</p>
                </div>
                <Switch checked={settings.require_mfa} onCheckedChange={v => setSettings(prev => ({ ...prev, require_mfa: v }))} />
              </div>

              <div className="space-y-2">
                <Label>Timeout de sesión (minutos)</Label>
                <Input type="number" min="5" max="1440" value={settings.session_timeout_minutes} onChange={e => setSettings(prev => ({ ...prev, session_timeout_minutes: parseInt(e.target.value) || 480 }))} />
              </div>

              <div className="space-y-2">
                <Label>Longitud mínima de contraseña</Label>
                <Input type="number" min="6" max="128" value={settings.password_min_length} onChange={e => setSettings(prev => ({ ...prev, password_min_length: parseInt(e.target.value) || 8 }))} />
              </div>

              <Button onClick={handleSave} disabled={saving}>
                {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null} Guardar Acceso
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="domains" className="space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Dominios Permitidos</CardTitle>
              <Button variant="outline" size="sm" onClick={addDomain}>
                <span className="text-sm">+ Agregar Dominio</span>
              </Button>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-500 mb-4">Solo se permitirán usuarios con emails de estos dominios</p>
              {settings.allowed_domains.length === 0 ? (
                <p className="text-slate-500 text-center py-8">No hay dominios configurados (todos permitidos)</p>
              ) : (
                <ul className="space-y-2">
                  {settings.allowed_domains.map((domain, idx) => (
                    <li key={idx} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                      <code className="text-sm font-mono">{domain}</code>
                      <Button variant="ghost" size="icon" onClick={() => removeDomain(domain)} className="text-red-500 hover:text-red-600">
                        <XCircle className="h-4 w-4" />
                      </Button>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="network" className="space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>IP Whitelist</CardTitle>
              <Button variant="outline" size="sm" onClick={addIp}>
                <span className="text-sm">+ Agregar IP/CIDR</span>
              </Button>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-500 mb-4">Solo estas IPs/rangos podrán acceder al panel de admin</p>
              {settings.ip_whitelist.length === 0 ? (
                <p className="text-slate-500 text-center py-8">No hay IPs configuradas (todas permitidas)</p>
              ) : (
                <ul className="space-y-2">
                  {settings.ip_whitelist.map((ip, idx) => (
                    <li key={idx} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                      <code className="text-sm font-mono">{ip}</code>
                      <Button variant="ghost" size="icon" onClick={() => removeIp(ip)} className="text-red-500 hover:text-red-600">
                        <XCircle className="h-4 w-4" />
                      </Button>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Mejores Prácticas</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-slate-500">
              <div className="flex items-center gap-3 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <span>Activa MFA para todos los admins</span>
              </div>
              <div className="flex items-center gap-3 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg">
                <AlertTriangle className="h-5 w-5 text-amber-600" />
                <span>Limita IPs de admin a VPN/Oficina</span>
              </div>
              <div className="flex items-center gap-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <Key className="h-5 w-5 text-blue-600" />
                <span>Usa contraseñas de 12+ caracteres</span>
              </div>
              <div className="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                <Shield className="h-5 w-5 text-slate-600" />
                <span>Revisa logs de auditoría semanalmente</span>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}