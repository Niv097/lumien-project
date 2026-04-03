import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { RotateCcw, Plus, Eye, CheckCircle, Play, XCircle, Filter, Search, Building2, FileText } from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../api';

interface RestorationOrder {
  id: number;
  order_id: string;
  case_id: string;
  order_reference: string;
  court_authority: string | null;
  destination_account: string;
  beneficiary_name: string | null;
  amount: number;
  utr_reference: string | null;
  status: 'REGISTERED' | 'VERIFIED' | 'APPROVED' | 'EXECUTED' | 'CLOSED';
  created_at: string;
  executed_at: string | null;
}

export default function MoneyRestoration() {
  const [orders, setOrders] = useState<RestorationOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('');
  const [searchCaseId, setSearchCaseId] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    loadOrders();
  }, [filterStatus, searchCaseId]);

  const loadOrders = async () => {
    try {
      const params: any = {};
      if (filterStatus) params.status = filterStatus;
      if (searchCaseId) params.case_id = searchCaseId;
      
      const res = await api.get('/operations/restoration-orders', { params });
      setOrders(res.data.items || []);
    } catch (err) {
      console.error('Failed to load restoration orders:', err);
    } finally {
      setLoading(false);
    }
  };

  const createOrder = async () => {
    const caseId = prompt('Enter Case ID:');
    if (!caseId) return;
    
    const orderRef = prompt('Enter Court Order Reference:');
    const authority = prompt('Enter Court/Authority:');
    const destAccount = prompt('Enter Destination Account:');
    const amount = prompt('Enter Amount:');
    
    try {
      await api.post('/operations/restoration-orders', {
        case_id: caseId,
        order_reference: orderRef,
        court_authority: authority,
        destination_account: destAccount,
        amount: parseFloat(amount || '0'),
        verification_details: ''
      });
      loadOrders();
    } catch (err) {
      alert('Failed to create restoration order');
    }
  };

  const verifyOrder = async (orderId: string) => {
    if (!confirm('Verify this restoration order?')) return;
    
    try {
      await api.post(`/operations/restoration-orders/${orderId}/verify`);
      loadOrders();
    } catch (err) {
      alert('Failed to verify');
    }
  };

  const approveOrder = async (orderId: string) => {
    if (!confirm('Approve this restoration order?')) return;
    
    try {
      await api.post(`/operations/restoration-orders/${orderId}/approve`);
      loadOrders();
    } catch (err) {
      alert('Failed to approve');
    }
  };

  const executeOrder = async (orderId: string) => {
    const utr = prompt('Enter UTR/Reference Number:');
    if (!utr) return;
    
    try {
      await api.post(`/operations/restoration-orders/${orderId}/execute`, {
        utr_reference: utr,
        execution_proof: ''
      });
      loadOrders();
    } catch (err) {
      alert('Failed to execute');
    }
  };

  const closeOrder = async (orderId: string) => {
    if (!confirm('Close this restoration order?')) return;
    
    try {
      await api.post(`/operations/restoration-orders/${orderId}/close`);
      loadOrders();
    } catch (err) {
      alert('Failed to close');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'REGISTERED':
        return <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">Registered</span>;
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
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Money Restoration</h1>
          <p className="text-sm text-gray-500 mt-1">Handle court orders for fund restoration</p>
        </div>
        <button
          onClick={createOrder}
          className="flex items-center gap-2 px-4 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-colors"
        >
          <Plus size={18} />
          Register Order
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
              <option value="VERIFIED">Verified</option>
              <option value="APPROVED">Approved</option>
              <option value="EXECUTED">Executed</option>
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
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Order ID</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Case ID</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Court/Authority</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Destination</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Amount</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Status</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {loading ? (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500">Loading...</td></tr>
            ) : orders.length === 0 ? (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500">No restoration orders found</td></tr>
            ) : (
              orders.map((order) => (
                <tr key={order.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{order.order_id}</td>
                  <td className="px-4 py-3 text-gray-600">{order.case_id}</td>
                  <td className="px-4 py-3">
                    <div className="text-sm">
                      <div className="text-gray-700">{order.order_reference}</div>
                      <div className="text-gray-500 text-xs flex items-center gap-1">
                        <Building2 size={10} />
                        {order.court_authority || 'N/A'}
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-600 text-sm">
                    <div>{order.destination_account}</div>
                    <div className="text-gray-500 text-xs">{order.beneficiary_name || 'N/A'}</div>
                  </td>
                  <td className="px-4 py-3 font-medium text-gray-900">
                    ₹{order.amount.toLocaleString()}
                  </td>
                  <td className="px-4 py-3">{getStatusBadge(order.status)}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <button 
                        onClick={() => navigate(`/restoration/${order.order_id}`)}
                        className="p-1.5 text-gray-600 hover:text-sky-600 hover:bg-sky-50 rounded"
                        title="View Details"
                      >
                        <Eye size={16} />
                      </button>
                      {order.status === 'REGISTERED' && (
                        <button 
                          onClick={() => verifyOrder(order.order_id)}
                          className="p-1.5 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded"
                          title="Verify"
                        >
                          <CheckCircle size={16} />
                        </button>
                      )}
                      {order.status === 'VERIFIED' && (
                        <button 
                          onClick={() => approveOrder(order.order_id)}
                          className="p-1.5 text-gray-600 hover:text-purple-600 hover:bg-purple-50 rounded"
                          title="Approve"
                        >
                          <FileText size={16} />
                        </button>
                      )}
                      {order.status === 'APPROVED' && (
                        <button 
                          onClick={() => executeOrder(order.order_id)}
                          className="p-1.5 text-gray-600 hover:text-green-600 hover:bg-green-50 rounded"
                          title="Execute"
                        >
                          <Play size={16} />
                        </button>
                      )}
                      {order.status === 'EXECUTED' && (
                        <button 
                          onClick={() => closeOrder(order.order_id)}
                          className="p-1.5 text-gray-600 hover:text-slate-600 hover:bg-slate-50 rounded"
                          title="Close"
                        >
                          <XCircle size={16} />
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
      <div className="grid grid-cols-5 gap-4 mt-6">
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center gap-2 mb-2">
            <RotateCcw className="text-gray-600" size={20} />
            <span className="font-semibold text-gray-700">Registered</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{orders.filter(o => o.status === 'REGISTERED').length}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="text-blue-600" size={20} />
            <span className="font-semibold text-gray-700">Verified</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{orders.filter(o => o.status === 'VERIFIED').length}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center gap-2 mb-2">
            <FileText className="text-purple-600" size={20} />
            <span className="font-semibold text-gray-700">Approved</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{orders.filter(o => o.status === 'APPROVED').length}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center gap-2 mb-2">
            <Play className="text-green-600" size={20} />
            <span className="font-semibold text-gray-700">Executed</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{orders.filter(o => o.status === 'EXECUTED').length}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center gap-2 mb-2">
            <XCircle className="text-slate-600" size={20} />
            <span className="font-semibold text-gray-700">Closed</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{orders.filter(o => o.status === 'CLOSED').length}</p>
        </div>
      </div>
    </motion.div>
  );
}
