import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Plus, Eye, Send, Copy, Filter, Search, Clock, Lock, CheckCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../api';

interface KYCPack {
  id: number;
  pack_id: string;
  case_id: string;
  version: number;
  status: 'DRAFT' | 'SUBMITTED' | 'LOCKED';
  acknowledgement_ref: string | null;
  submitted_at: string | null;
  locked_at: string | null;
  created_at: string;
  remarks: string | null;
}

export default function KYCPacks() {
  const [packs, setPacks] = useState<KYCPack[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('');
  const [searchCaseId, setSearchCaseId] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    loadPacks();
  }, [filterStatus, searchCaseId]);

  const loadPacks = async () => {
    try {
      const params: any = {};
      if (filterStatus) params.status = filterStatus;
      if (searchCaseId) params.case_id = searchCaseId;
      
      const res = await api.get('/operations/kyc-packs', { params });
      setPacks(res.data.items || []);
    } catch (err) {
      console.error('Failed to load KYC packs:', err);
    } finally {
      setLoading(false);
    }
  };

  const createPack = async () => {
    const caseId = prompt('Enter Case ID:');
    if (!caseId) return;
    
    try {
      await api.post('/operations/kyc-packs', {
        case_id: caseId,
        mandatory_fields: {},
        attachments: [],
        remarks: ''
      });
      loadPacks();
    } catch (err) {
      alert('Failed to create KYC pack');
    }
  };

  const submitPack = async (packId: string) => {
    if (!confirm('Submit this KYC pack? It will be locked after submission.')) return;
    
    try {
      await api.post(`/operations/kyc-packs/${packId}/submit`);
      loadPacks();
    } catch (err) {
      alert('Failed to submit KYC pack');
    }
  };

  const createVersion = async (packId: string) => {
    if (!confirm('Create new version of this pack?')) return;
    
    try {
      await api.post(`/operations/kyc-packs/${packId}/version`);
      loadPacks();
    } catch (err) {
      alert('Failed to create version');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'DRAFT':
        return <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">Draft</span>;
      case 'SUBMITTED':
        return <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs flex items-center gap-1"><CheckCircle size={12}/> Submitted</span>;
      case 'LOCKED':
        return <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs flex items-center gap-1"><Lock size={12}/> Locked</span>;
      default:
        return <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">{status}</span>;
    }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">KYC & Submissions</h1>
          <p className="text-sm text-gray-500 mt-1">Generate and submit KYC packs to authorities</p>
        </div>
        <button
          onClick={createPack}
          className="flex items-center gap-2 px-4 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-colors"
        >
          <Plus size={18} />
          New KYC Pack
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
              <option value="DRAFT">Draft</option>
              <option value="SUBMITTED">Submitted</option>
              <option value="LOCKED">Locked</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Pack ID</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Case ID</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Version</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Status</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Ack Ref</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Submitted</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {loading ? (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500">Loading...</td></tr>
            ) : packs.length === 0 ? (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500">No KYC packs found</td></tr>
            ) : (
              packs.map((pack) => (
                <tr key={pack.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{pack.pack_id}</td>
                  <td className="px-4 py-3 text-gray-600">{pack.case_id}</td>
                  <td className="px-4 py-3 text-gray-600">v{pack.version}</td>
                  <td className="px-4 py-3">{getStatusBadge(pack.status)}</td>
                  <td className="px-4 py-3 text-gray-600 text-sm">{pack.acknowledgement_ref || '-'}</td>
                  <td className="px-4 py-3 text-gray-600 text-sm">
                    {pack.submitted_at ? new Date(pack.submitted_at).toLocaleDateString() : '-'}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <button 
                        onClick={() => navigate(`/kyc-packs/${pack.pack_id}`)}
                        className="p-1.5 text-gray-600 hover:text-sky-600 hover:bg-sky-50 rounded"
                        title="View Details"
                      >
                        <Eye size={16} />
                      </button>
                      {pack.status === 'DRAFT' && (
                        <button 
                          onClick={() => submitPack(pack.pack_id)}
                          className="p-1.5 text-gray-600 hover:text-green-600 hover:bg-green-50 rounded"
                          title="Submit Pack"
                        >
                          <Send size={16} />
                        </button>
                      )}
                      {(pack.status === 'SUBMITTED' || pack.status === 'LOCKED') && (
                        <button 
                          onClick={() => createVersion(pack.pack_id)}
                          className="p-1.5 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded"
                          title="Create New Version"
                        >
                          <Copy size={16} />
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
            <FileText className="text-sky-600" size={20} />
            <span className="font-semibold text-gray-700">Draft Packs</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{packs.filter(p => p.status === 'DRAFT').length}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="text-green-600" size={20} />
            <span className="font-semibold text-gray-700">Submitted</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{packs.filter(p => p.status === 'SUBMITTED').length}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="text-amber-600" size={20} />
            <span className="font-semibold text-gray-700">Pending Submit</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{packs.filter(p => p.status === 'DRAFT').length}</p>
        </div>
      </div>
    </motion.div>
  );
}
