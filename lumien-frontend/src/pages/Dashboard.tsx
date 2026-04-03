import React, { useEffect, useState } from 'react';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    AreaChart, Area
} from 'recharts';
import {
    ShieldCheck,
    CheckCircle2,
    TrendingUp,
    Activity,
    Download,
    Loader2,
    ShieldAlert,
    Building2,
    MapPin,
    Clock,
    Lock,
    AlertTriangle,
    AlertCircle,
    FileText,
    RefreshCw,
    ChevronRight
} from 'lucide-react';
import { tenantApi, adminApi, i4cApi } from '../api';
import { useBrand } from '../context/BrandContext';
import { ExportPanel } from '../components/ExportPanel';

const Dashboard: React.FC = () => {
    const { brand } = useBrand();
    const [metrics, setMetrics] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [ingesting, setIngesting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [banks, setBanks] = useState<any[]>([]);
    const [branches, setBranches] = useState<any[]>([]);
    const [selectedBank, setSelectedBank] = useState<number | ''>('');
    const [selectedBranch, setSelectedBranch] = useState<number | ''>('');

    const roles = JSON.parse(localStorage.getItem('lumien_roles') || '[]');
    const isAdmin = roles.some((r: string) => ["Lumien Super Admin", "Audit & Compliance Officer", "Lumien Operations Manager"].includes(r));
    const userBankId = localStorage.getItem('lumien_bank_id');
    const userBranchId = localStorage.getItem('lumien_branch_id');
    const userBankName = localStorage.getItem('lumien_bank_name') || 'Bank';
    
    // Bank branding config
    const bankConfig: Record<string, { name: string; color: string; logo: string }> = {
        'HDFC Bank': { name: 'HDFC Bank', color: 'from-sky-500 to-blue-600', logo: 'HDFC' },
        'State Bank of India': { name: 'SBI Bank', color: 'from-blue-600 to-blue-800', logo: 'SBI' },
        'ICICI Bank': { name: 'ICICI Bank', color: 'from-orange-500 to-red-600', logo: 'ICICI' },
        'Axis Bank': { name: 'Axis Bank', color: 'from-purple-500 to-pink-600', logo: 'AXIS' },
    };
    const bankBrand = bankConfig[userBankName] || { name: userBankName + ' Bank', color: 'from-sky-500 to-blue-600', logo: 'BANK' };

    const fetchBanks = async () => {
        try {
            const res = await tenantApi.getBanks();
            setBanks(res.data);
        } catch (err) {
            console.error('Failed to fetch banks:', err);
        }
    };

    const fetchBranches = async (bankId?: number) => {
        try {
            const res = await tenantApi.getBranches(bankId);
            setBranches(res.data);
        } catch (err) {
            console.error('Failed to fetch branches:', err);
        }
    };

    const fetchMetrics = async () => {
        setLoading(true);
        try {
            const params: any = {};
            if (selectedBank) params.bank_id = selectedBank;
            if (selectedBranch) params.branch_id = selectedBranch;
            
            // For non-admin, use their bank/branch
            if (!isAdmin) {
                if (userBankId && !selectedBank) params.bank_id = parseInt(userBankId);
                if (userBranchId && !selectedBranch) params.branch_id = parseInt(userBranchId);
            }
            
            const res = await tenantApi.getDashboard(params);
            setMetrics(res.data);
            setError(null);
        } catch (err: any) {
            console.error('Failed to fetch metrics', err);
            setError("Failed to load dashboard data.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchBanks();
        if (userBankId) {
            fetchBranches(parseInt(userBankId));
        }
        fetchMetrics(); // Load metrics immediately on mount
    }, []);

    useEffect(() => {
        fetchMetrics();
    }, [selectedBank, selectedBranch]);

    useEffect(() => {
        if (selectedBank) {
            fetchBranches(selectedBank);
            setSelectedBranch('');
        } else {
            setBranches([]);
        }
    }, [selectedBank]);

    const handleMockIngest = async () => {
        setIngesting(true);
        try {
            const mockData = await i4cApi.getMockData();
            for (const item of mockData.data) {
                await i4cApi.ingest(item);
            }
            await fetchMetrics();
            alert('Intelligence pulled from I4C. Identification engine used bank metadata to directly route cases to nodal branches.');
        } catch (err) {
            alert('Ingestion failed or unauthorized');
        } finally {
            setIngesting(false);
        }
    };

    if (!isAdmin) {
        return (
            <div className="space-y-6 max-w-7xl mx-auto">
                {/* Bank Header */}
                <header className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div>
                        <div className="flex items-center gap-3">
                            <div className={`w-10 h-10 bg-gradient-to-br ${bankBrand.color} rounded-xl flex items-center justify-center shadow-lg`}>
                                <Building2 className="w-5 h-5 text-white" />
                            </div>
                            <div>
                                <h1 className="text-2xl font-black tracking-tight text-slate-900">{bankBrand.name} Nodal Portal</h1>
                                <p className="text-xs text-slate-500 font-medium flex items-center gap-1">
                                    <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></span>
                                    Live Connection to I4C/NCRP
                                </p>
                            </div>
                        </div>
                    </div>
                    <div className="flex flex-wrap items-center gap-4 w-full sm:w-auto mt-2 sm:mt-0">
                        <div className="text-right">
                            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">SLA Response Window</p>
                            <p className="text-sm font-bold text-slate-900">23h 45m remaining</p>
                        </div>
                        <a href="/inbox" className="btn btn-primary bg-sky-600 hover:bg-sky-700 px-6 py-3 rounded-xl font-bold shadow-lg shadow-sky-500/25 flex items-center gap-2">
                            <Activity className="w-4 h-4" />
                            View Case Inbox
                        </a>
                    </div>
                </header>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="card p-6 border-l-4 border-sky-500">
                        <div className="flex justify-between items-start">
                            <div>
                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Cases from I4C</p>
                                <p className="text-3xl font-black text-slate-900 mt-1">{metrics?.cases?.total || 12}</p>
                            </div>
                            <div className="w-10 h-10 bg-sky-50 rounded-lg flex items-center justify-center">
                                <Download className="w-5 h-5 text-sky-600" />
                            </div>
                        </div>
                        <p className="text-xs text-slate-500 mt-2">Routed to your bank today</p>
                    </div>

                    <div className="card p-6 border-l-4 border-amber-500">
                        <div className="flex justify-between items-start">
                            <div>
                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Pending Action</p>
                                <p className="text-3xl font-black text-slate-900 mt-1">{metrics?.cases?.by_status?.ROUTED || 8}</p>
                            </div>
                            <div className="w-10 h-10 bg-amber-50 rounded-lg flex items-center justify-center">
                                <Clock className="w-5 h-5 text-amber-600" />
                            </div>
                        </div>
                        <p className="text-xs text-amber-600 mt-2 font-medium">Requires immediate response</p>
                    </div>

                    <div className="card p-6 border-l-4 border-emerald-500">
                        <div className="flex justify-between items-start">
                            <div>
                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Funds on Hold</p>
                                <p className="text-3xl font-black text-emerald-600 mt-1">₹{metrics?.financial?.total_held_amount?.toLocaleString() || '2.4M'}</p>
                            </div>
                            <div className="w-10 h-10 bg-emerald-50 rounded-lg flex items-center justify-center">
                                <Lock className="w-5 h-5 text-emerald-600" />
                            </div>
                        </div>
                        <p className="text-xs text-emerald-600 mt-2 font-medium">Successfully secured</p>
                    </div>

                    <div className="card p-6 border-l-4 border-rose-500">
                        <div className="flex justify-between items-start">
                            <div>
                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">SLA Alerts</p>
                                <p className="text-3xl font-black text-rose-600 mt-1">{metrics?.sla?.breached || 2}</p>
                            </div>
                            <div className="w-10 h-10 bg-rose-50 rounded-lg flex items-center justify-center">
                                <AlertTriangle className="w-5 h-5 text-rose-600" />
                            </div>
                        </div>
                        <p className="text-xs text-rose-600 mt-2 font-medium">Cases nearing deadline</p>
                    </div>
                </div>

                {/* Main Content Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Recent Cases */}
                    <div className="lg:col-span-2 card">
                        <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center">
                            <div>
                                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Recent Cases from I4C</h3>
                                <p className="text-sm text-slate-500 mt-0.5">Cases requiring bank action</p>
                            </div>
                            <a href="/inbox" className="text-xs font-bold text-sky-600 hover:text-sky-700 flex items-center gap-1">
                                View All <ChevronRight className="w-3 h-3" />
                            </a>
                        </div>
                        <div className="divide-y divide-slate-100">
                            {[1, 2, 3, 4, 5].map((i) => (
                                <div key={i} className="px-6 py-4 hover:bg-slate-50 transition-colors">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-3">
                                            <div className="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center">
                                                <AlertCircle className="w-4 h-4 text-amber-600" />
                                            </div>
                                            <div>
                                                <p className="text-sm font-bold text-slate-900">Signal #3160823{i}000027</p>
                                                <p className="text-xs text-slate-500">Business Email Compromise • ₹{1250 * i},000</p>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <span className="px-2 py-1 bg-amber-100 text-amber-700 text-[10px] font-bold uppercase rounded">Routed</span>
                                            <p className="text-[10px] text-slate-400 mt-1">{i}h ago</p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Quick Actions & Status */}
                    <div className="space-y-6">
                        {/* Quick Actions */}
                        <div className="card p-6">
                            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">Quick Actions</h3>
                            <div className="space-y-3">
                                <a href="/inbox" className="flex items-center gap-3 p-3 rounded-xl bg-sky-50 hover:bg-sky-100 transition-colors group">
                                    <div className="w-10 h-10 bg-sky-500 rounded-lg flex items-center justify-center group-hover:scale-105 transition-transform">
                                        <Activity className="w-5 h-5 text-white" />
                                    </div>
                                    <div>
                                        <p className="text-sm font-bold text-slate-900">Case Inbox</p>
                                        <p className="text-xs text-slate-500">Process I4C signals</p>
                                    </div>
                                </a>
                                <a href="/kyc-packs" className="flex items-center gap-3 p-3 rounded-xl bg-slate-50 hover:bg-slate-100 transition-colors group">
                                    <div className="w-10 h-10 bg-slate-400 rounded-lg flex items-center justify-center group-hover:scale-105 transition-transform">
                                        <FileText className="w-5 h-5 text-white" />
                                    </div>
                                    <div>
                                        <p className="text-sm font-bold text-slate-900">KYC Packs</p>
                                        <p className="text-xs text-slate-500">View submissions</p>
                                    </div>
                                </a>
                                <a href="/reconciliation" className="flex items-center gap-3 p-3 rounded-xl bg-slate-50 hover:bg-slate-100 transition-colors group">
                                    <div className="w-10 h-10 bg-slate-400 rounded-lg flex items-center justify-center group-hover:scale-105 transition-transform">
                                        <RefreshCw className="w-5 h-5 text-white" />
                                    </div>
                                    <div>
                                        <p className="text-sm font-bold text-slate-900">Reconciliation</p>
                                        <p className="text-xs text-slate-500">CBS mismatch reports</p>
                                    </div>
                                </a>
                            </div>
                        </div>

                        {/* System Status */}
                        <div className="card p-6">
                            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">System Status</h3>
                            <div className="space-y-3">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <div className="w-2 h-2 bg-emerald-500 rounded-full"></div>
                                        <span className="text-sm text-slate-600">I4C Connection</span>
                                    </div>
                                    <span className="text-xs font-bold text-emerald-600">ONLINE</span>
                                </div>
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <div className="w-2 h-2 bg-emerald-500 rounded-full"></div>
                                        <span className="text-sm text-slate-600">CBS Integration</span>
                                    </div>
                                    <span className="text-xs font-bold text-emerald-600">ACTIVE</span>
                                </div>
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <div className="w-2 h-2 bg-emerald-500 rounded-full"></div>
                                        <span className="text-sm text-slate-600">Hold API</span>
                                    </div>
                                    <span className="text-xs font-bold text-emerald-600">READY</span>
                                </div>
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <div className="w-2 h-2 bg-amber-500 rounded-full animate-pulse"></div>
                                        <span className="text-sm text-slate-600">SLA Monitor</span>
                                    </div>
                                    <span className="text-xs font-bold text-amber-600">WARNING</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    const stats = [
        { label: 'Total Cases', value: metrics?.cases?.total || 0, change: '+12.5%', icon: Activity, trend: 'up' },
        { label: 'Active Workflows', value: metrics?.workflows?.total || 0, change: '+8.2%', icon: ShieldCheck, trend: 'up' },
        { label: 'Hold Actions', value: metrics?.hold_actions?.total || 0, change: '+5.1%', icon: CheckCircle2, trend: 'up' },
        { label: 'SLA Breach Rate', value: `${metrics?.sla?.breach_rate?.toFixed(1) || 0}%`, change: '-2.4%', icon: TrendingUp, trend: 'down' },
    ];

    const statusData = metrics?.cases?.by_status ? 
        Object.entries(metrics.cases.by_status).map(([name, value]) => ({ name: name.replace('_', ' '), value })) :
        [];

    return (
        <div className="space-y-8 max-w-7xl mx-auto">
            <header className="flex flex-col lg:flex-row lg:justify-between lg:items-end gap-4">
                <div>
                    <h1 className="text-4xl font-black tracking-tight text-slate-900 font-heading">National Intelligence Terminal</h1>
                    <div className="flex items-center gap-2 mt-1">
                        <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
                        <p className="text-slate-500 font-medium">Real-time fraud routing across Indian Banking Ecosystem.</p>
                    </div>
                </div>
                <div className="flex flex-wrap gap-3">
                    {/* Bank Filter */}
                    <div className="flex items-center gap-2">
                        <Building2 className="w-4 h-4 text-slate-400" />
                        <select
                            value={selectedBank}
                            onChange={(e) => setSelectedBank(e.target.value ? parseInt(e.target.value) : '')}
                            className="bg-white border border-slate-200 rounded-lg px-3 py-2 text-sm font-medium focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 outline-none"
                        >
                            <option value="">All Banks</option>
                            {banks.map(bank => (
                                <option key={bank.id} value={bank.id}>
                                    {bank.name}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Branch Filter */}
                    <div className="flex items-center gap-2">
                        <MapPin className="w-4 h-4 text-slate-400" />
                        <select
                            value={selectedBranch}
                            onChange={(e) => setSelectedBranch(e.target.value ? parseInt(e.target.value) : '')}
                            className="bg-white border border-slate-200 rounded-lg px-3 py-2 text-sm font-medium focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 outline-none"
                            disabled={!selectedBank}
                        >
                            <option value="">All Branches</option>
                            {branches.map(branch => (
                                <option key={branch.id} value={branch.id}>
                                    {branch.branch_name}
                                </option>
                            ))}
                        </select>
                    </div>

                    <button
                        onClick={handleMockIngest}
                        disabled={ingesting}
                        className="btn btn-primary h-10 px-6"
                    >
                        {ingesting ? <Loader2 className="w-5 h-5 animate-spin" /> : <Download className="w-5 h-5" />}
                        Pull I4C Intelligence
                    </button>
                </div>
            </header>

            {error ? (
                <div className="p-8 bg-rose-50 border border-rose-100 rounded-[32px] flex items-center gap-4 text-rose-700">
                    <div className="w-12 h-12 bg-rose-100 rounded-2xl flex items-center justify-center">
                        <ShieldAlert className="w-6 h-6" />
                    </div>
                    <div>
                        <p className="font-black uppercase tracking-widest text-[10px] mb-1">Error</p>
                        <p className="font-bold">{error}</p>
                    </div>
                </div>
            ) : (
                <>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                        {stats.map((item) => (
                            <div key={item.label} className="card p-8 group relative overflow-hidden">
                                <div className="absolute top-0 right-0 w-32 h-32 bg-[var(--brand-primary)] opacity-5 rounded-full -mr-16 -mt-16 group-hover:opacity-10 transition-all"></div>
                                <div className="flex justify-between items-start mb-6 relative z-10">
                                    <div className="w-12 h-12 bg-slate-50 rounded-2xl flex items-center justify-center group-hover:bg-[var(--brand-primary)] transition-all duration-500">
                                        <item.icon className="w-6 h-6 text-slate-400 group-hover:text-white transition-colors" />
                                    </div>
                                    <span className={`flex items-center text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-widest ${item.trend === 'up' ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'
                                        }`}>
                                        {item.change}
                                    </span>
                                </div>
                                <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] relative z-10">{item.label}</p>
                                <p className="text-3xl font-black text-slate-900 mt-2 tracking-tighter relative z-10">
                                    {loading ? '...' : item.value}
                                </p>
                            </div>
                        ))}
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        <div className="lg:col-span-2 card p-10">
                            <div className="flex items-center justify-between mb-10">
                                <div>
                                    <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.3em] mb-2">Case Status Distribution</h3>
                                    <p className="text-2xl font-black text-slate-900 tracking-tight">Cases by Status</p>
                                </div>
                            </div>
                            <div className="h-[300px]">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={statusData}>
                                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                        <XAxis dataKey="name" stroke="#94a3b8" fontSize={10} fontWeight="bold" tickLine={false} axisLine={false} />
                                        <YAxis stroke="#94a3b8" fontSize={10} fontWeight="bold" tickLine={false} axisLine={false} />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                                        />
                                        <Bar dataKey="value" fill={brand.primaryColor} radius={[4, 4, 0, 0]} />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>

                        <div className="card p-8">
                            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-8">Financial Summary</h3>
                            <div className="space-y-6">
                                <div>
                                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Total Amount</p>
                                    <p className="text-2xl font-black text-slate-900">
                                        ₹{metrics?.financial?.total_amount?.toLocaleString() || 0}
                                    </p>
                                </div>
                                <div>
                                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Held Amount</p>
                                    <p className="text-2xl font-black text-emerald-600">
                                        ₹{metrics?.financial?.total_held_amount?.toLocaleString() || 0}
                                    </p>
                                </div>
                                <div>
                                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Hold Success Rate</p>
                                    <p className="text-2xl font-black text-sky-600">
                                        {metrics?.financial?.hold_success_rate?.toFixed(1) || 0}%
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Export Panel - Admin Only */}
                        <ExportPanel />
                    </div>
                </>
            )}
        </div>
    );
};

export default Dashboard;
