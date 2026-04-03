import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, RefreshCw, AlertCircle, MessageSquare, AlertTriangle, ArrowUp, CheckCircle, XCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../api';

type GrievanceStatus = 'OPEN' | 'ESCALATED' | 'RESOLVED' | 'CLOSED';

type GrievanceType = 'HOLD_REMOVAL' | 'DELAY' | 'OTHER';

interface Grievance {
  id: number;
  grievance_id: string;
  case_id: string;
  grievance_type: GrievanceType;
  escalation_stage: number;
  status: GrievanceStatus;
  info_furnished_note: string | null;
  outcome_code: string | null;
  release_direction_doc: string | null;
  opened_at: string;
  resolved_at: string | null;
  remarks: string | null;
}

export default function GrievanceDetail() {
  const { grievanceId } = useParams<{ grievanceId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<Grievance | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get(`/operations/grievances/${grievanceId}`);
        setData(res.data);
      } catch (e) {
        setData(null);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [grievanceId]);

  const getStatusBadge = (status: GrievanceStatus) => {
    switch (status) {
      case 'OPEN':
        return (
          <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-xs flex items-center gap-1">
            <AlertTriangle size={12} /> Open
          </span>
        );
      case 'ESCALATED':
        return (
          <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded text-xs flex items-center gap-1">
            <ArrowUp size={12} /> Escalated
          </span>
        );
      case 'RESOLVED':
        return (
          <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs flex items-center gap-1">
            <CheckCircle size={12} /> Resolved
          </span>
        );
      case 'CLOSED':
        return (
          <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs flex items-center gap-1">
            <XCircle size={12} /> Closed
          </span>
        );
      default:
        return <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">{status}</span>;
    }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate('/grievances')} className="p-2 hover:bg-slate-100 rounded-lg transition-colors">
          <ArrowLeft className="w-5 h-5 text-slate-600" />
        </button>
        <div>
          <div className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-sky-600" />
            <h1 className="text-2xl font-bold text-gray-900">Grievance</h1>
            {data?.status && getStatusBadge(data.status)}
          </div>
          <p className="text-sm text-gray-500 mt-1">{grievanceId}</p>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16 text-gray-500">
          <RefreshCw className="w-5 h-5 animate-spin mr-2" /> Loading...
        </div>
      ) : !data ? (
        <div className="bg-white p-8 rounded-lg shadow-sm border border-gray-200 text-center">
          <AlertCircle className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <div className="text-gray-700 font-medium">Grievance not found</div>
        </div>
      ) : (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-xs font-semibold text-gray-500">Grievance ID</div>
              <div className="text-sm font-medium text-gray-900 mt-1">{data.grievance_id}</div>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-500">Case ID</div>
              <div className="text-sm font-medium text-gray-900 mt-1">{data.case_id || '-'}</div>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-500">Type</div>
              <div className="text-sm font-medium text-gray-900 mt-1">{data.grievance_type}</div>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-500">Escalation Stage</div>
              <div className="text-sm font-medium text-gray-900 mt-1">Stage {data.escalation_stage}</div>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-500">Opened At</div>
              <div className="text-sm font-medium text-gray-900 mt-1">{data.opened_at ? new Date(data.opened_at).toLocaleString() : '-'}</div>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-500">Resolved At</div>
              <div className="text-sm font-medium text-gray-900 mt-1">{data.resolved_at ? new Date(data.resolved_at).toLocaleString() : '-'}</div>
            </div>
            <div className="col-span-2">
              <div className="text-xs font-semibold text-gray-500">Info Furnished Note</div>
              <div className="text-sm text-gray-900 mt-1">{data.info_furnished_note || '-'}</div>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-500">Outcome Code</div>
              <div className="text-sm font-medium text-gray-900 mt-1">{data.outcome_code || '-'}</div>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-500">Release Direction Doc</div>
              <div className="text-sm font-medium text-gray-900 mt-1">{data.release_direction_doc || '-'}</div>
            </div>
            <div className="col-span-2">
              <div className="text-xs font-semibold text-gray-500">Remarks</div>
              <div className="text-sm text-gray-900 mt-1">{data.remarks || '-'}</div>
            </div>
          </div>
        </div>
      )}
    </motion.div>
  );
}
