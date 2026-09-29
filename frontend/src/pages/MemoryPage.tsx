import { Card, CardContent, Input, Button } from '@/components/ui';
import { Brain, Search, Database, Trash2, Download } from 'lucide-react';

export function MemoryPage() {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Memoria</h1>
          <p className="text-slate-500 dark:text-slate-400">Búsqueda semántica en tu trabajo</p>
        </div>
      </div>

      <Card>
        <CardContent className="py-4">
          <div className="flex gap-3 mb-6">
            <Input
              placeholder="Busca en tu memoria... (ej: qué prometí a Juan, deadline contratos)"
              className="flex-1"
              leftIcon={<Search className="h-4 w-4" />}
            />
            <Button variant="secondary">Buscar</Button>
          </div>
          
          <div className="space-y-2 text-sm text-slate-500 dark:text-slate-400">
            <p>La búsqueda semántica te permite encontrar información usando lenguaje natural.</p>
            <p className="font-medium">Ejemplos de consultas:</p>
            <ul className="list-disc list-inside space-y-1 mt-1">
              <li>"¿Qué prometí hacer esta semana?"</li>
              <li>"¿Qué correos hablan del proyecto HES?"</li>
              <li>"¿Qué tareas tengo bloqueadas?"</li>
              <li>"¿Qué deadlines vienen esta semana?"</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="py-6 text-center">
            <Database className="h-10 w-10 mx-auto text-slate-300 dark:text-slate-600 mb-3" />
            <h3 className="font-medium text-slate-900 dark:text-slate-100 mb-1">Estadísticas</h3>
            <p className="text-slate-500 dark:text-slate-400 text-sm">Memoria no indexada aún</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="py-6 text-center">
            <Download className="h-10 w-10 mx-auto text-slate-300 dark:text-slate-600 mb-3" />
            <h3 className="font-medium text-slate-900 dark:text-slate-100 mb-1">Exportar</h3>
            <Button variant="secondary" size="sm" className="mt-2">Exportar memoria</Button>
          </CardContent>
        </Card>

        <Card className="border-red-200 dark:border-red-800">
          <CardContent className="py-6 text-center">
            <Trash2 className="h-10 w-10 mx-auto text-red-400 mb-3" />
            <h3 className="font-medium text-red-600 dark:text-red-400 mb-1">Limpiar</h3>
            <Button variant="destructive" size="sm" className="mt-2">Borrar toda la memoria</Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}