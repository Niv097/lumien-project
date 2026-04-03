import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, RefreshCw, AlertCircle, Shield, Send, CheckCircle, Clock } from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../api';

type LEAStatus = 'REGISTERED' | 'ACKNOWLEDGED' | 'RESPONSE_SENT';

interface LEARequest {
  id: number;
  request_id: string;
  case_id: string;
  io_name: string | null;
  police_station: string | null;
  request_received_at: string | null;
  status: LEAStatus;
  acknowledgement_proof: string | null;
  response_dispatch_proof: string | null;
  dispatched_at: string | null;
  remarks: string | null;
}

export default function LEARequestDetail() {
  const { requestId } = useParams<{ requestId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<LEARequest | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get(`/operations/lea-requests/${requestId}`);
        setData(res.data);
      } catch (e) {
        setData(null);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [requestId]);

  const getStatusBadge = (status: LEAStatus) => {
    switch (status) {
      case 'REGISTERED':
        return (
          <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs flex items-center gap-1">
            <Clock size={12} /> Registered
          </span>
        );
      case 'ACKNOWLEDGED':
        return (
          <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs flex items-center gap-1">
            <CheckCircle size={12} /> Acknowledged
          </span>
        );
      case 'RESPONSE_SENT':
        return (
          <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs flex items-center gap-1">
            <Send size={12} /> Response Sent
          </span>
        );
      default:
        return <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">{status}</span>;
    }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate('/lea-requests')} className="p-2 hover:bg-slate-100 rounded-lg transition-colors">
          <ArrowLeft className="w-5 h-5 text-slate-600" />
        </button>
        <div>
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-sky-600" />
            <h1 className="text-2xl font-bold text-gray-900">LEA Request</h1>
            {data?.status && getStatusBadge(data.status)}
          </div>
          <p className="text-sm text-gray-500 mt-1">{requestId}</p>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16 text-gray-500">
          <RefreshCw className="w-5 h-5 animate-spin mr-2" /> Loading...
        </div>
      ) : !data ? (
        <div className="bg-white p-8 rounded-lg shadow-sm border border-gray-200 text-center">
          <AlertCircle className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <div className="text-gray-700 font-medium">Request not found</div>
        </div>
      ) : (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-xs font-semibold text-gray-500">Request ID</div>
              <div className="text-sm font-medium text-gray-900 mt-1">{data.request_id}</div>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-500">Case ID</div>
              <div className="text-sm font-medium text-gray-900 mt-1">{data.case_id || '-'}</div>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-500">IO Name</div>
              <div className="text-sm font-medium text-gray-900 mt-1">{data.io_name || '-'}</div>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-500">Police Station</div>
              <div className="text-sm font-medium text-gray-900 mt-1">{data.police_station || '-'}</div>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-500">Received At</div>
              <div className="text-sm font-medium text-gray-900 mt-1">{data.request_received_at ? new Date(data.request_received_at).toLocaleString() : '-'}</div>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-500">Dispatched At</div>
              <div className="text-sm font-medium text-gray-900 mt-1">{data.dispatched_at ? new Date(data.dispatched_at).toLocaleString() : '-'}</div>
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
