import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, RefreshCw, AlertCircle, FileText, CheckCircle, Play, XCircle, RotateCcw } from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../api';

type RestorationStatus = 'REGISTERED' | 'VERIFIED' | 'APPROVED' | 'EXECUTED' | 'CLOSED';

interface RestorationOrder {
  id: number;
  order_id: string;
  case_id: string;
  order_reference: string | null;
  court_authority: string | null;
  destination_account: string;
  beneficiary_name: string | null;
  amount: number;
  utr_reference: string | null;
  status: RestorationStatus;
  created_at: string;
  executed_at: string | null;
  remarks: string | null;
}

export default function RestorationDetail() {
  const { orderId } = useParams<{ orderId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<RestorationOrder | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get(`/operations/restoration-orders/${orderId}`);
        setData(res.data);
      } catch (e) {
        setData(null);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [orderId]);

  const getStatusBadge = (status: RestorationStatus) => {
    switch (status) {
      case 'REGISTERED':
        return <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs flex items-center gap-1"><RotateCcw size={12}/> Registered</span>;
      case 'VERIFIED':
        return <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs flex items-center gap-1"><CheckCircle size={12}/> Verified</span>;
      case 'APPROVED':
        return <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs flex items-center gap-1"><FileText size={12}/> Approved</span>;
      case 'EXECUTED':
        return <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs flex items-center gap-1"><Play size={12}/> Executed</span>;
      case 'CLOSED':
        return <span className="px-2 py-1 bg-slate-100 text-slate-700 rounded text-xs flex items-center gap-1"><XCircle size={12}/> Closed</span>;
      default:
        return <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">{status}</span>;
    }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate('/restoration')} className="p-2 hover:bg-slate-100 rounded-lg transition-colors">
          <ArrowLeft className="w-5 h-5 text-slate-600" />
        </button>
        <div>
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-sky-600" />
            <h1 className="text-2xl font-bold text-gray-900">Restoration Order</h1>
            {data?.status && getStatusBadge(data.status)}
          </div>
          <p className="text-sm text-gray-500 mt-1">{orderId}</p>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16 text-gray-500">
          <RefreshCw className="w-5 h-5 animate-spin mr-2" /> Loading...
        </div>
      ) : !data ? (
        <div className="bg-white p-8 rounded-lg shadow-sm border border-gray-200 text-center">
          <AlertCircle className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <div className="text-gray-700 font-medium">Order not found</div>
        </div>
      ) : (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-xs font-semibold text-gray-500">Order ID</div>
              <div className="text-sm font-medium text-gray-900 mt-1">{data.order_id}</div>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-500">Case ID</div>
              <div className="text-sm font-medium text-gray-900 mt-1">{data.case_id || '-'}</div>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-500">Order Reference</div>
              <div className="text-sm font-medium text-gray-900 mt-1">{data.order_reference || '-'}</div>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-500">Court / Authority</div>
              <div className="text-sm font-medium text-gray-900 mt-1">{data.court_authority || '-'}</div>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-500">Destination Account</div>
              <div className="text-sm font-medium text-gray-900 mt-1">{data.destination_account || '-'}</div>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-500">Beneficiary</div>
              <div className="text-sm font-medium text-gray-900 mt-1">{data.beneficiary_name || '-'}</div>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-500">Amount</div>
              <div className="text-sm font-medium text-gray-900 mt-1">₹{(data.amount ?? 0).toLocaleString()}</div>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-500">UTR Reference</div>
              <div className="text-sm font-medium text-gray-900 mt-1">{data.utr_reference || '-'}</div>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-500">Created At</div>
              <div className="text-sm font-medium text-gray-900 mt-1">{data.created_at ? new Date(data.created_at).toLocaleString() : '-'}</div>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-500">Executed At</div>
              <div className="text-sm font-medium text-gray-900 mt-1">{data.executed_at ? new Date(data.executed_at).toLocaleString() : '-'}</div>
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
