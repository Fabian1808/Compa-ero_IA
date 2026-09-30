import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { Layout } from '@/components/layout';
import { AdminLayout } from '@/components/layout';
import { HomePage } from '@/pages/HomePage';
import { TasksPage } from '@/pages/TasksPage';
import { ProjectsPage } from '@/pages/ProjectsPage';
import { CalendarPage } from '@/pages/CalendarPage';
import { FollowupsPage } from '@/pages/FollowupsPage';
import { MemoryPage } from '@/pages/MemoryPage';
import { WorkMapPage } from '@/pages/WorkMapPage';
import { ConnectorsPage } from '@/pages/ConnectorsPage';
import { AppsPage } from '@/pages/AppsPage';
import { SettingsPage } from '@/pages/SettingsPage';
import { FocusPage } from '@/pages/FocusPage';
import { AuthPage } from '@/pages/AuthPage';
import { CommitmentsPage } from '@/pages/CommitmentsPage';
import { DeadlinesPage } from '@/pages/DeadlinesPage';
import { AdminDashboardPage } from '@/pages/AdminDashboardPage';
import { AdminTenantsPage } from '@/pages/AdminTenantsPage';
import { AdminUsersPage } from '@/pages/AdminUsersPage';
import { AdminSettingsPage } from '@/pages/AdminSettingsPage';
import { AdminSecurityPage } from '@/pages/AdminSecurityPage';
import { AdminMetricsPage } from '@/pages/AdminMetricsPage';
import { AdminAuditLogsPage } from '@/pages/AdminAuditLogsPage';
import { InitializationPage } from '@/pages/InitializationPage';

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent" />
      </div>
    );
  }

  return isAuthenticated ? <>{children}</> : <Navigate to="/auth" replace />;
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent" />
      </div>
    );
  }

  return isAuthenticated ? <Navigate to="/" replace /> : <>{children}</>;
}

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/auth" element={<PublicRoute><AuthPage /></PublicRoute>} />
        <Route path="/init" element={<PublicRoute><InitializationPage /></PublicRoute>} />
        <Route element={<PrivateRoute><Layout /></PrivateRoute>}>
          <Route path="/" element={<HomePage />} />
          <Route path="/tasks" element={<TasksPage />} />
          <Route path="/projects" element={<ProjectsPage />} />
          <Route path="/calendar" element={<CalendarPage />} />
          <Route path="/followups" element={<FollowupsPage />} />
          <Route path="/commitments" element={<CommitmentsPage />} />
          <Route path="/deadlines" element={<DeadlinesPage />} />
          <Route path="/memory" element={<MemoryPage />} />
          <Route path="/workmap" element={<WorkMapPage />} />
          <Route path="/connectors" element={<ConnectorsPage />} />
          <Route path="/apps" element={<AppsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/focus" element={<FocusPage />} />
        </Route>
        <Route element={<PrivateRoute><AdminLayout /></PrivateRoute>}>
          <Route path="/admin" element={<AdminDashboardPage />} />
          <Route path="/admin/tenants" element={<AdminTenantsPage />} />
          <Route path="/admin/users" element={<AdminUsersPage />} />
          <Route path="/admin/settings" element={<AdminSettingsPage />} />
          <Route path="/admin/security" element={<AdminSecurityPage />} />
          <Route path="/admin/metrics" element={<AdminMetricsPage />} />
          <Route path="/admin/audit-logs" element={<AdminAuditLogsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
export default App;


