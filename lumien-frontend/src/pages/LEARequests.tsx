import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Plus, Eye, Send, CheckCircle, Clock, Filter, Search, Building2, User } from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../api';

interface LEAResponse {
  id: number;
  request_id: string;
  case_id: string;
  io_name: string | null;
  police_station: string | null;
  request_received_at: string | null;
  status: 'REGISTERED' | 'ACKNOWLEDGED' | 'RESPONSE_SENT';
  dispatched_at: string | null;
  acknowledgement_proof: string | null;
  created_at: string;
}

export default function LEARequests() {
  const [requests, setRequests] = useState<LEAResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('');
  const [searchCaseId, setSearchCaseId] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    loadRequests();
  }, [filterStatus, searchCaseId]);

  const loadRequests = async () => {
    try {
      const params: any = {};
      if (filterStatus) params.status = filterStatus;
      if (searchCaseId) params.case_id = searchCaseId;
      
      const res = await api.get('/operations/lea-requests', { params });
      setRequests(res.data.items || []);
    } catch (err) {
      console.error('Failed to load LEA requests:', err);
    } finally {
      setLoading(false);
    }
  };

  const createRequest = async () => {
    const caseId = prompt('Enter Case ID:');
    if (!caseId) return;
    
    const ioName = prompt('Enter IO Name:');
    const policeStation = prompt('Enter Police Station:');
    
    try {
      await api.post('/operations/lea-requests', {
        case_id: caseId,
        io_name: ioName,
        police_station: policeStation,
        request_attachment: ''
      });
      loadRequests();
    } catch (err) {
      alert('Failed to register LEA request');
    }
  };

  const acknowledgeRequest = async (requestId: string) => {
    if (!confirm('Acknowledge this LEA request?')) return;
    
    try {
      await api.post(`/operations/lea-requests/${requestId}/acknowledge`, {
        acknowledgement_proof: `ACK-${Date.now()}`
      });
      loadRequests();
    } catch (err) {
      alert('Failed to acknowledge');
    }
  };

  const dispatchResponse = async (requestId: string) => {
    if (!confirm('Dispatch response for this LEA request?')) return;
    
    try {
      await api.post(`/operations/lea-requests/${requestId}/dispatch`, {
        response_pack: {},
        dispatch_proof: `DSP-${Date.now()}`
      });
      loadRequests();
    } catch (err) {
      alert('Failed to dispatch');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'REGISTERED':
        return <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs flex items-center gap-1"><Clock size={12}/> Registered</span>;
      case 'ACKNOWLEDGED':
        return <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs flex items-center gap-1"><CheckCircle size={12}/> Acknowledged</span>;
      case 'RESPONSE_SENT':
        return <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs flex items-center gap-1"><Send size={12}/> Response Sent</span>;
      default:
        return <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">{status}</span>;
    }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">LEA Requests</h1>
          <p className="text-sm text-gray-500 mt-1">Manage Law Enforcement Agency requests and responses</p>
        </div>
        <button
          onClick={createRequest}
          className="flex items-center gap-2 px-4 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-colors"
        >
          <Plus size={18} />
          Register LEA Request
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 mb-4">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 flex-1">
            <Search size={18} className="text-gray-400" />
            <input
              type="text"
              placeholder="Search by Case ID..."
              value={searchCaseId}
              onChange={(e) => setSearchCaseId(e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter size={18} className="text-gray-400" />
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
            >
              <option value="">All Status</option>
              <option value="REGISTERED">Registered</option>
              <option value="ACKNOWLEDGED">Acknowledged</option>
              <option value="RESPONSE_SENT">Response Sent</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Request ID</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Case ID</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">IO/Police Station</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Received</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Status</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {loading ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">Loading...</td></tr>
            ) : requests.length === 0 ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">No LEA requests found</td></tr>
            ) : (
              requests.map((req) => (
                <tr key={req.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{req.request_id}</td>
                  <td className="px-4 py-3 text-gray-600">{req.case_id}</td>
                  <td className="px-4 py-3">
                    <div className="text-sm">
                      <div className="flex items-center gap-1 text-gray-700">
                        <User size={12} />
                        {req.io_name || 'N/A'}
                      </div>
                      <div className="flex items-center gap-1 text-gray-500 text-xs mt-0.5">
                        <Building2 size={12} />
                        {req.police_station || 'N/A'}
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-600 text-sm">
                    {req.request_received_at ? new Date(req.request_received_at).toLocaleDateString() : '-'}
                  </td>
                  <td className="px-4 py-3">{getStatusBadge(req.status)}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <button 
                        onClick={() => navigate(`/lea-requests/${req.request_id}`)}
                        className="p-1.5 text-gray-600 hover:text-sky-600 hover:bg-sky-50 rounded"
                        title="View Details"
                      >
                        <Eye size={16} />
                      </button>
                      {req.status === 'REGISTERED' && (
                        <button 
                          onClick={() => acknowledgeRequest(req.request_id)}
                          className="p-1.5 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded"
                          title="Acknowledge"
                        >
                          <CheckCircle size={16} />
                        </button>
                      )}
                      {req.status === 'ACKNOWLEDGED' && (
                        <button 
                          onClick={() => dispatchResponse(req.request_id)}
                          className="p-1.5 text-gray-600 hover:text-green-600 hover:bg-green-50 rounded"
                          title="Dispatch Response"
                        >
                          <Send size={16} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-3 gap-4 mt-6">
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center gap-2 mb-2">
            <Shield className="text-sky-600" size={20} />
            <span className="font-semibold text-gray-700">Registered</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{requests.filter(r => r.status === 'REGISTERED').length}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="text-blue-600" size={20} />
            <span className="font-semibold text-gray-700">Acknowledged</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{requests.filter(r => r.status === 'ACKNOWLEDGED').length}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center gap-2 mb-2">
            <Send className="text-green-600" size={20} />
            <span className="font-semibold text-gray-700">Response Sent</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{requests.filter(r => r.status === 'RESPONSE_SENT').length}</p>
        </div>
      </div>
    </motion.div>
  );
}
