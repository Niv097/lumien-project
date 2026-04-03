import React, { useEffect, useState } from 'react';
import { caseApi } from '../api';
import { Coins, CheckCircle2, History, Loader2, Search, ArrowRight, ShieldCheck } from 'lucide-react';
import { cn } from '../utils/cn';
import { Link } from 'react-router-dom';

const Reconciliation: React.FC = () => {
    const [items, setItems] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState<string | null>(null);

    const fetchData = async () => {
        try {
            const res = await caseApi.getReconciliation();
            setItems(Array.isArray(res.data) ? res.data : (res.data?.items || []));
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleReconcile = async (id: string) => {
        setActionLoading(id);
        try {
            await caseApi.reconcileCase(id);
            await fetchData();
        } catch (err: any) {
            alert(err.response?.data?.detail || "Reconciliation failed");
        } finally {
            setActionLoading(null);
        }
    };

    return (
        <div className="space-y-8 max-w-7xl mx-auto pb-20">
            <header className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-slate-900 font-heading">Financial Reconciliation</h1>
                    <p className="text-slate-500 mt-1">Settle account holds and verify final fund availability for victim restoration.</p>
                </div>
                <div className="flex gap-4 items-center bg-emerald-50 px-4 py-2 rounded-2xl border border-emerald-100">
                    <div className="w-10 h-10 bg-emerald-500 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/20">
                        <Coins className="w-6 h-6 text-white" />
                    </div>
                    <div>
                        <p className="text-[10px] font-black text-emerald-600 uppercase tracking-widest leading-none">Total Discrepancies</p>
                        <p className="text-lg font-black text-slate-900 leading-none mt-1">
                            ₹{items.reduce((acc, i) => acc + (parseFloat(i.platform_value) || 0), 0).toLocaleString()}
                        </p>
                    </div>
                </div>
            </header>

            <div className="grid grid-cols-1 gap-6">
                <div className="card">
                    <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
                        <h3 className="text-sm font-bold text-slate-900 uppercase tracking-tight flex items-center gap-2">
                            <ShieldCheck className="w-4 h-4 text-emerald-500" /> Pending Settlement Queue
                        </h3>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="border-b border-slate-100 bg-slate-50/30">
                                    <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Item ID</th>
                                    <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Mismatch Type</th>
                                    <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Platform Value</th>
                                    <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">CBS Value</th>
                                    <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Status</th>
                                    <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest text-right">Action</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                                {loading ? (
                                    <tr>
                                        <td colSpan={6} className="px-6 py-20 text-center">
                                            <Loader2 className="w-8 h-8 animate-spin text-sky-600 mx-auto" />
                                        </td>
                                    </tr>
                                ) : items.length === 0 ? (
                                    <tr>
                                        <td colSpan={6} className="px-6 py-20 text-center">
                                            <p className="text-sm font-bold text-slate-400 italic">"Zero reconciliation items—CBS is perfectly synchronized."</p>
                                        </td>
                                    </tr>
                                ) : items.map((i) => (
                                    <tr key={i.id} className="hover:bg-slate-50/50 transition-colors group">
                                        <td className="px-6 py-4">
                                            <span className="text-sm font-bold text-sky-700">{i.item_id}</span>
                                            <p className="text-xs text-slate-400">Case: {i.case_id}</p>
                                        </td>
                                        <td className="px-6 py-4 text-sm font-bold text-slate-900">{i.mismatch_type}</td>
                                        <td className="px-6 py-4 text-sm font-black text-slate-900 font-mono italic">₹{parseFloat(i.platform_value || 0).toLocaleString()}</td>
                                        <td className="px-6 py-4 text-sm font-black text-slate-900 font-mono italic">₹{parseFloat(i.cbs_value || 0).toLocaleString()}</td>
                                        <td className="px-6 py-4">
                                            <span className="px-2 py-1 rounded-full text-[10px] font-black uppercase tracking-widest bg-emerald-50 text-emerald-700 border border-emerald-100">
                                                {(i.status || 'PENDING').replace('_', ' ')}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <button
                                                onClick={() => handleReconcile(i.item_id)}
                                                disabled={!!actionLoading || i.status === 'CLOSED' || i.status === 'RESOLVED'}
                                                className="btn btn-primary py-2 px-4 text-[10px] font-black uppercase tracking-widest bg-emerald-600 hover:bg-emerald-500 shadow-emerald-500/20 disabled:opacity-50"
                                            >
                                                {actionLoading === i.item_id ? <Loader2 className="w-3 h-3 animate-spin" /> : (i.status === 'CLOSED' || i.status === 'RESOLVED' ? 'Resolved' : 'Resolve')}
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Reconciliation;
