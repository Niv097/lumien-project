import React, { useEffect, useState } from 'react';
import { adminApi } from '../api';
import { Clock, AlertCircle, CheckCircle2, Loader2, ShieldAlert } from 'lucide-react';
import { cn } from '../utils/cn';

const SLAMonitor: React.FC = () => {
    const [data, setData] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await adminApi.getSLAMonitor();
                setData(res.data);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const getStatus = (item: any) => {
        if (item.completion_time) return 'completed';
        const now = new Date();
        const deadline = new Date(item.deadline);
        if (now > deadline) return 'breached';
        const diff = deadline.getTime() - now.getTime();
        if (diff < 4 * 60 * 60 * 1000) return 'critical'; // < 4 hours
        return 'on-track';
    };

    return (
        <div className="space-y-8 max-w-7xl mx-auto">
            <header>
                <h1 className="text-3xl font-bold tracking-tight text-slate-900 font-heading">SLA Command Center</h1>
                <p className="text-slate-500 mt-1">Strategic oversight of bank response times and regulatory compliance.</p>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="card p-6 border-l-4 border-l-emerald-500">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Average Response Time</p>
                    <p className="text-2xl font-black text-slate-900 mt-1">4.2 Hours</p>
                </div>
                <div className="card p-6 border-l-4 border-l-amber-500">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Active Escalations</p>
                    <p className="text-2xl font-black text-slate-900 mt-1">{data.filter(i => getStatus(i) === 'critical').length}</p>
                </div>
                <div className="card p-6 border-l-4 border-l-rose-500">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Total Breaches (24h)</p>
                    <p className="text-2xl font-black text-slate-900 mt-1">{data.filter(i => i.is_breached || getStatus(i) === 'breached').length}</p>
                </div>
            </div>

            <div className="card">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="border-b border-slate-100 bg-slate-50/30">
                                <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Complaint ID</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Routing Time</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Deadline</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Status</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Time Remaining</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {loading ? (
                                <tr>
                                    <td colSpan={5} className="px-6 py-20 text-center">
                                        <Loader2 className="w-8 h-8 animate-spin text-sky-600 mx-auto" />
                                    </td>
                                </tr>
                            ) : data.length === 0 ? (
                                <tr>
                                    <td colSpan={5} className="px-6 py-20 text-center">
                                        <p className="text-sm font-bold text-slate-400">No active tracking records.</p>
                                    </td>
                                </tr>
                            ) : data.map((item) => {
                                const status = getStatus(item);
                                const deadline = new Date(item.deadline);
                                const now = new Date();
                                const diffHours = status === 'completed' || status === 'breached' ? 0 : Math.max(0, (deadline.getTime() - now.getTime()) / (1000 * 60 * 60));

                                return (
                                    <tr key={item.id} className="hover:bg-slate-50 transition-colors">
                                        <td className="px-6 py-4 text-sm font-bold text-sky-700">CASE-{item.complaint_id}</td>
                                        <td className="px-6 py-4 text-xs font-medium text-slate-600">
                                            {new Date(item.start_time).toLocaleString()}
                                        </td>
                                        <td className="px-6 py-4 text-xs font-bold text-slate-900">
                                            {new Date(item.deadline).toLocaleString()}
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={cn(
                                                "inline-flex items-center px-2 py-1 rounded text-[10px] font-black uppercase tracking-widest",
                                                status === 'completed' && "bg-emerald-50 text-emerald-700",
                                                status === 'on-track' && "bg-sky-50 text-sky-700",
                                                status === 'critical' && "bg-amber-50 text-amber-700",
                                                status === 'breached' && "bg-rose-50 text-rose-700"
                                            )}>
                                                {status.replace('-', ' ')}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-sm font-black text-slate-900 font-mono italic">
                                            {status === 'completed' ? '--' : status === 'breached' ? 'EXPIRED' : `${diffHours.toFixed(1)}h`}
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default SLAMonitor;
