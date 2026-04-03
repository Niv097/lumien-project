import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('lumien_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.clear();
            window.location.href = '/';
        }
        return Promise.reject(error);
    }
);

export const authApi = {
    login: (credentials: URLSearchParams) => api.post('/auth/login', credentials, {
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    }),
    register: (data: { username: string; email: string; password: string; role?: string; bank_id?: number; branch_id?: number }) => 
        api.post('/auth/register', data),
};

export const caseApi = {
    getCases: (params?: any) => api.get('/tenant/cases', { params }),
    getCaseDetail: (id: string) => api.get(`/tenant/cases/${id}`),
    routeCase: (id: string) => api.post(`/cases/${id}/route`),
    bankRespond: (id: string, data: any) => api.post(`/bank/${id}/respond`, data),
    getReconciliation: () => api.get('/operations/reconciliation'),
    reconcileCase: (id: string) => api.post(`/bank/${id}/reconcile`),
};

// New tenant API for multi-tenant operations
export const tenantApi = {
    getBanks: () => api.get('/tenant/banks'),
    getBranches: (bankId?: number) => api.get('/tenant/branches', { params: { bank_id: bankId } }),
    getCases: (params?: { bank_id?: number; branch_id?: number; status?: string }) => api.get('/tenant/cases', { params }),
    getCaseDetail: (id: number) => api.get(`/tenant/cases/${id}`),
    getWorkflows: (params?: { case_id?: number; bank_id?: number; branch_id?: number }) => api.get('/tenant/workflow', { params }),
    getDashboard: (params?: { bank_id?: number; branch_id?: number }) => api.get('/tenant/dashboard', { params }),
    getHoldActions: (params?: { bank_id?: number; branch_id?: number; case_id?: string }) => api.get('/tenant/hold-actions', { params }),
};

export const i4cApi = {
    getMockData: () => api.get('/i4c/ncrp-mock'),
    ingest: (data: any) => api.post('/i4c/ingest', data),
};

export const i4cDatasetApi = {
    // Fraud Reports (Case Inbox data source)
    getFraudReports: (params?: { bank_id?: number; status?: string; branch_id?: number; limit?: number }) => 
        api.get('/i4c-dataset/fraud-reports', { params: { ...params, limit: params?.limit || 10000 } }),
    getFraudReportDetail: (acknowledgement_no: string) => api.get(`/i4c-dataset/fraud-reports/${acknowledgement_no}`),
    
    // Incidents (Transactions)
    getIncidents: (params?: { acknowledgement_no?: string }) => api.get('/i4c-dataset/incidents', { params }),
    
    // Workflow & Timeline
    getCaseWorkflow: (acknowledgement_no: string) => api.get(`/i4c-dataset/workflow/${acknowledgement_no}`),
    getTimeline: (acknowledgement_no: string) => api.get(`/i4c-dataset/timeline/${acknowledgement_no}`),
    
    // Hold Actions
    getHoldActions: (acknowledgement_no: string) => api.get(`/i4c-dataset/hold-actions/${acknowledgement_no}`),
    createHoldAction: (data: any) => api.post('/i4c-dataset/hold-actions', data),
    
    // Status Updates (I4C Sync for all bank responses)
    createStatusUpdate: (data: any) => api.post('/i4c-dataset/status-updates', data),
    
    // Reference Data
    getStatusCodes: () => api.get('/i4c-dataset/status-codes'),
    getBankMaster: () => api.get('/i4c-dataset/bank-master'),
};

export const adminApi = {
    getMetrics: () => api.get('/admin/metrics'),
    getAuditLogs: () => api.get('/admin/audit-logs'),
    getBanks: () => api.get('/tenant/banks'),
    getSLAMonitor: () => api.get('/admin/sla-monitor'),
    getMisrouteAnalytics: () => api.get('/admin/misroute-analytics'),
};

// Operations API for playbooks and advanced features
export const operationsApi = {
    // KYC Pack Submission
    getKYCPacks: (params?: any) => api.get('/operations/kyc-packs', { params }),
    getKYCPack: (packId: string) => api.get(`/operations/kyc-packs/${packId}`),
    createKYCPack: (data: any) => api.post('/operations/kyc-packs', data),
    submitKYCPack: (packId: string) => api.post(`/operations/kyc-packs/${packId}/submit`),
    uploadKYCDocument: (packId: string, formData: FormData) => 
        api.post(`/operations/kyc-packs/${packId}/attachments`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        }),
    
    // LEA Requests
    getLEARequests: (params?: any) => api.get('/operations/lea-requests', { params }),
    getLEARequest: (requestId: string) => api.get(`/operations/lea-requests/${requestId}`),
    acknowledgeLEARequest: (requestId: string) => api.post(`/operations/lea-requests/${requestId}/acknowledge`),
    submitLEAResponse: (requestId: string, data: any) => api.post(`/operations/lea-requests/${requestId}/submit-response`, data),
    
    // Grievance Workbench
    getGrievances: (params?: any) => api.get('/operations/grievances', { params }),
    getGrievance: (grievanceId: string) => api.get(`/operations/grievances/${grievanceId}`),
    createGrievance: (data: any) => api.post('/operations/grievances', data),
    resolveGrievance: (grievanceId: string, data: any) => api.post(`/operations/grievances/${grievanceId}/resolve`, data),
    
    // Money Restoration
    getRestorations: (params?: any) => api.get('/operations/restorations', { params }),
    getRestoration: (restorationId: string) => api.get(`/operations/restorations/${restorationId}`),
    createRestoration: (data: any) => api.post('/operations/restorations', data),
    approveRestoration: (restorationId: string) => api.post(`/operations/restorations/${restorationId}/approve`),
    executeRestoration: (restorationId: string) => api.post(`/operations/restorations/${restorationId}/execute`),
    
    // Evidence & Documents
    uploadEvidence: (caseId: string, formData: FormData) => 
        api.post(`/operations/cases/${caseId}/evidence`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        }),
    getEvidence: (caseId: string) => api.get(`/operations/cases/${caseId}/evidence`),
    downloadEvidence: (evidenceId: string) => api.get(`/operations/evidence/${evidenceId}/download`, { responseType: 'blob' }),
    
    // Export & Reporting
    exportCases: (params: any) => api.get('/operations/export/cases', { params, responseType: 'blob' }),
    generateReport: (reportType: string, params: any) => api.post(`/operations/reports/${reportType}`, params),
    getExportHistory: () => api.get('/operations/export/history'),
    
    // Real I4C Integration
    getI4CConfig: () => api.get('/operations/i4c/config'),
    updateI4CConfig: (data: any) => api.post('/operations/i4c/config', data),
    testI4CConnection: () => api.post('/operations/i4c/test-connection'),
    getI4CAPILogs: () => api.get('/operations/i4c/logs'),
    
    // Notifications
    getNotifications: () => api.get('/operations/notifications'),
    markNotificationRead: (id: string) => api.post(`/operations/notifications/${id}/read`),
    getNotificationSettings: () => api.get('/operations/notifications/settings'),
    updateNotificationSettings: (data: any) => api.post('/operations/notifications/settings', data),
};

// New unified cases API for branch-based visibility (hides receiver bank)
export const casesApi = {
    getCases: (params?: { status?: string; source_type?: string }) => 
        api.get('/cases/', { params }),
    getCaseDetail: (caseId: string) => api.get(`/cases/${caseId}`),
    performAction: (caseId: string, action: string, hold_amount?: number, remarks?: string) => {
        const params = new URLSearchParams();
        params.append('action', action);
        // Only send hold_amount for hold/freeze actions
        if (hold_amount && hold_amount > 0 && (action === 'hold' || action === 'freeze')) {
            params.append('hold_amount', hold_amount.toString());
        }
        if (remarks) {
            params.append('remarks', remarks);
        }
        return api.post(`/cases/${caseId}/action?${params.toString()}`);
    },
    uploadEvidence: (caseId: string, file_name: string, file_type: string, file_url?: string) => {
        const params = new URLSearchParams();
        params.append('file_name', file_name);
        params.append('file_type', file_type);
        if (file_url) {
            params.append('file_url', file_url);
        }
        return api.post(`/cases/${caseId}/evidence?${params.toString()}`);
    },
    getEvidence: (caseId: string) => api.get(`/cases/${caseId}/evidence`),
    // Admin only
    assignCase: (caseId: string, branchId: number) => 
        api.post(`/cases/${caseId}/assign?target_branch_id=${branchId}`),
    toggleDemoAccess: (branchId: number, enable: boolean) => 
        api.post(`/cases/admin/branches/${branchId}/demo-access?enable=${enable}`),
    getBranches: () => api.get('/cases/admin/branches'),
};

export default api;
