import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import CaseInbox from './pages/CaseInbox';
import CaseDetail from './pages/CaseDetail';
import SLAMonitor from './pages/SLAMonitor';
import MisrouteAnalytics from './pages/MisrouteAnalytics';
import LoginAudit from './pages/LoginAudit';
import AuditLogs from './pages/AuditLogs';
import Settings from './pages/Settings';
import Reconciliation from './pages/Reconciliation';
import KYCPacks from './pages/KYCPacks';
import KYCPackDetail from './pages/KYCPackDetail';
import LEARequests from './pages/LEARequests';
import LEARequestDetail from './pages/LEARequestDetail';
import GrievanceWorkbench from './pages/GrievanceWorkbench';
import GrievanceDetail from './pages/GrievanceDetail';
import MoneyRestoration from './pages/MoneyRestoration';
import RestorationDetail from './pages/RestorationDetail';
import DemoDataset from './pages/DemoDataset';

import Login from './pages/Login';

const App: React.FC = () => {
    const [isAuthenticated, setIsAuthenticated] = React.useState(!!localStorage.getItem('lumien_token'));

    if (!isAuthenticated) {
        return <Login onLogin={() => setIsAuthenticated(true)} />;
    }

    return (
        <Router>
            <div className="flex min-h-screen bg-slate-50">
                <Sidebar />
                <main className="flex-1 ml-64 p-8">
                    <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/inbox" element={<CaseInbox />} />
                        <Route path="/case/:id" element={<CaseDetail />} />
                        <Route path="/sla" element={<SLAMonitor />} />
                        <Route path="/misroute" element={<MisrouteAnalytics />} />
                        <Route path="/admin/audit-logs" element={<AuditLogs />} />
                        <Route path="/admin/login-audit" element={<LoginAudit />} />
                        <Route path="/reconciliation" element={<Reconciliation />} />
                        <Route path="/kyc-packs" element={<KYCPacks />} />
                        <Route path="/kyc-packs/:packId" element={<KYCPackDetail />} />
                        <Route path="/lea-requests" element={<LEARequests />} />
                        <Route path="/lea-requests/:requestId" element={<LEARequestDetail />} />
                        <Route path="/grievances" element={<GrievanceWorkbench />} />
                        <Route path="/grievances/:grievanceId" element={<GrievanceDetail />} />
                        <Route path="/restoration" element={<MoneyRestoration />} />
                        <Route path="/restoration/:orderId" element={<RestorationDetail />} />
                        <Route path="/demo-dataset" element={<DemoDataset />} />
                        <Route path="/settings" element={<Settings />} />
                        <Route path="*" element={<Navigate to="/" />} />
                    </Routes>
                </main>
            </div>
        </Router>
    );
};

export default App;
