import React, { useEffect, useState } from 'react';
import { adminApi } from '../api';
import { ShieldAlert, RefreshCcw, Search, ExternalLink, Loader2, ArrowRight } from 'lucide-react';
import { cn } from '../utils/cn';

const MisrouteAnalytics: React.FC = () => {
    const [misroutes, setMisroutes] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await adminApi.getMisrouteAnalytics();
                setMisroutes(res.data);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    return (
        <div className="space-y-8 max-w-7xl mx-auto">
            <header className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-slate-900 font-heading">Misroute Intelligence</h1>
                    <p className="text-slate-500 mt-1">Analyzing cases rejected by banks to refine identification algorithms.</p>
                </div>
                <div className="flex gap-3">
                    <button className="btn btn-secondary flex items-center gap-2 text-sm font-bold">
                        <RefreshCcw className="w-4 h-4" /> Recalibrate Engines
                    </button>
                </div>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="card p-6 bg-slate-900 text-white">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Routing Error Rate</p>
                    <p className="text-3xl font-black mt-2">1.8%</p>
                    <div className="mt-4 flex items-center gap-2 text-emerald-400 text-xs font-bold">
                        <RefreshCcw className="w-3 h-3" /> Improved 0.4% from last week
                    </div>
                </div>
                <div className="card p-6 border-l-4 border-l-rose-500">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Total Disputed Cases</p>
                    <p className="text-2xl font-black text-slate-900 mt-1">{misroutes.length}</p>
                </div>
                <div className="card p-6 border-l-4 border-l-sky-500">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Re-routed Successfully</p>
                    <p className="text-2xl font-black text-slate-900 mt-1">42</p>
                </div>
            </div>

            <div className="card">
                <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
                    <h3 className="text-sm font-bold text-slate-900 uppercase tracking-tight flex items-center gap-2">
                        <ShieldAlert className="w-4 h-4 text-rose-500" /> Disputed Routing Ledger
                    </h3>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="border-b border-slate-100 bg-slate-50/30">
                                <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Case ID</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Original Target</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Bank Remarks</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">System Signal</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {loading ? (
                                <tr>
                                    <td colSpan={5} className="px-6 py-20 text-center">
                                        <Loader2 className="w-8 h-8 animate-spin text-sky-600 mx-auto" />
                                    </td>
                                </tr>
                            ) : misroutes.length === 0 ? (
                                <tr>
                                    <td colSpan={5} className="px-6 py-20 text-center">
                                        <p className="text-sm font-bold text-slate-400">No active routing disputes found.</p>
                                    </td>
                                </tr>
                            ) : misroutes.map((m) => (
                                <tr key={m.id} className="hover:bg-rose-50/30 transition-colors">
                                    <td className="px-6 py-4 text-sm font-bold text-sky-700">CASE-{m.complaint_id}</td>
                                    <td className="px-6 py-4">
                                        <span className="text-xs font-bold text-slate-600 bg-slate-100 px-2 py-1 rounded">BANK_ID: {m.bank_id}</span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <p className="text-xs text-slate-600 max-w-xs truncate italic">"{m.remarks}"</p>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className="text-[10px] font-bold text-amber-600 border border-amber-200 bg-amber-50 px-2 py-1 rounded-full">IFSC_MAPPING_AMBIGUOUS</span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <button className="flex items-center gap-1 text-[10px] font-black text-sky-600 uppercase hover:underline">
                                            Re-analyze <ArrowRight className="w-3 h-3" />
                                        </button>
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

export default MisrouteAnalytics;
