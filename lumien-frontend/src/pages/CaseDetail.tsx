import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
    ArrowLeft,
    ShieldCheck,
    Clock,
    History,
    FileText,
    MessageSquare,
    AlertTriangle,
    Send,
    CheckCircle2,
    Lock,
    ExternalLink,
    ShieldAlert,
    Info,
    Building2,
    Loader2,
    CreditCard,
    ArrowRightLeft,
    RefreshCw,
    Server,
    Code,
    Upload,
    Download
} from 'lucide-react';
import { caseApi, casesApi, i4cDatasetApi, operationsApi } from '../api';
import { cn } from '../utils/cn';

const CaseDetail: React.FC = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState(false);
    const [remarks, setRemarks] = useState('');
    const [holdAmount, setHoldAmount] = useState<number>(0);
    const [holdAmountError, setHoldAmountError] = useState<string>('');
    const [i4cSyncResult, setI4cSyncResult] = useState<any>(null);
    const [evidence, setEvidence] = useState<any[]>([]);
    const [uploading, setUploading] = useState(false);
    const [selectedFileType, setSelectedFileType] = useState('DOCUMENT');

    const fetchData = async () => {
        if (!id) return;
        setLoading(true);
        try {
            // Use new unified cases API for case detail
            const res = await casesApi.getCaseDetail(id);
            setData(res.data);
            // Also fetch evidence
            await fetchEvidence();
        } catch (err) {
            console.error('Failed to fetch case detail:', err);
            setData(null);
        } finally {
            setLoading(false);
        }
    };

    const fetchEvidence = async () => {
        if (!id) return;
        try {
            const res = await operationsApi.getEvidence(id);
            setEvidence(res.data.items || []);
        } catch (err) {
            console.log('Evidence fetch (optional):', err);
        }
    };

    const handleEvidenceUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file || !id) return;
        
        setUploading(true);
        const formData = new FormData();
        formData.append('file', file);
        formData.append('description', 'Case evidence');
        
        try {
            await operationsApi.uploadEvidence(id, formData);
            await fetchEvidence();
            alert('Evidence uploaded successfully');
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Upload failed');
        } finally {
            setUploading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [id]);

    useEffect(() => {
        // Initialize hold amount from unified case data (amount field)
        const amount = data?.amount || data?.report?.amount || data?.complaint?.amount;
        if (amount && amount > 0) {
            setHoldAmount(amount);
        }
    }, [data]);

    const handleRoute = async () => {
        if (!id) return;
        setActionLoading(true);
        try {
            await caseApi.routeCase(id);
            await fetchData();
            alert('Case routed to bank node.');
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Routing failed');
        } finally {
            setActionLoading(false);
        }
    };

    const handleBankResponse = async (code: string) => {
        if (!id) return;
        setActionLoading(true);
        try {
            // Validate hold amount before submitting
            if (code === 'hold' && holdAmount > (data?.amount || 0)) {
                alert('Hold amount cannot exceed exposure amount');
                setActionLoading(false);
                return;
            }
            
            // Use new unified cases API with hold_amount
            const res = await casesApi.performAction(id, code, holdAmount);
            
            await fetchData();
            alert(`Action performed: ${code}\nNew status: ${res.data.new_status}`);
        } catch (err: any) {
            console.error('Action failed:', err.response?.data || err.message);
            alert(err.response?.data?.detail || err.response?.data?.message || err.message || 'Action failed');
        } finally {
            setActionLoading(false);
        }
    };

    if (loading) return <div className="flex h-screen items-center justify-center"><Loader2 className="w-10 h-10 animate-spin text-sky-600" /></div>;
    if (!data) return <div className="p-8">Case not found</div>;

    // Handle both I4C dataset structure AND new unified case structure
    // New unified API returns flat case data: case_id, transaction_id, amount, etc.
    const isUnifiedCase = data.case_id !== undefined;
    
    // For unified case structure, data is flat
    // For legacy structure, data is nested in report/complaint/incidents
    const report = isUnifiedCase ? data : (data.report || data.complaint || {});
    const incidents = isUnifiedCase ? [] : (data.incidents || data.transactions || []);
    const workflow = isUnifiedCase ? {} : (data.workflow || {});
    const timeline = isUnifiedCase ? [] : (data.timeline || []);
    const holdActions = isUnifiedCase ? [] : (data.hold_actions || data.holdActions || []);
    
    // Get status - unified case has direct status field
    const caseStatus = isUnifiedCase ? data.status : (workflow.current_state || report.status || 'NEW');
    
    // DEBUG: Log status to console
    console.log('Case status:', caseStatus, 'Raw data.status:', data.status);
    
    // Get SLA risk from API
    const slaRisk = data.sla_risk || 'LOW';
    const slaRemainingHours = data.sla_remaining_hours || 24;
    
    // SLA Risk display config
    const slaRiskConfig: Record<string, { color: string; bg: string; icon: string }> = {
        'LOW': { color: 'text-emerald-700', bg: 'bg-emerald-100', icon: '' },
        'MEDIUM': { color: 'text-amber-700', bg: 'bg-amber-100', icon: '⚠' },
        'HIGH': { color: 'text-rose-700', bg: 'bg-rose-100', icon: '⚠' },
    };
    const slaConfig = slaRiskConfig[slaRisk] || slaRiskConfig['LOW'];
    
    // Get I4C sync status from status updates
    const statusUpdates = data.status_updates || [];
    const i4cSyncStatus: string = (data.i4c_sync_status as string) || (statusUpdates.length > 0 ? 'SYNCED' : 'PENDING');

    return (
        <div className="space-y-8 max-w-7xl mx-auto pb-20">
            <header className="flex justify-between items-center">
                <div className="flex items-center gap-6">
                    <button onClick={() => navigate(-1)} className="p-2 border border-slate-200 rounded-xl hover:bg-white hover:shadow-sm transition-all group">
                        <ArrowLeft className="w-5 h-5 text-slate-500 group-hover:text-slate-900 group-hover:-translate-x-1 transition-all" />
                    </button>
                    <div>
                        <div className="flex items-center gap-3">
                            <h1 className="text-3xl font-black tracking-tighter text-slate-900 font-heading">Signal #{data.case_id || report.complaint_id || report.acknowledgement_no || id}</h1>
                            <span className={cn(
                                "px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-[0.2em] border shadow-sm",
                                caseStatus === 'NEW' ? "bg-slate-50 text-slate-600 border-slate-200" :
                                caseStatus === 'UNDER_REVIEW' ? "bg-amber-50 text-amber-700 border-amber-100" :
                                caseStatus === 'HOLD_INITIATED' ? "bg-orange-50 text-orange-700 border-orange-100" :
                                caseStatus === 'ACTION_SUBMITTED' ? "bg-blue-50 text-blue-700 border-blue-100" :
                                caseStatus === 'CLOSED' ? "bg-emerald-50 text-emerald-700 border-emerald-100" :
                                caseStatus === 'BANK_PENDING' ? "bg-amber-50 text-amber-700 border-amber-100" :
                                caseStatus === 'ROUTED' ? "bg-sky-50 text-sky-700 border-sky-100" :
                                caseStatus === 'RELATED_CONFIRMED' ? "bg-emerald-50 text-emerald-700 border-emerald-100" :
                                caseStatus === 'HOLD_CONFIRMED' ? "bg-green-50 text-green-700 border-green-100" :
                                caseStatus === 'NOT_RELATED' ? "bg-rose-50 text-rose-700 border-rose-100" :
                                caseStatus === 'BANK_CONFIRMED' ? "bg-blue-50 text-blue-700 border-blue-100" :
                                    "bg-slate-50 text-slate-600 border-slate-200"
                            )}>
                                {caseStatus.replace('_', ' ')}
                            </span>
                            {/* I4C Sync Status Indicator */}
                            {i4cSyncStatus && (
                                <span className={cn(
                                    "px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-wider border",
                                    i4cSyncStatus === 'SYNCED' ? "bg-emerald-100 text-emerald-800 border-emerald-200" :
                                    i4cSyncStatus === 'FAILED' ? "bg-rose-100 text-rose-800 border-rose-200" :
                                    i4cSyncStatus === 'PENDING' ? "bg-amber-100 text-amber-800 border-amber-200" :
                                        "bg-slate-100 text-slate-600 border-slate-200"
                                )}>
                                    I4C: {i4cSyncStatus}
                                </span>
                            )}
                        </div>
                        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mt-2 flex items-center gap-2">
                            <Clock className="w-3 h-3 text-sky-500" /> 
                            SLA Response Window: <span className="text-slate-900">{Math.floor(slaRemainingHours)}h {Math.floor((slaRemainingHours % 1) * 60)}m remaining</span>
                            {/* SLA Risk Alert */}
                            <span className={cn(
                                "ml-2 px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-wider border",
                                slaConfig.bg, slaConfig.color
                            )}>
                                SLA Risk: {slaRisk} {slaConfig.icon}
                            </span>
                        </p>
                    </div>
                </div>
                <div className="flex gap-3">
                    {caseStatus === 'ENRICHED' && (
                        <button
                            onClick={handleRoute}
                            disabled={actionLoading}
                            className="btn btn-primary text-sm font-bold flex items-center gap-2"
                        >
                            {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                            Execute Routing
                        </button>
                    )}
                </div>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                <div className="lg:col-span-8 space-y-8">
                    <div className="card">
                        <div className="px-8 py-5 border-b border-slate-100 bg-slate-50/30">
                            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                                <FileText className="w-4 h-4" /> Complaint Data
                            </h3>
                        </div>
                        <div className="p-8 grid grid-cols-3 gap-y-8">
                            <div>
                                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Transaction ID</p>
                                <p className="text-sm font-bold text-slate-900">{data.transaction_id || 'N/A'}</p>
                            </div>
                            <div>
                                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Exposure Amount</p>
                                <p className="text-lg font-black text-slate-900 font-mono tracking-tighter">₹{(data.amount || 0).toLocaleString()}</p>
                            </div>
                            <div>
                                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Payment Mode</p>
                                <p className="text-sm font-bold text-slate-900">{data.payment_mode || 'Unknown'}</p>
                            </div>
                            <div>
                                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">State / District</p>
                                <p className="text-sm font-bold text-slate-900">{data.state || 'N/A'}{data.district ? ` / ${data.district}` : ''}</p>
                            </div>
                            <div>
                                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Source</p>
                                <p className="text-sm font-bold text-slate-900">{data.source_type || 'N/A'}</p>
                            </div>
                            <div>
                                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Assigned Branch</p>
                                <p className="text-sm font-bold text-slate-900">{data.assigned_branch || 'Unassigned'}</p>
                            </div>
                        </div>
                    </div>

                    {/* Transaction Flow / Money Trail Section */}
                    <div className="card">
                        <div className="px-8 py-5 border-b border-slate-100 bg-slate-50/30">
                            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                                <ArrowRightLeft className="w-4 h-4" /> Transaction Flow / Money Trail
                                {/* Hop Indicator */}
                                <span className="ml-2 px-2 py-0.5 bg-sky-100 text-sky-700 rounded text-[10px] font-bold">
                                    {(() => {
                                        const hops = data.transaction_hops || [
                                            { step: 1 },
                                            ...(data.source_type === 'demo' ? [{ step: 2 }] : [])
                                        ];
                                        return `${hops.length} hop${hops.length !== 1 ? 's' : ''} detected`;
                                    })()}
                                </span>
                            </h3>
                        </div>
                        <div className="p-8">
                            {/* Generate simulated transaction hops for demo/I4C cases */}
                            {(() => {
                                // Create simulated money trail based on case data
                                const hops = data.transaction_hops || [
                                    {
                                        step: 1,
                                        from_account: data.payer_account_number ? `****${data.payer_account_number.slice(-4)}` : '****7823',
                                        to_account: '****4521',
                                        payment_mode: data.payment_mode || 'UPI',
                                        amount: data.amount || 250,
                                        timestamp: data.created_at || new Date().toISOString(),
                                        direction: 'Victim → Fraudster'
                                    },
                                    ...(data.source_type === 'demo' ? [{
                                        step: 2,
                                        from_account: '****4521',
                                        to_account: '****8892',
                                        payment_mode: 'IMPS',
                                        amount: data.amount || 250,
                                        timestamp: new Date(Date.now() + 5 * 60000).toISOString(), // 5 mins later
                                        direction: 'Fraudster → Layer 2'
                                    }] : [])
                                ];
                                
                                if (hops.length === 0) {
                                    return (
                                        <div className="text-center py-8 text-slate-400">
                                            <ArrowRightLeft className="w-12 h-12 mx-auto mb-4 opacity-50" />
                                            <p className="text-sm">No transaction flow data available</p>
                                        </div>
                                    );
                                }
                                
                                return (
                                    <div className="space-y-6">
                                        {hops.map((hop: any, index: number) => (
                                            <div key={index} className="relative">
                                                {/* Connection line */}
                                                {index < hops.length - 1 && (
                                                    <div className="absolute left-6 top-14 w-0.5 h-8 bg-slate-200" />
                                                )}
                                                
                                                <div className="flex gap-4">
                                                    {/* Step indicator */}
                                                    <div className="flex-shrink-0 w-12 h-12 bg-sky-100 rounded-full flex items-center justify-center">
                                                        <span className="text-sm font-black text-sky-600">{hop.step}</span>
                                                    </div>
                                                    
                                                    {/* Transaction details */}
                                                    <div className="flex-1 bg-slate-50 rounded-xl p-4 border border-slate-100">
                                                        <div className="flex items-center justify-between mb-3">
                                                            <span className="text-xs font-black text-slate-500 uppercase tracking-widest">
                                                                Step {hop.step}
                                                            </span>
                                                            <span className="text-[10px] px-2 py-0.5 bg-slate-200 text-slate-600 rounded font-medium">
                                                                {hop.direction}
                                                            </span>
                                                        </div>
                                                        
                                                        <div className="grid grid-cols-2 gap-4">
                                                            <div>
                                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">From Account</p>
                                                                <p className="text-sm font-bold text-slate-900 font-mono">{hop.from_account}</p>
                                                            </div>
                                                            <div>
                                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">To Account</p>
                                                                <p className="text-sm font-bold text-slate-900 font-mono">{hop.to_account}</p>
                                                            </div>
                                                            <div>
                                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Payment Mode</p>
                                                                <p className="text-sm font-bold text-slate-900">{hop.payment_mode}</p>
                                                            </div>
                                                            <div>
                                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Amount</p>
                                                                <p className="text-lg font-black text-slate-900 font-mono tracking-tighter">₹{hop.amount?.toLocaleString()}</p>
                                                            </div>
                                                        </div>
                                                        
                                                        <div className="mt-3 pt-3 border-t border-slate-200">
                                                            <p className="text-[10px] text-slate-400 font-mono">
                                                                {hop.timestamp ? new Date(hop.timestamp).toLocaleString() : 'N/A'}
                                                            </p>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                );
                            })()}
                        </div>
                    </div>

                    <div className="card">
                        <div className="p-8 relative">
                            <div className="absolute -top-4 left-8 px-4 py-2 bg-white border border-slate-200 rounded-xl shadow-sm">
                                <div className="flex items-center gap-3">
                                    <ShieldCheck className="w-4 h-4 text-emerald-500" />
                                    <span className="text-xs font-black text-slate-900 uppercase tracking-widest">Case Assignment</span>
                                </div>
                            </div>
                            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-8">
                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 bg-sky-50 rounded-2xl flex items-center justify-center">
                                        <Building2 className="w-6 h-6 text-sky-600" />
                                    </div>
                                    <div>
                                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Assigned Branch</p>
                                        <p className="text-lg font-black text-slate-900">{data.assigned_branch || 'Not Assigned'}</p>
                                    </div>
                                </div>
                                <div className="text-right flex flex-col justify-center">
                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Case Source</p>
                                    <p className="text-4xl font-black text-emerald-600 tracking-tighter">{data.source_type === 'demo' ? 'DEMO' : 'I4C'}</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Transactions Section - I4C Incidents */}
                    {incidents.length > 0 && (
                        <div className="card">
                            <div className="px-8 py-5 border-b border-slate-100 bg-slate-50/30">
                                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                                    <CreditCard className="w-4 h-4" /> Transaction Details ({incidents.length})
                                </h3>
                            </div>
                            <div className="p-8">
                                <div className="space-y-4">
                                    {incidents.map((incident: any, index: number) => (
                                        <div key={incident.id || index} className="flex items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-100">
                                            <div className="flex items-center gap-4">
                                                <div className="w-10 h-10 bg-sky-100 rounded-lg flex items-center justify-center">
                                                    <ArrowRightLeft className="w-5 h-5 text-sky-600" />
                                                </div>
                                                <div>
                                                    <p className="text-sm font-bold text-slate-900">RRN: {incident.rrn || 'N/A'}</p>
                                                    <p className="text-xs text-slate-500">{incident.transaction_date || 'N/A'} {incident.transaction_time || ''}</p>
                                                    <p className="text-xs text-slate-400">To: {incident.payee_bank || 'N/A'}</p>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <p className="text-lg font-black text-slate-900 font-mono">₹{(incident.amount || 0).toLocaleString()}</p>
                                                {incident.disputed_amount > 0 && (
                                                    <p className="text-xs text-rose-600 font-medium">Disputed: ₹{incident.disputed_amount.toLocaleString()}</p>
                                                )}
                                                {incident.layer ? (
                                                    <span className="text-[10px] px-2 py-0.5 bg-slate-200 text-slate-600 rounded-full">Layer {incident.layer}</span>
                                                ) : (
                                                    <span className="text-[10px] px-2 py-0.5 bg-slate-100 text-slate-400 rounded-full">Layer N/A</span>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    <div className="card">
                        <div className="px-8 py-5 border-b border-slate-100 bg-slate-50/30">
                            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                                <History className="w-4 h-4" /> Case Timeline
                            </h3>
                        </div>
                        <div className="p-8 space-y-6">
                            {/* Timeline Events from API */}
                            {data?.timeline?.length > 0 ? (
                                data.timeline.map((event: any, index: number) => (
                                    <div key={event.id || index} className="flex gap-4">
                                        <div className={cn(
                                            "w-2 h-2 rounded-full mt-1.5",
                                            event.event_type?.includes('HOLD') ? "bg-orange-500" :
                                            event.event_type?.includes('CONFIRM') ? "bg-emerald-500" :
                                            event.event_type?.includes('FREEZE') ? "bg-blue-500" :
                                            event.event_type?.includes('NOT_RELATED') ? "bg-rose-500" :
                                            event.event_type?.includes('ASSIGNED') ? "bg-indigo-500" :
                                            event.event_type?.includes('CREATED') ? "bg-sky-500" :
                                                "bg-slate-500"
                                        )} />
                                        <div>
                                            <p className={cn(
                                                "text-xs font-bold uppercase tracking-widest",
                                                event.event_type?.includes('HOLD') ? "text-orange-700" :
                                                event.event_type?.includes('CONFIRM') ? "text-emerald-700" :
                                                event.event_type?.includes('FREEZE') ? "text-blue-700" :
                                                event.event_type?.includes('NOT_RELATED') ? "text-rose-700" :
                                                event.event_type?.includes('ASSIGNED') ? "text-indigo-700" :
                                                event.event_type?.includes('CREATED') ? "text-sky-700" :
                                                    "text-slate-700"
                                            )}>
                                                {event.event_type?.replace(/_/g, ' ') || 'Case Event'}
                                            </p>
                                            <p className="text-sm text-slate-600 font-medium">{event.description || 'No description'}</p>
                                            <p className="text-[10px] text-slate-400 mt-1 font-mono">{event.created_at ? new Date(event.created_at).toLocaleString() : 'N/A'}</p>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <div className="text-center py-8 text-slate-400">
                                    <History className="w-12 h-12 mx-auto mb-4 opacity-50" />
                                    <p className="text-sm">No timeline events yet</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Response Cycle Section */}
                    {data?.response_cycle && (
                        <div className="card">
                            <div className="px-8 py-5 border-b border-slate-100 bg-slate-50/30">
                                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                                    <RefreshCw className="w-4 h-4" /> Response Cycle
                                </h3>
                            </div>
                            <div className="p-8">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Request ID</p>
                                        <p className="text-sm font-mono text-slate-900">{data.response_cycle.request_id || 'N/A'}</p>
                                    </div>
                                    <div>
                                        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Job ID</p>
                                        <p className="text-sm font-mono text-slate-900">{data.response_cycle.job_id || 'N/A'}</p>
                                    </div>
                                    <div>
                                        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Status Code</p>
                                        <p className="text-sm font-bold text-slate-900">{data.response_cycle.status_code || 'N/A'}</p>
                                    </div>
                                    <div>
                                        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Response Code</p>
                                        <p className="text-sm font-bold text-slate-900">{data.response_cycle.response_code || 'N/A'}</p>
                                    </div>
                                    <div>
                                        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Sent At</p>
                                        <p className="text-sm text-slate-600">{data.response_cycle.sent_at ? new Date(data.response_cycle.sent_at).toLocaleString() : 'N/A'}</p>
                                    </div>
                                    <div>
                                        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Received At</p>
                                        <p className="text-sm text-slate-600">{data.response_cycle.received_at ? new Date(data.response_cycle.received_at).toLocaleString() : 'N/A'}</p>
                                    </div>
                                    <div>
                                        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Transaction Count</p>
                                        <p className="text-sm font-bold text-slate-900">{data.response_cycle.transaction_count || 0}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Status Payload Section */}
                    {data?.status_payload && (
                        <div className="card">
                            <div className="px-8 py-5 border-b border-slate-100 bg-slate-50/30">
                                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                                    <Code className="w-4 h-4" /> Status Payload (Sent to I4C)
                                </h3>
                            </div>
                            <div className="p-8">
                                <div className="space-y-4">
                                    <div className="flex items-center gap-4">
                                        <div className="px-3 py-1 bg-emerald-100 text-emerald-700 rounded text-xs font-bold uppercase">
                                            {data.status_payload.method}
                                        </div>
                                        <p className="text-sm font-mono text-slate-600">{data.status_payload.endpoint}</p>
                                    </div>
                                    {data.status_payload.headers && (
                                        <div>
                                            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Headers</p>
                                            <pre className="bg-slate-100 p-3 rounded-lg text-xs font-mono text-slate-700 overflow-x-auto">
                                                {JSON.stringify(data.status_payload.headers, null, 2)}
                                            </pre>
                                        </div>
                                    )}
                                    {data.status_payload.body && (
                                        <div>
                                            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Body</p>
                                            <pre className="bg-slate-900 text-slate-100 p-4 rounded-lg text-xs font-mono overflow-x-auto max-h-64 overflow-y-auto">
                                                {JSON.stringify(data.status_payload.body, null, 2)}
                                            </pre>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Evidence & Documents Section */}
                    <div className="card">
                        <div className="px-8 py-5 border-b border-slate-100 bg-slate-50/30 flex items-center justify-between">
                            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                                <FileText className="w-4 h-4" /> Evidence & Documents ({data?.evidence?.length || 0})
                            </h3>
                            <div className="flex items-center gap-2">
                                <select
                                    value={selectedFileType}
                                    onChange={(e) => setSelectedFileType(e.target.value)}
                                    className="text-xs border border-slate-200 rounded-lg px-2 py-1 bg-white"
                                >
                                    <option value="TRANSACTION_SCREENSHOT">Transaction Screenshot</option>
                                    <option value="BANK_STATEMENT">Bank Statement</option>
                                    <option value="CBS_CONFIRMATION">CBS Confirmation</option>
                                    <option value="INVESTIGATION_NOTE">Investigation Note</option>
                                </select>
                                <label className="btn btn-secondary text-xs flex items-center gap-2 cursor-pointer">
                                    <Upload className="w-4 h-4" />
                                    {uploading ? 'Uploading...' : 'Upload'}
                                    <input
                                        type="file"
                                        className="hidden"
                                        onChange={handleEvidenceUpload}
                                        disabled={uploading}
                                    />
                                </label>
                            </div>
                        </div>
                        <div className="p-8">
                            {data?.evidence?.length > 0 ? (
                                <div className="space-y-3">
                                    {data.evidence.map((item: any, idx: number) => (
                                        <div key={idx} className="flex items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-100">
                                            <div className="flex items-center gap-4">
                                                <div className="w-10 h-10 bg-violet-100 rounded-lg flex items-center justify-center">
                                                    <FileText className="w-5 h-5 text-violet-600" />
                                                </div>
                                                <div>
                                                    <p className="text-sm font-bold text-slate-900">{item.file_name || 'Document'}</p>
                                                    <p className="text-xs text-slate-500">
                                                        {item.file_type || 'Document'} • Uploaded {item.uploaded_at ? new Date(item.uploaded_at).toLocaleDateString() : 'N/A'}
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <a
                                                    href={item.file_url || '#'}
                                                    className="p-2 hover:bg-slate-200 rounded-lg text-slate-600"
                                                    title="Download"
                                                >
                                                    <Download className="w-4 h-4" />
                                                </a>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-8">
                                    <FileText className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                                    <p className="text-slate-500 text-sm">No evidence uploaded yet</p>
                                    <p className="text-slate-400 text-xs mt-1">Upload transaction screenshots, bank statements, or investigation notes</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                <div className="lg:col-span-4 space-y-8">
                    <div className="card bg-slate-900 border-slate-800 shadow-2xl sticky top-8">
                        <div className="p-8">
                            <h3 className="text-xs font-bold text-sky-400 uppercase tracking-widest mb-6 flex items-center gap-2">
                                <ShieldAlert className="w-4 h-4" /> Bank Action Playbook
                            </h3>
                            <div className="space-y-4">
                                <textarea
                                    value={remarks}
                                    onChange={(e) => setRemarks(e.target.value)}
                                    placeholder="Enter status remarks..."
                                    className="w-full h-24 bg-white/5 border border-white/10 rounded-xl p-3 text-xs text-white placeholder:text-slate-600 outline-none focus:ring-1 focus:ring-sky-500/50 resize-none mb-2"
                                ></textarea>

                                <div className="space-y-1 mb-4">
                                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest pl-1">Actual Hold Amount (INR)</label>
                                    <input
                                        type="number"
                                        value={holdAmount}
                                        onChange={(e) => {
                                            const val = parseFloat(e.target.value);
                                            setHoldAmount(val);
                                            // Validate hold amount
                                            const exposure = data?.amount || 0;
                                            if (val > exposure) {
                                                setHoldAmountError(`Hold amount cannot exceed exposure amount of ₹${exposure.toLocaleString()}`);
                                            } else {
                                                setHoldAmountError('');
                                            }
                                        }}
                                        className={cn(
                                            "w-full bg-white/5 border rounded-xl px-3 py-2 text-sm text-white font-mono outline-none focus:ring-1",
                                            holdAmountError ? "border-rose-500 focus:ring-rose-500/50" : "border-white/10 focus:ring-emerald-500/50"
                                        )}
                                    />
                                    {holdAmountError && (
                                        <p className="text-[10px] text-rose-400 mt-1">{holdAmountError}</p>
                                    )}
                                </div>

                                {/* Action buttons shown for active cases - based on new lifecycle */}
                                {(caseStatus === 'NEW' || caseStatus === 'ASSIGNED' || caseStatus === 'UNDER_REVIEW' || caseStatus === 'HOLD') && (
                                    <button
                                        onClick={() => handleBankResponse('confirm')}
                                        disabled={actionLoading}
                                        className="w-full btn btn-primary bg-emerald-600 border-none h-12 text-xs font-black uppercase tracking-widest hover:bg-emerald-500 shadow-emerald-500/20"
                                    >
                                        {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : 'Confirm Related'}
                                    </button>
                                )}

                                {(caseStatus === 'NEW' || caseStatus === 'ASSIGNED' || caseStatus === 'UNDER_REVIEW' || caseStatus === 'HOLD') && (
                                    <button
                                        onClick={() => handleBankResponse('hold')}
                                        disabled={actionLoading || !!holdAmountError}
                                        className="w-full btn bg-amber-600 text-white border-none h-12 text-xs font-black uppercase tracking-widest hover:bg-amber-500 shadow-amber-500/20 disabled:opacity-50"
                                    >
                                        {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : 'Initiate Hold / Freeze'}
                                    </button>
                                )}

                                {(caseStatus === 'NEW' || caseStatus === 'ASSIGNED' || caseStatus === 'UNDER_REVIEW' || caseStatus === 'HOLD') && (
                                    <button
                                        onClick={() => handleBankResponse('not_related')}
                                        disabled={actionLoading}
                                        className="w-full btn bg-rose-600 text-white border-none h-12 text-xs font-black uppercase tracking-widest hover:bg-rose-500 shadow-rose-500/20"
                                    >
                                        {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : 'Mark Not Related'}
                                    </button>
                                )}
                                
                                {/* Show message when case is in final state */}
                                {['HOLD_INITIATED', 'ACTION_SUBMITTED', 'CLOSED', 'NOT_RELATED', 'RECONCILED'].includes(caseStatus) && (
                                    <div className="p-4 bg-slate-800 rounded-xl text-center">
                                        <p className="text-xs text-slate-400">Case action completed</p>
                                        <p className="text-sm font-bold text-slate-200 mt-1">Status: {caseStatus.replace('_', ' ')}</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CaseDetail;
