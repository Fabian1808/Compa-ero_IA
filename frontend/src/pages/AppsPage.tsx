import { Card, CardContent, CardHeader, CardTitle, Badge, Button } from '@/components/ui';
import { Mail, Calendar, MessageSquare, HardDrive, Zap, Plus, Check, Loader2, X } from 'lucide-react';

const availableApps = [
  {
    id: 'outlook',
    name: 'Outlook',
    description: 'Correo, contactos y hilos de conversación',
    icon: Mail,
    color: 'bg-blue-500',
    status: 'connected' as const,
    scopes: ['Mail.Read', 'Mail.ReadWrite', 'Contacts.Read'],
  },
  {
    id: 'calendar',
    name: 'Calendario',
    description: 'Eventos, reuniones y disponibilidad',
    icon: Calendar,
    color: 'bg-green-500',
    status: 'available' as const,
    scopes: ['Calendars.Read'],
  },
  {
    id: 'teams',
    name: 'Teams',
    description: 'Chats, canales y reuniones online',
    icon: MessageSquare,
    color: 'bg-purple-500',
    status: 'available' as const,
    scopes: ['Chat.Read', 'OnlineMeetings.Read'],
  },
  {
    id: 'onedrive',
    name: 'OneDrive',
    description: 'Archivos y documentos personales',
    icon: HardDrive,
    color: 'bg-cyan-500',
    status: 'available' as const,
    scopes: ['Files.Read', 'Files.ReadWrite'],
  },
  {
    id: 'sharepoint',
    name: 'SharePoint',
    description: 'Sitios, listas y documentos de equipo',
    icon: Zap,
    color: 'bg-orange-500',
    status: 'available' as const,
    scopes: ['Sites.Read.All'],
  },
];

export function AppsPage() {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Aplicaciones conectadas</h1>
        <p className="text-slate-500 dark:text-slate-400">Gestiona qué aplicaciones puede usar AI Workmate</p>
      </div>

      <div className="space-y-4">
        {availableApps.map((app) => (
          <Card key={app.id}>
            <CardContent className="py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-xl ${app.color}`}>
                    <app.icon className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900 dark:text-slate-100">{app.name}</h3>
                    <p className="text-sm text-slate-500 dark:text-slate-400">{app.description}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant={app.status === 'connected' ? 'success' : 'muted'}>
                        {app.status === 'connected' ? 'Conectado' : 'Disponible'}
                      </Badge>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {app.status === 'connected' ? (
                    <Button variant="destructive" size="sm">
                      <X className="h-4 w-4" />
                      Desconectar
                    </Button>
                  ) : (
                    <Button variant="primary" size="sm">
                      <Plus className="h-4 w-4" />
                      Conectar
                    </Button>
                  )}
                </div>
              </div>

              {app.status === 'connected' && (
                <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-700">
                  <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Permisos concedidos:</h4>
                  <div className="flex flex-wrap gap-1">
                    {app.scopes.map((scope) => (
                      <Badge key={scope} variant="muted" className="text-xs">{scope}</Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="border-dashed border-2 border-slate-300 dark:border-slate-600">
        <CardContent className="py-8 text-center">
          <Plus className="h-10 w-10 mx-auto text-slate-300 dark:text-slate-600 mb-3" />
          <h3 className="font-medium text-slate-900 dark:text-slate-100 mb-1">Más aplicaciones próximamente</h3>
          <p className="text-slate-500 dark:text-slate-400 mb-4">Excel, Power BI, SAP, GitHub, y más en futuras fases</p>
          <Button variant="secondary">
            <Plus className="h-4 w-4" />
            Sugerir integración
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}