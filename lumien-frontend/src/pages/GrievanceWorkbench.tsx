import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MessageSquare, Plus, Eye, ArrowUp, CheckCircle, XCircle, Filter, Search, AlertTriangle, User } from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../api';

interface Grievance {
  id: number;
  grievance_id: string;
  case_id: string;
  grievance_type: 'HOLD_REMOVAL' | 'DELAY' | 'OTHER';
  escalation_stage: number;
  status: 'OPEN' | 'ESCALATED' | 'RESOLVED' | 'CLOSED';
  info_furnished_note: string | null;
  outcome_code: string | null;
  opened_at: string;
  resolved_at: string | null;
  release_direction_doc: string | null;
}

export default function GrievanceWorkbench() {
  const [grievances, setGrievances] = useState<Grievance[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('');
  const [filterType, setFilterType] = useState('');
  const [searchCaseId, setSearchCaseId] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    loadGrievances();
  }, [filterStatus, filterType, searchCaseId]);

  const loadGrievances = async () => {
    try {
      const params: any = {};
      if (filterStatus) params.status = filterStatus;
      if (filterType) params.grievance_type = filterType;
      if (searchCaseId) params.case_id = searchCaseId;
      
      const res = await api.get('/operations/grievances', { params });
      setGrievances(res.data.items || []);
    } catch (err) {
      console.error('Failed to load grievances:', err);
    } finally {
      setLoading(false);
    }
  };

  const createGrievance = async () => {
    const caseId = prompt('Enter Case ID:');
    if (!caseId) return;
    
    const type = prompt('Grievance Type (HOLD_REMOVAL, DELAY, OTHER):', 'HOLD_REMOVAL');
    if (!type) return;
    
    try {
      await api.post('/operations/grievances', {
        case_id: caseId,
        grievance_type: type,
        info_furnished_note: ''
      });
      loadGrievances();
    } catch (err) {
      alert('Failed to register grievance');
    }
  };

  const escalateGrievance = async (grievanceId: string) => {
    if (!confirm('Escalate this grievance to next stage?')) return;
    
    try {
      await api.post(`/operations/grievances/${grievanceId}/escalate`);
      loadGrievances();
    } catch (err) {
      alert('Failed to escalate');
    }
  };

  const resolveGrievance = async (grievanceId: string) => {
    const outcomeCode = prompt('Enter outcome code:');
    if (!outcomeCode) return;
    
    try {
      await api.post(`/operations/grievances/${grievanceId}/resolve`, {
        outcome_code: outcomeCode,
        release_direction_doc: ''
      });
      loadGrievances();
    } catch (err) {
      alert('Failed to resolve');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'OPEN':
        return <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-xs flex items-center gap-1"><AlertTriangle size={12}/> Open</span>;
      case 'ESCALATED':
        return <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded text-xs flex items-center gap-1"><ArrowUp size={12}/> Escalated</span>;
      case 'RESOLVED':
        return <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs flex items-center gap-1"><CheckCircle size={12}/> Resolved</span>;
      case 'CLOSED':
        return <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs flex items-center gap-1"><XCircle size={12}/> Closed</span>;
      default:
        return <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">{status}</span>;
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'HOLD_REMOVAL': return 'Hold Removal';
      case 'DELAY': return 'Delay';
      case 'OTHER': return 'Other';
      default: return type;
    }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Grievance Workbench</h1>
          <p className="text-sm text-gray-500 mt-1">Handle customer complaints and escalations</p>
        </div>
        <button
          onClick={createGrievance}
          className="flex items-center gap-2 px-4 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-colors"
        >
          <Plus size={18} />
          Register Grievance
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
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
            >
              <option value="">All Types</option>
              <option value="HOLD_REMOVAL">Hold Removal</option>
              <option value="DELAY">Delay</option>
              <option value="OTHER">Other</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
            >
              <option value="">All Status</option>
              <option value="OPEN">Open</option>
              <option value="ESCALATED">Escalated</option>
              <option value="RESOLVED">Resolved</option>
              <option value="CLOSED">Closed</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Grievance ID</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Case ID</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Type</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Stage</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Status</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Opened</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {loading ? (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500">Loading...</td></tr>
            ) : grievances.length === 0 ? (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500">No grievances found</td></tr>
            ) : (
              grievances.map((g) => (
                <tr key={g.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{g.grievance_id}</td>
                  <td className="px-4 py-3 text-gray-600">{g.case_id}</td>
                  <td className="px-4 py-3 text-gray-600 text-sm">{getTypeLabel(g.grievance_type)}</td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs">
                      Stage {g.escalation_stage}
                    </span>
                  </td>
                  <td className="px-4 py-3">{getStatusBadge(g.status)}</td>
                  <td className="px-4 py-3 text-gray-600 text-sm">
                    {new Date(g.opened_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <button 
                        onClick={() => navigate(`/grievances/${g.grievance_id}`)}
                        className="p-1.5 text-gray-600 hover:text-sky-600 hover:bg-sky-50 rounded"
                        title="View Details"
                      >
                        <Eye size={16} />
                      </button>
                      {(g.status === 'OPEN' || g.status === 'ESCALATED') && g.escalation_stage < 5 && (
                        <button 
                          onClick={() => escalateGrievance(g.grievance_id)}
                          className="p-1.5 text-gray-600 hover:text-orange-600 hover:bg-orange-50 rounded"
                          title="Escalate"
                        >
                          <ArrowUp size={16} />
                        </button>
                      )}
                      {(g.status === 'OPEN' || g.status === 'ESCALATED') && (
                        <button 
                          onClick={() => resolveGrievance(g.grievance_id)}
                          className="p-1.5 text-gray-600 hover:text-green-600 hover:bg-green-50 rounded"
                          title="Resolve"
                        >
                          <CheckCircle size={16} />
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
      <div className="grid grid-cols-4 gap-4 mt-6">
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="text-yellow-600" size={20} />
            <span className="font-semibold text-gray-700">Open</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{grievances.filter(g => g.status === 'OPEN').length}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center gap-2 mb-2">
            <ArrowUp className="text-orange-600" size={20} />
            <span className="font-semibold text-gray-700">Escalated</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{grievances.filter(g => g.status === 'ESCALATED').length}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="text-blue-600" size={20} />
            <span className="font-semibold text-gray-700">Resolved</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{grievances.filter(g => g.status === 'RESOLVED').length}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center gap-2 mb-2">
            <MessageSquare className="text-sky-600" size={20} />
            <span className="font-semibold text-gray-700">Total</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{grievances.length}</p>
        </div>
      </div>
    </motion.div>
  );
}
