import React, { useEffect, useMemo, useState } from 'react';
import api from '../api';
import { Loader2, Database, Search, Upload } from 'lucide-react';

type SheetKey =
    | 'readme'
    | 'i4c-inbound-fraud-reports'
    | 'i4c-incidents'
    | 'bank-case-workflow'
    | 'bank-hold-actions'
    | 'bank-statusupdate-requests'
    | 'bank-statusupdate-txn-details'
    | 'i4c-statusupdate-responses'
    | 'workflow-timeline'
    | 'meta-status-codes'
    | 'scenarios';

const SHEETS: Array<{ key: SheetKey; label: string; filterLabel?: string; filterParam?: string }> = [
    { key: 'readme', label: 'README' },
    { key: 'i4c-inbound-fraud-reports', label: 'I4C_Inbound_FraudReports', filterLabel: 'acknowledgement_no', filterParam: 'acknowledgement_no' },
    { key: 'i4c-incidents', label: 'I4C_Incidents', filterLabel: 'acknowledgement_no', filterParam: 'acknowledgement_no' },
    { key: 'bank-case-workflow', label: 'Bank_Case_Workflow', filterLabel: 'case_id', filterParam: 'case_id' },
    { key: 'bank-hold-actions', label: 'Bank_Hold_Actions', filterLabel: 'case_id', filterParam: 'case_id' },
    { key: 'bank-statusupdate-requests', label: 'Bank_StatusUpdate_Request', filterLabel: 'request_id', filterParam: 'request_id' },
    { key: 'bank-statusupdate-txn-details', label: 'Bank_StatusUpdate_TxnDetails', filterLabel: 'request_id', filterParam: 'request_id' },
    { key: 'i4c-statusupdate-responses', label: 'I4C_StatusUpdate_Response', filterLabel: 'request_id', filterParam: 'request_id' },
    { key: 'workflow-timeline', label: 'Workflow_Timeline', filterLabel: 'case_id', filterParam: 'case_id' },
    { key: 'meta-status-codes', label: 'Meta_StatusCodes' },
    { key: 'scenarios', label: 'Demo_Scenarios' },
];

const DemoDataset: React.FC = () => {
    const [sheet, setSheet] = useState<SheetKey>('i4c-inbound-fraud-reports');
    const [filterValue, setFilterValue] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [rows, setRows] = useState<any[]>([]);
    const [total, setTotal] = useState<number>(0);
    const [uploading, setUploading] = useState(false);

    const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        setUploading(true);
        setError(null);
        try {
            const res = await api.post('/demo/upload-dataset', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            alert(res.data.message || 'Dataset uploaded. Ingestion starting in the background.');
            // We can optionally refresh data after a delay if needed
        } catch (err: any) {
            setError(err?.response?.data?.detail || err?.message || 'Failed to upload dataset');
        } finally {
            setUploading(false);
            if (e.target) e.target.value = ''; // reset
        }
    };

    const selectedSheetMeta = useMemo(() => SHEETS.find(s => s.key === sheet), [sheet]);

    const fetchData = async () => {
        setLoading(true);
        setError(null);

        try {
            const params: any = { skip: 0, limit: 200 };
            if (selectedSheetMeta?.filterParam && filterValue.trim()) {
                params[selectedSheetMeta.filterParam] = filterValue.trim();
            }

            const res = await api.get(`/tenant/demo/${sheet}`, { params });
            const items = Array.isArray(res.data?.items) ? res.data.items : [];
            setRows(items);
            setTotal(typeof res.data?.total === 'number' ? res.data.total : items.length);
        } catch (e: any) {
            setError(e?.response?.data?.detail || e?.message || 'Failed to load sheet');
            setRows([]);
            setTotal(0);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [sheet]);

    const columns = useMemo(() => {
        const first = rows[0];
        if (!first) return [] as string[];
        return Object.keys(first);
    }, [rows]);

    return (
        <div className="space-y-8 max-w-7xl mx-auto">
            <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-slate-900 flex items-center justify-center">
                        <Database className="w-5 h-5 text-white" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight text-slate-900 font-heading">Demo Dataset Explorer</h1>
                        <p className="text-slate-500 mt-1">Browse all Excel sheets ingested from the simulated demo dataset.</p>
                    </div>
                </div>
                <div className="flex items-center gap-4">
                    <label className={`btn btn-primary cursor-pointer inline-flex items-center gap-2 ${uploading ? 'opacity-50 pointer-events-none' : ''}`}>
                        {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
                        {uploading ? 'Uploading & Ingesting...' : 'Upload New Dataset'}
                        <input type="file" className="hidden" accept=".xlsx" onChange={handleUpload} disabled={uploading} />
                    </label>
                </div>
            </header>

            <div className="card p-6 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
                    <div className="space-y-1">
                        <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Sheet</label>
                        <select
                            className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-white text-sm font-bold text-slate-700"
                            value={sheet}
                            onChange={(e) => {
                                setFilterValue('');
                                setSheet(e.target.value as SheetKey);
                            }}
                        >
                            {SHEETS.map(s => (
                                <option key={s.key} value={s.key}>{s.label}</option>
                            ))}
                        </select>
                    </div>

                    <div className="space-y-1">
                        <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Filter</label>
                        <input
                            className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-white text-sm font-bold text-slate-700"
                            placeholder={selectedSheetMeta?.filterLabel ? `Filter by ${selectedSheetMeta.filterLabel}` : 'No filter for this sheet'}
                            value={filterValue}
                            disabled={!selectedSheetMeta?.filterParam}
                            onChange={(e) => setFilterValue(e.target.value)}
                        />
                    </div>

                    <button
                        onClick={fetchData}
                        className="btn btn-primary w-full md:w-auto inline-flex items-center justify-center gap-2"
                    >
                        <Search className="w-4 h-4" />
                        Refresh
                    </button>
                </div>

                <div className="text-xs font-medium text-slate-500">
                    Showing {rows.length} rows{typeof total === 'number' ? ` (total: ${total})` : ''}
                </div>
            </div>

            <div className="card">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="border-b border-slate-100 bg-slate-50/30">
                                {columns.map((c) => (
                                    <th key={c} className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">{c}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {loading ? (
                                <tr>
                                    <td colSpan={Math.max(columns.length, 1)} className="px-6 py-20 text-center">
                                        <Loader2 className="w-8 h-8 animate-spin text-sky-600 mx-auto" />
                                    </td>
                                </tr>
                            ) : error ? (
                                <tr>
                                    <td colSpan={Math.max(columns.length, 1)} className="px-6 py-10 text-center text-sm font-bold text-red-600">{error}</td>
                                </tr>
                            ) : rows.length === 0 ? (
                                <tr>
                                    <td colSpan={Math.max(columns.length, 1)} className="px-6 py-10 text-center text-sm font-bold text-slate-500">No rows</td>
                                </tr>
                            ) : (
                                rows.map((r, idx) => (
                                    <tr key={r.id ?? idx} className="hover:bg-slate-50 transition-colors">
                                        {columns.map((c) => (
                                            <td key={c} className="px-6 py-4 text-xs font-medium text-slate-700 whitespace-nowrap">
                                                {r[c] === null || r[c] === undefined ? '' : String(r[c])}
                                            </td>
                                        ))}
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default DemoDataset;
