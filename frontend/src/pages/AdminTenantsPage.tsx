import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, Input, Button, Badge, Select, SelectTrigger, SelectValue, SelectContent, SelectItem, Table, TableHeader, TableRow, TableHead, TableBody, TableCell, Pagination, Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogDescription, Label } from '@/components/ui';
import { 
  Building2, Plus, Search, Filter, MoreHorizontal, 
  Edit, Trash2, Eye, UserPlus, Mail, 
  Loader2, CheckCircle, XCircle, AlertTriangle
} from 'lucide-react';
import { api } from '@/services/api';
import { formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';

interface Tenant {
  id: string;
  name: string;
  slug: string;
  domain: string | null;
  is_active: boolean;
  subscription_tier: string;
  subscription_status: string;
  created_at: string;
  user_count: number;
}

export function AdminTenantsPage() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const perPage = 10;
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newTenant, setNewTenant] = useState({ name: '', slug: '', domain: '', subscription_tier: 'free' });
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTenants = async () => {
    setLoading(true);
    try {
      const data = await api.getTenants({
        page,
        per_page: perPage,
        search,
        status: statusFilter === 'all' ? '' : statusFilter,
      });
      setTenants(data.tenants);
      setTotal(data.total);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al cargar tenants');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTenants();
  }, [page, search, statusFilter]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setError(null);
    try {
      await api.createTenant(newTenant);
      setShowCreateDialog(false);
      setNewTenant({ name: '', slug: '', domain: '', subscription_tier: 'free' });
      fetchTenants();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al crear tenant');
    } finally {
      setCreating(false);
    }
  };

  const handleToggleActive = async (tenant: Tenant) => {
    try {
      await api.updateTenant(tenant.id, { is_active: !tenant.is_active });
      fetchTenants();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al actualizar tenant');
    }
  };

  const handleDelete = async (tenant: Tenant) => {
    if (!confirm(`¿Eliminar tenant "${tenant.name}"? Esta acción no se puede deshacer.`)) return;
    try {
      await api.deleteTenant(tenant.id);
      fetchTenants();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al eliminar tenant');
    }
  };

  const getTierBadge = (tier: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'outline' | 'destructive'> = {
      free: 'outline',
      pro: 'default',
      enterprise: 'secondary',
    };
    return <Badge variant={variants[tier] || 'outline'}>{tier}</Badge>;
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
      active: 'default',
      inactive: 'secondary',
      past_due: 'destructive',
      trialing: 'outline',
    };
    return <Badge variant={variants[status] || 'outline'}>{status}</Badge>;
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Tenants</h1>
          <p className="text-slate-500 dark:text-slate-400">Gestión de organizaciones multi-tenant</p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button onClick={() => setShowCreateDialog(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Nuevo Tenant
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Crear nuevo tenant</DialogTitle>
              <DialogDescription>Configura una nueva organización</DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid gap-2 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label htmlFor="name">Nombre</Label>
                  <Input id="name" value={newTenant.name} onChange={e => setNewTenant({...newTenant, name: e.target.value})} placeholder="Mi Empresa" required />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="slug">Slug (URL)</Label>
                  <Input id="slug" value={newTenant.slug} onChange={e => setNewTenant({...newTenant, slug: e.target.value.toLowerCase().replace(/\s+/g, '-')})} placeholder="mi-empresa" required />
                </div>
                <div className="space-y-1.5 sm:col-span-2">
                  <Label htmlFor="domain">Dominio personalizado (opcional)</Label>
                  <Input id="domain" value={newTenant.domain} onChange={e => setNewTenant({...newTenant, domain: e.target.value})} placeholder="empresa.com" />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="subscription_tier">Plan</Label>
                  <Select value={newTenant.subscription_tier} onValueChange={v => setNewTenant({...newTenant, subscription_tier: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="free">Free</SelectItem>
                      <SelectItem value="pro">Pro</SelectItem>
                      <SelectItem value="enterprise">Enterprise</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              {error && <div className="text-red-500 text-sm">{error}</div>}
              <div className="flex justify-end gap-2 pt-4">
                <Button type="button" variant="secondary" onClick={() => setShowCreateDialog(false)}>Cancelar</Button>
                <Button type="submit" disabled={creating}>
                  {creating ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null} Crear
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 text-red-700 dark:text-red-300 text-sm flex items-center justify-between">
          <span>{error}</span>
          <Button variant="ghost" size="sm" onClick={() => setError(null)}><XCircle className="h-4 w-4" /></Button>
        </div>
      )}

      <Card>
        <CardHeader className="pb-2">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="Buscar por nombre o slug..."
                value={search}
                onChange={e => { setSearch(e.target.value); setPage(1); }}
                className="pl-10"
              />
            </div>
            <Select value={statusFilter} onValueChange={v => { setStatusFilter(v as any); setPage(1); }} className="w-40">
              <SelectTrigger><SelectValue placeholder="Estado" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos</SelectItem>
                <SelectItem value="active">Activos</SelectItem>
                <SelectItem value="inactive">Inactivos</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8"><Loader2 className="h-8 w-8 animate-spin text-primary-500" /></div>
          ) : tenants.length === 0 ? (
            <div className="text-center py-12">
              <Building2 className="h-12 w-12 mx-auto text-slate-300 dark:text-slate-600 mb-3" />
              <p className="text-slate-500 dark:text-slate-400">No se encontraron tenants</p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Tenant</TableHead>
                      <TableHead>Dominio</TableHead>
                      <TableHead>Plan</TableHead>
                      <TableHead>Estado Suscripción</TableHead>
                      <TableHead>Usuarios</TableHead>
                      <TableHead>Estado</TableHead>
                      <TableHead>Creado</TableHead>
                      <TableHead className="text-right">Acciones</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {tenants.map(tenant => (
                      <TableRow key={tenant.id}>
                        <TableCell>
                          <div>
                            <p className="font-medium text-slate-900 dark:text-slate-100">{tenant.name}</p>
                            <p className="text-sm text-slate-500 dark:text-slate-400">{tenant.slug}</p>
                          </div>
                        </TableCell>
                        <TableCell className="text-sm text-slate-500 dark:text-slate-400">
                          {tenant.domain || '—'}
                        </TableCell>
                        <TableCell>{getTierBadge(tenant.subscription_tier)}</TableCell>
                        <TableCell>{getStatusBadge(tenant.subscription_status)}</TableCell>
                        <TableCell className="text-sm text-slate-500 dark:text-slate-400">{tenant.user_count}</TableCell>
                        <TableCell>
                          <Badge variant={tenant.is_active ? 'default' : 'secondary'}>
                            {tenant.is_active ? 'Activo' : 'Inactivo'}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-sm text-slate-500 dark:text-slate-400">
                          {formatDistanceToNow(new Date(tenant.created_at), { addSuffix: true, locale: es })}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-2">
                            <Button variant="ghost" size="icon" onClick={() => handleToggleActive(tenant)} title={tenant.is_active ? 'Desactivar' : 'Activar'}>
                              {tenant.is_active ? <XCircle className="h-4 w-4 text-amber-500" /> : <CheckCircle className="h-4 w-4 text-green-500" />}
                            </Button>
                            <Button variant="ghost" size="icon" onClick={() => handleDelete(tenant)} title="Eliminar">
                              <Trash2 className="h-4 w-4 text-red-500" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
              <Pagination
                page={page}
                total={total}
                perPage={perPage}
                onPageChange={setPage}
              />
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}