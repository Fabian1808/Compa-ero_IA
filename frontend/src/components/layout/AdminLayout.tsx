import { Outlet } from 'react-router-dom';
import { AdminSidebar } from './AdminSidebar';

export function AdminLayout() {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <AdminSidebar />
      <main className="lg:pl-64 min-h-screen">
        <div className="p-6 lg:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}