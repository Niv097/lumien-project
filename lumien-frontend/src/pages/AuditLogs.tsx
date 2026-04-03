import React, { useEffect, useState } from 'react';
import { adminApi } from '../api';
import { Table, Loader2, FileSearch } from 'lucide-react';

const AuditLogs: React.FC = () => {
    const [logs, setLogs] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchLogs = async () => {
            try {
                const res = await adminApi.getAuditLogs();
                setLogs(res.data);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchLogs();
    }, []);

    return (
        <div className="space-y-8 max-w-7xl mx-auto">
            <header>
                <h1 className="text-3xl font-bold tracking-tight text-slate-900 font-heading">Immutable Audit Ledger</h1>
                <p className="text-slate-500 mt-1">Strategic record of every state transition and routing lifecycle event.</p>
            </header>

            <div className="card">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="border-b border-slate-100 bg-slate-50/30">
                                <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Timestamp</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Action</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Resource ID</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Transition Path</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {loading ? (
                                <tr>
                                    <td colSpan={4} className="px-6 py-20 text-center">
                                        <Loader2 className="w-8 h-8 animate-spin text-sky-600 mx-auto" />
                                    </td>
                                </tr>
                            ) : logs.map((log) => (
                                <tr key={log.id} className="hover:bg-slate-50 transition-colors">
                                    <td className="px-6 py-4 text-xs font-mono font-bold text-slate-500">
                                        {new Date(log.timestamp).toLocaleString()}
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className="text-xs font-black bg-slate-100 px-2 py-1 rounded uppercase tracking-tighter">
                                            {log.action}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-sm font-bold text-sky-700">
                                        CASE-{log.resource_id}
                                    </td>
                                    <td className="px-6 py-4 text-xs font-medium text-slate-600">
                                        <span className="text-slate-400">{log.old_value || 'None'}</span>
                                        <span className="mx-2 text-sky-400">→</span>
                                        <span className="text-sky-700 font-bold">{log.new_value}</span>
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

export default AuditLogs;
