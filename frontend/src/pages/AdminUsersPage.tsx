import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, Input, Button, Badge, Select, SelectTrigger, SelectValue, SelectContent, SelectItem, Table, TableHeader, TableRow, TableHead, TableBody, TableCell, Pagination, Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogDescription, Label } from '@/components/ui';
import { 
  Users, Plus, Search, Filter, MoreHorizontal, 
  Edit, Trash2, Eye, UserPlus, Mail, 
  Loader2, CheckCircle, XCircle, AlertTriangle, Shield
} from 'lucide-react';
import { api } from '@/services/api';
import { formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';

interface User {
  id: string;
  user_id: string;
  email: string;
  name: string;
  role: string;
  is_active: boolean;
  joined_at: string | null;
  last_active_at: string | null;
}

export function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState<'all' | 'owner' | 'admin' | 'member' | 'viewer'>('all');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const perPage = 10;
  const [showInviteDialog, setShowInviteDialog] = useState(false);
  const [inviteData, setInviteData] = useState({ email: '', role: 'member' });
  const [inviting, setInviting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTenant, setSelectedTenant] = useState<string>('');

  const fetchUsers = async () => {
    if (!selectedTenant) {
      setUsers([]);
      setTotal(0);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const data = await api.getTenantUsers(selectedTenant, { page, per_page: perPage });
      // Client-side filtering for search/role/status
      let filtered = data.users;
      if (search) {
        filtered = filtered.filter(u => 
          u.email.toLowerCase().includes(search.toLowerCase()) ||
          u.name.toLowerCase().includes(search.toLowerCase())
        );
      }
      if (roleFilter !== 'all') {
        filtered = filtered.filter(u => u.role === roleFilter);
      }
      if (statusFilter !== 'all') {
        filtered = filtered.filter(u => u.is_active === (statusFilter === 'active'));
      }
      setUsers(filtered);
      setTotal(data.total);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al cargar usuarios');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [page, search, roleFilter, statusFilter, selectedTenant]);

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    setInviting(true);
    setError(null);
    try {
      await api.createInvitation(selectedTenant, inviteData);
      setShowInviteDialog(false);
      setInviteData({ email: '', role: 'member' });
      fetchUsers();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al invitar usuario');
    } finally {
      setInviting(false);
    }
  };

  const handleRoleChange = async (user: User, newRole: string) => {
    try {
      await api.updateTenantUser(selectedTenant, user.user_id, { role: newRole });
      fetchUsers();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al actualizar rol');
    }
  };

  const handleToggleActive = async (user: User) => {
    try {
      await api.updateTenantUser(selectedTenant, user.user_id, { is_active: !user.is_active });
      fetchUsers();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al actualizar usuario');
    }
  };

  const handleRemove = async (user: User) => {
    if (!confirm(`¿Eliminar usuario "${user.email}" del tenant?`)) return;
    try {
      await api.removeTenantUser(selectedTenant, user.user_id);
      fetchUsers();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al eliminar usuario');
    }
  };

  const getRoleBadge = (role: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'outline' | 'destructive'> = {
      owner: 'secondary',
      admin: 'default',
      member: 'outline',
      viewer: 'outline',
    };
    const icons: Record<string, any> = {
      owner: <Shield className="h-3 w-3 mr-1" />,
      admin: <Shield className="h-3 w-3 mr-1" />,
    };
    return (
      <Badge variant={variants[role] || 'outline'} className="gap-1">
        {icons[role] || null}{role}
      </Badge>
    );
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Usuarios</h1>
          <p className="text-slate-500 dark:text-slate-400">Gestión de miembros por tenant</p>
        </div>
        {selectedTenant && (
          <Dialog open={showInviteDialog} onOpenChange={setShowInviteDialog}>
            <DialogTrigger asChild>
              <Button onClick={() => setShowInviteDialog(true)}>
                <UserPlus className="h-4 w-4 mr-2" />
                Invitar usuario
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Invitar usuario</DialogTitle>
                <DialogDescription>Envía una invitación por email</DialogDescription>
              </DialogHeader>
              <form onSubmit={handleInvite} className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="email">Email</Label>
                  <Input id="email" type="email" value={inviteData.email} onChange={e => setInviteData({...inviteData, email: e.target.value})} placeholder="usuario@empresa.com" required />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="role">Rol</Label>
                  <Select value={inviteData.role} onValueChange={v => setInviteData({...inviteData, role: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="owner">Owner</SelectItem>
                      <SelectItem value="admin">Admin</SelectItem>
                      <SelectItem value="member">Member</SelectItem>
                      <SelectItem value="viewer">Viewer</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                {error && <div className="text-red-500 text-sm">{error}</div>}
                <div className="flex justify-end gap-2 pt-4">
                  <Button type="button" variant="secondary" onClick={() => setShowInviteDialog(false)}>Cancelar</Button>
                  <Button type="submit" disabled={inviting}>
                    {inviting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null} Enviar invitación
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        )}
        <Button onClick={() => setShowInviteDialog(true)} disabled={!selectedTenant}>
          <UserPlus className="h-4 w-4 mr-2" />
          Invitar usuario
        </Button>
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
                placeholder="Buscar por email o nombre..."
                value={search}
                onChange={e => { setSearch(e.target.value); setPage(1); }}
                className="pl-10"
              />
            </div>
            <Select value={roleFilter} onValueChange={v => { setRoleFilter(v as any); setPage(1); }} className="w-36">
              <SelectTrigger><SelectValue placeholder="Rol" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos</SelectItem>
                <SelectItem value="owner">Owner</SelectItem>
                <SelectItem value="admin">Admin</SelectItem>
                <SelectItem value="member">Member</SelectItem>
                <SelectItem value="viewer">Viewer</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={v => { setStatusFilter(v as any); setPage(1); }} className="w-36">
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
          {!selectedTenant ? (
            <div className="text-center py-12">
              <Users className="h-12 w-12 mx-auto text-slate-300 dark:text-slate-600 mb-3" />
              <p className="text-slate-500 dark:text-slate-400">Selecciona un tenant en la configuración para ver sus usuarios</p>
            </div>
          ) : loading ? (
            <div className="flex justify-center py-8"><Loader2 className="h-8 w-8 animate-spin text-primary-500" /></div>
          ) : users.length === 0 ? (
            <div className="text-center py-12">
              <Users className="h-12 w-12 mx-auto text-slate-300 dark:text-slate-600 mb-3" />
              <p className="text-slate-500 dark:text-slate-400">No se encontraron usuarios</p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Usuario</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Rol</TableHead>
                      <TableHead>Estado</TableHead>
                      <TableHead>Unido</TableHead>
                      <TableHead>Última actividad</TableHead>
                      <TableHead className="text-right">Acciones</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.map(user => (
                      <TableRow key={user.id}>
                        <TableCell>
                          <p className="font-medium text-slate-900 dark:text-slate-100">{user.name || 'Sin nombre'}</p>
                        </TableCell>
                        <TableCell className="text-sm text-slate-500 dark:text-slate-400">{user.email}</TableCell>
                        <TableCell>{getRoleBadge(user.role)}</TableCell>
                        <TableCell>
                          <Badge variant={user.is_active ? 'default' : 'secondary'}>
                            {user.is_active ? 'Activo' : 'Inactivo'}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-sm text-slate-500 dark:text-slate-400">
                          {user.joined_at ? formatDistanceToNow(new Date(user.joined_at), { addSuffix: true, locale: es }) : '—'}
                        </TableCell>
                        <TableCell className="text-sm text-slate-500 dark:text-slate-400">
                          {user.last_active_at ? formatDistanceToNow(new Date(user.last_active_at), { addSuffix: true, locale: es }) : 'Nunca'}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-2">
                            <Select value={user.role} onValueChange={v => handleRoleChange(user, v)} className="w-32">
                              <SelectTrigger className="py-1 text-xs"><SelectValue /></SelectTrigger>
                              <SelectContent>
                                <SelectItem value="owner">Owner</SelectItem>
                                <SelectItem value="admin">Admin</SelectItem>
                                <SelectItem value="member">Member</SelectItem>
                                <SelectItem value="viewer">Viewer</SelectItem>
                              </SelectContent>
                            </Select>
                            <Button variant="ghost" size="icon" onClick={() => handleToggleActive(user)} title={user.is_active ? 'Desactivar' : 'Activar'}>
                              {user.is_active ? <XCircle className="h-4 w-4 text-amber-500" /> : <CheckCircle className="h-4 w-4 text-green-500" />}
                            </Button>
                            <Button variant="ghost" size="icon" onClick={() => handleRemove(user)} title="Eliminar">
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

function getRoleBadge(role: string) {
  const variants: Record<string, 'default' | 'secondary' | 'outline' | 'destructive'> = {
    owner: 'secondary',
    admin: 'default',
    member: 'outline',
    viewer: 'outline',
  };
  const icons: Record<string, any> = {
    owner: <Shield className="h-3 w-3 mr-1" />,
    admin: <Shield className="h-3 w-3 mr-1" />,
  };
  return (
    <Badge variant={variants[role] || 'outline'} className="gap-1">
      {icons[role] || null}{role}
    </Badge>
  );
}