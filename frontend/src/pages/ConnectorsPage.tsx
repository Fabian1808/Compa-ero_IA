import { useState, useEffect } from 'react';
import { Card, CardContent, Button, Badge, Input, Tabs, TabsList, TabsTrigger, TabsContent, Separator, Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui';
import { 
  Mail, MessageSquare, FileSpreadsheet, BarChart3, Database, Github, 
  Zap, Settings, Play, RefreshCw, Search, CheckCircle, XCircle,
  ChevronDown, ChevronUp, ExternalLink, FolderOpen
} from 'lucide-react';
import { api } from '@/services/api';

interface ConnectorInfo {
  name: string;
  category: string;
  description: string;
}

interface Account {
  id: string;
  provider: string;
  email: string;
  status: string;
  last_sync: string | null;
  meta: Record<string, any>;
}

export function ConnectorsPage() {
  const [connectors, setConnectors] = useState<Record<string, string[]>>({});
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);
  const [selectedConnector, setSelectedConnector] = useState<string>('outlook');
  const [syncStatus, setSyncStatus] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);
  const [externalConfigs, setExternalConfigs] = useState<Record<string, any>>({});
  const [activeTab, setActiveTab] = useState<'microsoft' | 'external' | 'accounts'>('microsoft');
  const [searchQuery, setSearchQuery] = useState('');

  const microsoftConnectors = ['outlook', 'teams', 'onedrive', 'sharepoint', 'excel', 'powerbi'];
  const externalConnectors = ['sap', 'github', 'n8n', 'power_automate'];

  const connectorInfo: Record<string, ConnectorInfo> = {
    outlook: { name: 'Outlook', category: 'microsoft', description: 'Email, Calendar, Contacts' },
    teams: { name: 'Microsoft Teams', category: 'microsoft', description: 'Chats, Channels, Meetings' },
    onedrive: { name: 'OneDrive', category: 'microsoft', description: 'Files, Documents' },
    sharepoint: { name: 'SharePoint', category: 'microsoft', description: 'Sites, Lists, Documents' },
    excel: { name: 'Excel', category: 'microsoft', description: 'Spreadsheets, Data Import/Export' },
    powerbi: { name: 'Power BI', category: 'microsoft', description: 'Dashboards, Metrics' },
    sap: { name: 'SAP', category: 'external', description: 'ERP, Orders, Finance' },
    github: { name: 'GitHub', category: 'external', description: 'Issues, PRs, Commits' },
    n8n: { name: 'n8n', category: 'external', description: 'Workflow Automation' },
    power_automate: { name: 'Power Automate', category: 'external', description: 'Cloud Flows' },
  };

  const connectorIcons: Record<string, any> = {
    outlook: Mail,
    teams: MessageSquare,
    onedrive: FileSpreadsheet,
    sharepoint: FolderOpen,
    excel: FileSpreadsheet,
    powerbi: BarChart3,
    sap: Database,
    github: Github,
    n8n: Zap,
    power_automate: Zap,
  };

  useEffect(() => {
    loadConnectors();
    loadAccounts();
    loadExternalConfigs();
  }, []);

  const loadConnectors = async () => {
    try {
      const data = await api.getConnectors();
      setConnectors(data);
    } catch (err) {
      console.error('Failed to load connectors', err);
    }
  };

  const loadAccounts = async () => {
    try {
      const data = await api.getAccounts();
      setAccounts(data);
    } catch (err) {
      console.error('Failed to load accounts', err);
    }
  };

  const loadExternalConfigs = async () => {
    for (const conn of externalConnectors) {
      try {
        const config = await api.getExternalConnectorConfig(conn);
        setExternalConfigs(prev => ({ ...prev, [conn]: config }));
      } catch (err) {
        // Config might not exist
      }
    }
  };

  const handleTest = async (account: Account, connectorType: string) => {
    setSyncStatus(prev => ({ ...prev, [connectorType]: { status: 'testing' } }));
    try {
      const result = await api.testConnector(account.id, connectorType);
      setSyncStatus(prev => ({ ...prev, [connectorType]: { status: result.success ? 'success' : 'error', message: result.success ? 'Connected' : 'Failed' } }));
    } catch (err: any) {
      setSyncStatus(prev => ({ ...prev, [connectorType]: { status: 'error', message: err.response?.data?.detail || 'Error' } }));
    }
  };

  const handleSync = async (account: Account, connectorType: string) => {
    setSyncStatus(prev => ({ ...prev, [connectorType]: { status: 'syncing' } }));
    try {
      const result = await api.syncConnector(account.id, connectorType);
      setSyncStatus(prev => ({ ...prev, [connectorType]: { status: 'success', message: `Synced ${result.results?.length || 0} batches` } }));
      loadAccounts(); // Refresh last_sync
    } catch (err: any) {
      setSyncStatus(prev => ({ ...prev, [connectorType]: { status: 'error', message: err.response?.data?.detail || 'Sync failed' } }));
    }
  };

  const handleSearch = async () => {
    if (!selectedAccount || !searchQuery.trim()) return;
    try {
      const result = await api.getConnectorItems(selectedAccount.id, selectedConnector, searchQuery);
      setSyncStatus(prev => ({ ...prev, [`${selectedConnector}_search`]: { status: 'success', results: result.items } }));
    } catch (err: any) {
      setSyncStatus(prev => ({ ...prev, [`${selectedConnector}_search`]: { status: 'error', message: err.response?.data?.detail || 'Search failed' } }));
    }
  };

  const handleSaveExternalConfig = async (connectorType: string) => {
    const config = externalConfigs[connectorType] || {};
    try {
      await api.setExternalConnectorConfig(connectorType, config);
      alert('Configuration saved');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to save');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error': return <XCircle className="h-4 w-4 text-red-500" />;
      case 'testing':
      case 'syncing': return <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />;
      default: return <ChevronDown className="h-4 w-4 text-slate-400" />;
    }
  };

  const getAccountStatusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
      active: 'default',
      error: 'destructive',
      inactive: 'secondary',
    };
    return <Badge variant={variants[status] || 'outline'}>{status}</Badge>;
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Conectores</h1>
          <p className="text-slate-500 dark:text-slate-400">Gestiona integraciones con servicios externos</p>
        </div>
        <Button onClick={loadAccounts}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Actualizar cuentas
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="microsoft">Microsoft 365</TabsTrigger>
          <TabsTrigger value="external">Externos</TabsTrigger>
          <TabsTrigger value="accounts">Cuentas</TabsTrigger>
        </TabsList>

        {/* Microsoft 365 Tab */}
        <TabsContent value="microsoft">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {microsoftConnectors.map(conn => {
              const info = connectorInfo[conn];
              const Icon = connectorIcons[conn];
              const status = syncStatus[conn];
              return (
                <Card key={conn} className="overflow-hidden">
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-xl bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
                          <Icon className="h-6 w-6 text-primary-600 dark:text-primary-400" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-slate-900 dark:text-slate-100">{info.name}</h3>
                          <p className="text-sm text-slate-500 dark:text-slate-400">{info.description}</p>
                        </div>
                      </div>
                      {status && getStatusIcon(status.status || '')}
                    </div>
                    
                    <Separator className="my-4" />
                    
                    {selectedAccount ? (
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <Badge variant={selectedAccount.status === 'active' ? 'default' : 'secondary'}>
                            {selectedAccount.email}
                          </Badge>
                          {status && (
                            <Badge variant={status.status === 'success' ? 'default' : status.status === 'error' ? 'destructive' : 'secondary'}>
                              {status.message || status.status}
                            </Badge>
                          )}
                        </div>
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleTest(selectedAccount!, conn)}
                            disabled={selectedAccount.status !== 'active'}
                          >
                            <ChevronDown className="h-4 w-4 mr-1" />
                            Probar
                          </Button>
                          <Button
                            size="sm"
                            onClick={() => handleSync(selectedAccount!, conn)}
                            disabled={selectedAccount.status !== 'active'}
                          >
                            <Play className="h-4 w-4 mr-1" />
                            Sincronizar
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center text-slate-500 dark:text-slate-400 py-4">
                        <p className="text-sm">Selecciona una cuenta en la pestaña "Cuentas"</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>

        {/* External Tab */}
        <TabsContent value="external">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {externalConnectors.map(conn => {
              const info = connectorInfo[conn];
              const Icon = connectorIcons[conn];
              const config = externalConfigs[conn] || {};
              const isConfigured = Object.keys(config).length > 0;
              return (
                <Card key={conn} className="overflow-hidden">
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-xl bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                          <Icon className="h-6 w-6 text-amber-600 dark:text-amber-400" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-slate-900 dark:text-slate-100">{info.name}</h3>
                          <p className="text-sm text-slate-500 dark:text-slate-400">{info.description}</p>
                        </div>
                      </div>
                      <Badge variant={isConfigured ? 'default' : 'outline'}>
                        {isConfigured ? 'Configurado' : 'Pendiente'}
                      </Badge>
                    </div>
                    
                    <Separator className="my-4" />
                    
                    <div className="space-y-3">
                      {conn === 'sap' && (
                        <>
                          <div className="grid gap-2 sm:grid-cols-2">
                            <Input
                              placeholder="Base URL (ej: https://sap.example.com)"
                              value={config.base_url || ''}
                              onChange={e => setExternalConfigs(prev => ({ ...prev, sap: { ...prev.sap, base_url: e.target.value } }))}
                            />
                            <Input
                              placeholder="Client ID"
                              value={config.client_id || ''}
                              onChange={e => setExternalConfigs(prev => ({ ...prev, sap: { ...prev.sap, client_id: e.target.value } }))}
                            />
                            <Input
                              type="password"
                              placeholder="Client Secret"
                              value={config.client_secret || ''}
                              onChange={e => setExternalConfigs(prev => ({ ...prev, sap: { ...prev.sap, client_secret: e.target.value } }))}
                            />
                            <Input
                              placeholder="Username (opcional)"
                              value={config.username || ''}
                              onChange={e => setExternalConfigs(prev => ({ ...prev, sap: { ...prev.sap, username: e.target.value } }))}
                            />
                          </div>
                          <Button onClick={() => handleSaveExternalConfig('sap')} disabled={!config.base_url || !config.client_id}>
                            Guardar configuración SAP
                          </Button>
                        </>
                      )}
                      
                      {conn === 'github' && (
                        <>
                          <div className="grid gap-2 sm:grid-cols-3">
                            <Input
                              placeholder="Personal Access Token"
                              type="password"
                              value={config.token || ''}
                              onChange={e => setExternalConfigs(prev => ({ ...prev, github: { ...prev.github, token: e.target.value } }))}
                            />
                            <Input
                              placeholder="Owner (usuario/org)"
                              value={config.owner || ''}
                              onChange={e => setExternalConfigs(prev => ({ ...prev, github: { ...prev.github, owner: e.target.value } }))}
                            />
                            <Input
                              placeholder="Repository"
                              value={config.repo || ''}
                              onChange={e => setExternalConfigs(prev => ({ ...prev, github: { ...prev.github, repo: e.target.value } }))}
                            />
                          </div>
                          <Button onClick={() => handleSaveExternalConfig('github')} disabled={!config.token || !config.owner || !config.repo}>
                            Guardar configuración GitHub
                          </Button>
                        </>
                      )}
                      
                      {conn === 'n8n' && (
                        <>
                          <div className="grid gap-2 sm:grid-cols-2">
                            <Input
                              placeholder="Base URL (ej: http://localhost:5678)"
                              value={config.base_url || ''}
                              onChange={e => setExternalConfigs(prev => ({ ...prev, n8n: { ...prev.n8n, base_url: e.target.value } }))}
                            />
                            <Input
                              type="password"
                              placeholder="API Key"
                              value={config.api_key || ''}
                              onChange={e => setExternalConfigs(prev => ({ ...prev, n8n: { ...prev.n8n, api_key: e.target.value } }))}
                            />
                          </div>
                          <Button onClick={() => handleSaveExternalConfig('n8n')} disabled={!config.base_url || !config.api_key}>
                            Guardar configuración n8n
                          </Button>
                        </>
                      )}
                      
                      {conn === 'power_automate' && (
                        <>
                          <div className="grid gap-2 sm:grid-cols-2">
                            <Input
                              placeholder="Tenant ID"
                              value={config.tenant_id || ''}
                              onChange={e => setExternalConfigs(prev => ({ ...prev, power_automate: { ...prev.power_automate, tenant_id: e.target.value } }))}
                            />
                            <Input
                              placeholder="Client ID"
                              value={config.client_id || ''}
                              onChange={e => setExternalConfigs(prev => ({ ...prev, power_automate: { ...prev.power_automate, client_id: e.target.value } }))}
                            />
                            <Input
                              type="password"
                              placeholder="Client Secret"
                              value={config.client_secret || ''}
                              onChange={e => setExternalConfigs(prev => ({ ...prev, power_automate: { ...prev.power_automate, client_secret: e.target.value } }))}
                            />
                          </div>
                          <Button onClick={() => handleSaveExternalConfig('power_automate')} disabled={!config.tenant_id || !config.client_id || !config.client_secret}>
                            Guardar configuración Power Automate
                          </Button>
                        </>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>

        {/* Accounts Tab */}
        <TabsContent value="accounts">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Cuentas conectadas</h3>
                <Badge variant="outline">{accounts.length} cuentas</Badge>
              </div>
              
              {accounts.length === 0 ? (
                <div className="text-center py-12">
                  <Mail className="h-12 w-12 mx-auto text-slate-300 dark:text-slate-600 mb-3" />
                  <p className="text-slate-500 dark:text-slate-400">No hay cuentas conectadas</p>
                  <p className="text-sm text-slate-400 dark:text-slate-500 mt-1">Ve a Configuración &gt; Autenticación para conectar Microsoft 365</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {accounts.map(account => (
                    <Card key={account.id} className="hover:shadow-md transition-shadow">
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            <div className="w-10 h-10 rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
                              <Mail className="h-5 w-5 text-primary-600 dark:text-primary-400" />
                            </div>
                            <div>
                              <p className="font-medium text-slate-900 dark:text-slate-100">{account.email}</p>
                              <p className="text-sm text-slate-500 dark:text-slate-400">
                                {account.provider} • {getAccountStatusBadge(account.status)}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            {account.last_sync && (
                              <span className="text-sm text-slate-500 dark:text-slate-400">
                                Última sync: {new Date(account.last_sync).toLocaleString()}
                              </span>
                            )}
                            <Select
                              value={selectedAccount?.id === account.id ? account.id : ''}
                              onValueChange={value => setSelectedAccount(value ? account : null)}
                            >
                              <SelectTrigger className="w-40">
                                <SelectValue placeholder="Seleccionar" />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value={account.id}>
                                  Usar esta cuenta
                                </SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}