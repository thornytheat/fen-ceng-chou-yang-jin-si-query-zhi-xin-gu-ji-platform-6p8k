import { Navigate, Route, Routes } from 'react-router-dom';
import AppShell from '../components/layout/AppShell';
import Datasets from '../pages/Datasets';
import Login from '../pages/Login';
import Plans from '../pages/Plans';
import Qc from '../pages/Qc';
import Queries from '../pages/Queries';
import { RequireAuth, RequirePermission } from './guards';

function Protected({ permission, children }: { permission: string; children: React.ReactNode }) {
  return (
    <RequireAuth>
      <AppShell>
        <RequirePermission permission={permission}>{children}</RequirePermission>
      </AppShell>
    </RequireAuth>
  );
}

export default function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Navigate to="/datasets" replace />} />
      <Route path="/datasets" element={<Protected permission="dataset:read"><Datasets /></Protected>} />
      <Route path="/plans" element={<Protected permission="plan:read"><Plans /></Protected>} />
      <Route path="/queries" element={<Protected permission="query:read"><Queries /></Protected>} />
      <Route path="/qc" element={<Protected permission="qc:read"><Qc /></Protected>} />
      <Route path="*" element={<Navigate to="/datasets" replace />} />
    </Routes>
  );
}
