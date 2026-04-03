import { useState } from 'react';
import { Download, FileSpreadsheet, FileText, Calendar, Filter } from 'lucide-react';
import { operationsApi } from '../api';

export function ExportPanel() {
  const [exporting, setExporting] = useState(false);
  const [format, setFormat] = useState<'csv' | 'excel' | 'pdf'>('excel');
  const [dateRange, setDateRange] = useState({ start: '', end: '' });
  const [status, setStatus] = useState('');

  const handleExport = async () => {
    setExporting(true);
    try {
      const response = await operationsApi.exportCases({
        format,
        start_date: dateRange.start,
        end_date: dateRange.end,
        status: status || undefined
      });
      
      // Create download link
      const blob = new Blob([response.data], { 
        type: format === 'csv' ? 'text/csv' : format === 'excel' ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' : 'application/pdf'
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `fraud-cases-export-${new Date().toISOString().split('T')[0]}.${format === 'excel' ? 'xlsx' : format}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('Export failed');
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="card p-6">
      <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
        <Download className="w-5 h-5 text-sky-500" />
        Export Cases
      </h3>
      
      <div className="space-y-4">
        <div>
          <label className="text-xs font-bold text-slate-500 uppercase">Format</label>
          <div className="flex gap-2 mt-2">
            {[
              { id: 'excel', icon: FileSpreadsheet, label: 'Excel' },
              { id: 'csv', icon: FileText, label: 'CSV' },
              { id: 'pdf', icon: FileText, label: 'PDF' }
            ].map((f) => (
              <button
                key={f.id}
                onClick={() => setFormat(f.id as any)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg border ${
                  format === f.id 
                    ? 'bg-sky-50 border-sky-500 text-sky-700' 
                    : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                <f.icon className="w-4 h-4" />
                {f.label}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-bold text-slate-500 uppercase flex items-center gap-1">
              <Calendar className="w-3 h-3" /> Start Date
            </label>
            <input
              type="date"
              className="input w-full mt-1"
              value={dateRange.start}
              onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
            />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-500 uppercase flex items-center gap-1">
              <Calendar className="w-3 h-3" /> End Date
            </label>
            <input
              type="date"
              className="input w-full mt-1"
              value={dateRange.end}
              onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
            />
          </div>
        </div>

        <div>
          <label className="text-xs font-bold text-slate-500 uppercase flex items-center gap-1">
            <Filter className="w-3 h-3" /> Status Filter
          </label>
          <select
            className="input w-full mt-1"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            <option value="">All Status</option>
            <option value="NEW">New</option>
            <option value="ACKNOWLEDGED">Acknowledged</option>
            <option value="HOLD_INITIATED">Hold Initiated</option>
            <option value="CLOSED">Closed</option>
          </select>
        </div>

        <button
          onClick={handleExport}
          disabled={exporting}
          className="w-full btn btn-primary flex items-center justify-center gap-2"
        >
          {exporting ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Exporting...
            </>
          ) : (
            <>
              <Download className="w-4 h-4" />
              Export {format.toUpperCase()}
            </>
          )}
        </button>
      </div>
    </div>
  );
}
