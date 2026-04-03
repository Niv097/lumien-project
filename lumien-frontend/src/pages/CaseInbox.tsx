import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
    Search,
    Filter,
    ChevronRight,
    FileDown,
    Loader2,
    Building2
} from 'lucide-react';
import { casesApi } from '../api';
import { cn } from '../utils/cn';

interface Case {
    id: number;
    case_id: string;
    transaction_id: string;
    amount: number;
    payment_mode: string;
    payer_account_number: string;
    payer_bank: string;  // Victim's bank - visible
    mobile_number: string;
    district: string;
    state: string;
    status: string;
    source_type: string;
    created_at: string;
    // NOTE: Receiver bank is intentionally NOT included - hidden from UI per spec
}

const CaseInbox: React.FC = () => {
    const [cases, setCases] = useState<Case[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [branchName, setBranchName] = useState<string>('');
    const [selectedStatus, setSelectedStatus] = useState<string>('');

    const userBranchId = localStorage.getItem('lumien_branch_id');
    const userBankName = localStorage.getItem('lumien_bank_name') || '';
    const userRoles = JSON.parse(localStorage.getItem('lumien_roles') || '[]');
    const isAdmin = userRoles.some((r: string) => 
        ["Lumien Super Admin", "Audit & Compliance Officer", "Lumien Operations Manager"].includes(r)
    );

    const fetchCases = async () => {
        setLoading(true);
        try {
            const params: any = {};
            if (selectedStatus) {
                params.status = selectedStatus;
            }
            
            // Use new unified cases API - handles branch visibility automatically
            const res = await casesApi.getCases(params);
            setCases(res.data.cases || []);
            setError(null);
        } catch (err: any) {
            console.error('Failed to fetch cases:', err);
            setError(err.message || 'Failed to load cases');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        const storedBranchName = localStorage.getItem('lumien_branch_name');
        if (storedBranchName) {
            setBranchName(storedBranchName);
        }
        fetchCases();
    }, []);

    useEffect(() => {
        fetchCases();
    }, [selectedStatus]);

    const statusOptions = [
        { value: '', label: 'All Statuses' },
        { value: 'NEW', label: 'New' },
        { value: 'ASSIGNED', label: 'Assigned' },
        { value: 'UNDER_REVIEW', label: 'Under Review' },
        { value: 'HOLD', label: 'Hold' },
        { value: 'FROZEN', label: 'Frozen' },
        { value: 'CONFIRMED', label: 'Confirmed' },
        { value: 'NOT_RELATED', label: 'Not Related' },
        { value: 'RECONCILED', label: 'Reconciled' },
        { value: 'CLOSED', label: 'Closed' },
    ];

    const newCasesCount = cases.filter(c => c.status === 'NEW').length;

    if (error) {
        return (
            <div className="p-8">
                <div className="bg-red-50 border border-red-200 rounded-lg p-6">
                    <h2 className="text-red-700 font-bold mb-2">Error Loading Case Inbox</h2>
                    <p className="text-red-600">{error}</p>
                    <button 
                        onClick={() => window.location.reload()}
                        className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                    >
                        Reload Page
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-8 max-w-7xl mx-auto">
            <header className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-slate-900 font-heading">Intelligence Repository</h1>
                    <p className="text-slate-500 mt-1">
                        {isAdmin ? 'Universal view of all complaints across the Lumien intermediary layer.' : 
                         branchName ? `Cases for ${branchName}` : 'Cases for your branch'}
                    </p>
                </div>
                <div className="flex gap-3">
                    {newCasesCount > 0 && (
                        <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-100 text-amber-700 rounded-lg text-xs font-bold animate-pulse">
                            <span className="w-2 h-2 bg-amber-500 rounded-full"></span>
                            {newCasesCount} New Case{newCasesCount > 1 ? 's' : ''} Pending
                        </div>
                    )}
                    <button className="btn btn-secondary flex items-center gap-2 text-sm font-bold">
                        <FileDown className="w-4 h-4" /> Export Ledger
                    </button>
                    <button
                        onClick={fetchCases}
                        className="btn btn-primary flex items-center gap-2 text-sm font-bold"
                    >
                        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                        Refresh Ledger
                    </button>
                </div>
            </header>

            <div className="card p-4">
                <div className="flex flex-wrap gap-4 items-center">
                    {!isAdmin && (
                        <div className="flex items-center gap-2">
                            <Building2 className="w-4 h-4 text-slate-400" />
                            <span className="text-sm font-medium text-slate-700">
                                {branchName || userBankName || 'Your Branch'}
                            </span>
                        </div>
                    )}

                    <div className="flex items-center gap-2">
                        <Filter className="w-4 h-4 text-slate-400" />
                        <select
                            value={selectedStatus}
                            onChange={(e) => setSelectedStatus(e.target.value)}
                            className="bg-white border border-slate-200 rounded-lg px-3 py-2 text-sm font-medium focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 outline-none"
                        >
                            {statusOptions.map(opt => (
                                <option key={opt.value} value={opt.value}>
                                    {opt.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    {selectedStatus && (
                        <button
                            onClick={() => setSelectedStatus('')}
                            className="text-sm text-sky-600 hover:text-sky-700 font-medium"
                        >
                            Clear Filter
                        </button>
                    )}
                </div>
            </div>

            <div className="card">
                <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex gap-4">
                    <div className="relative flex-1">
                        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                        <input
                            type="text"
                            placeholder="Search by Complaint ID, Bank, or Transaction..."
                            className="w-full pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 transition-all font-medium"
                        />
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="border-b border-slate-100 bg-slate-50/30">
                                <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Case ID</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Transaction ID</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">State / District</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Payment Mode</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Amount</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Status</th>
                                <th className="px-6 py-4"></th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {loading ? (
                                <tr>
                                    <td colSpan={7} className="px-6 py-20 text-center">
                                        <Loader2 className="w-8 h-8 animate-spin text-sky-600 mx-auto" />
                                        <p className="text-sm text-slate-500 mt-4 font-bold">Synchronizing Intel Ledger...</p>
                                    </td>
                                </tr>
                            ) : cases.length === 0 ? (
                                <tr>
                                    <td colSpan={7} className="px-6 py-20 text-center">
                                        <p className="text-sm text-slate-500 font-bold">No active cases found. Pull data from I4C Portal on Dashboard.</p>
                                    </td>
                                </tr>
                            ) : cases.map((c) => (
                                <tr key={c.id} className={cn(
                                    "transition-all cursor-pointer group",
                                    c.status === 'NEW' 
                                        ? "bg-amber-50/60 hover:bg-amber-100/80 border-l-4 border-amber-500" 
                                        : "hover:bg-slate-50/80"
                                )}>
                                    <td className="px-6 py-5">
                                        <p className="text-sm font-bold text-sky-700 tracking-tight">{c.case_id}</p>
                                        <p className="text-[10px] text-slate-400 mt-0.5">
                                            {c.created_at ? new Date(c.created_at).toLocaleString('en-IN', { 
                                                day: '2-digit', 
                                                month: 'short', 
                                                year: 'numeric'
                                            }) : 'N/A'}
                                        </p>
                                        {c.source_type === 'demo' && (
                                            <span className="text-[9px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded">DEMO</span>
                                        )}
                                    </td>
                                    <td className="px-6 py-5">
                                        <p className="text-sm font-medium text-slate-900">{c.transaction_id}</p>
                                        <p className="text-[10px] text-slate-400">{c.payer_account_number}</p>
                                    </td>
                                    <td className="px-6 py-5">
                                        <p className="text-sm font-medium text-slate-700">{c.state}</p>
                                        {c.district && (
                                            <p className="text-[10px] text-slate-400">{c.district}</p>
                                        )}
                                    </td>
                                    <td className="px-6 py-5 text-sm font-medium text-slate-600">{c.payment_mode}</td>
                                    <td className="px-6 py-5 text-sm font-black text-slate-900 font-mono tracking-tighter">₹{c.amount?.toLocaleString()}</td>
                                    <td className="px-6 py-5">
                                        <span className={cn(
                                            "inline-flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-black uppercase tracking-widest",
                                            c.status === 'NEW' && "bg-amber-100 text-amber-700 border border-amber-300",
                                            c.status === 'ASSIGNED' && "bg-sky-50 text-sky-700",
                                            c.status === 'UNDER_REVIEW' && "bg-blue-50 text-blue-700",
                                            c.status === 'HOLD' && "bg-orange-50 text-orange-700",
                                            c.status === 'FROZEN' && "bg-purple-50 text-purple-700",
                                            c.status === 'CONFIRMED' && "bg-emerald-50 text-emerald-700",
                                            c.status === 'NOT_RELATED' && "bg-rose-50 text-rose-700",
                                            c.status === 'RECONCILED' && "bg-green-50 text-green-700",
                                            c.status === 'CLOSED' && "bg-slate-100 text-slate-600"
                                        )}>
                                            {c.status === 'NEW' && (
                                                <span className="w-1.5 h-1.5 bg-amber-500 rounded-full animate-pulse"></span>
                                            )}
                                            {c.status?.replace('_', ' ')}
                                        </span>
                                    </td>
                                    <td className="px-6 py-5">
                                        <Link
                                            to={`/case/${c.case_id}`}
                                            className="p-2 text-slate-400 hover:text-sky-600 hover:bg-sky-50 rounded-lg transition-all inline-block"
                                        >
                                            <ChevronRight className="w-4 h-4" />
                                        </Link>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default CaseInbox;
