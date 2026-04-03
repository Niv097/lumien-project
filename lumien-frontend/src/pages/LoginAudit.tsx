import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Clock, 
  Building2, 
  Filter, 
  Download, 
  Calendar,
  Activity,
  LogOut,
  CheckCircle2,
  AlertCircle,
  Search,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { adminApi } from '../api';

interface LoginRecord {
  audit_id: string;
  username: string;
  email: string;
  bank_name: string;
  bank_code: string;
  roles: string[];
  login_time: string;
  logout_time: string | null;
  session_duration_minutes: number | null;
  status: 'active' | 'logged_out' | 'expired';
}

interface BankSummary {
  bank_name: string;
  bank_code: string;
  total_logins: number;
  active_sessions: number;
  unique_users: number;
}

export default function LoginAudit() {
  const [records, setRecords] = useState<LoginRecord[]>([]);
  const [summary, setSummary] = useState<BankSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterBank, setFilterBank] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [dateRange, setDateRange] = useState({ start: '', end: '' });
  const [pagination, setPagination] = useState({ limit: 50, offset: 0, total: 0 });

  useEffect(() => {
    fetchLoginRecords();
    fetchSummary();
  }, [filterBank, filterStatus, dateRange, pagination.offset, pagination.limit]);

  const fetchLoginRecords = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filterBank) params.append('bank_code', filterBank);
      if (filterStatus) params.append('status', filterStatus);
      if (dateRange.start) params.append('start_date', dateRange.start);
      if (dateRange.end) params.append('end_date', dateRange.end);
      params.append('limit', pagination.limit.toString());
      params.append('offset', pagination.offset.toString());

      const response = await api.get(`/auth/login-audit?${params.toString()}`);
      setRecords(response.data.items || []);
      setPagination(prev => ({ ...prev, total: response.data.total }));
    } catch (error) {
      console.error('Failed to fetch login records:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSummary = async () => {
    try {
      const params = new URLSearchParams();
      if (dateRange.start) params.append('start_date', dateRange.start);
      if (dateRange.end) params.append('end_date', dateRange.end);

      const response = await api.get(`/auth/login-audit/summary?${params.toString()}`);
      setSummary(response.data.banks || []);
    } catch (error) {
      console.error('Failed to fetch summary:', error);
    }
  };

  const formatDateTime = (isoString: string | null) => {
    if (!isoString) return '-';
    return new Date(isoString).toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatDuration = (minutes: number | null) => {
    if (!minutes) return '-';
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  const exportToCSV = () => {
    const headers = ['Username', 'Email', 'Bank', 'Bank Code', 'Roles', 'Login Time', 'Logout Time', 'Duration', 'Status'];
    const rows = records.map(r => [
      r.username,
      r.email,
      r.bank_name,
      r.bank_code,
      r.roles.join(', '),
      formatDateTime(r.login_time),
      formatDateTime(r.logout_time),
      formatDuration(r.session_duration_minutes),
      r.status
    ]);
    
    const csv = [headers.join(','), ...rows.map(row => row.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `login-audit-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  const totalPages = Math.ceil(pagination.total / pagination.limit);
  const currentPage = Math.floor(pagination.offset / pagination.limit) + 1;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Login Audit Records</h1>
              <p className="text-sm text-gray-500 mt-1">
                Track all bank user logins, session duration, and activity status
              </p>
            </div>
            <button
              onClick={exportToCSV}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Download className="w-4 h-4" />
              Export CSV
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Bank Summary Cards */}
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Building2 className="w-5 h-5 text-blue-600" />
            Bank-wise Login Summary
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {summary.map((bank) => (
              <div key={bank.bank_code} className="bg-white rounded-xl shadow-sm border p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="font-semibold text-gray-900">{bank.bank_name}</span>
                  <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                    {bank.bank_code}
                  </span>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Total Logins</span>
                    <span className="font-medium">{bank.total_logins}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Active Sessions</span>
                    <span className="font-medium text-green-600">{bank.active_sessions}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Unique Users</span>
                    <span className="font-medium">{bank.unique_users}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl shadow-sm border p-4 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <Filter className="w-5 h-5 text-gray-500" />
            <h3 className="font-semibold text-gray-900">Filters</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <Search className="w-4 h-4 inline mr-1" />
                Bank Code
              </label>
              <input
                type="text"
                placeholder="e.g., SBI, HDFC"
                value={filterBank}
                onChange={(e) => setFilterBank(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All Status</option>
                <option value="active">Active</option>
                <option value="logged_out">Logged Out</option>
                <option value="expired">Expired</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <Calendar className="w-4 h-4 inline mr-1" />
                From Date
              </label>
              <input
                type="date"
                value={dateRange.start}
                onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <Calendar className="w-4 h-4 inline mr-1" />
                To Date
              </label>
              <input
                type="date"
                value={dateRange.end}
                onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
        </div>

        {/* Records Table */}
        <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
          <div className="px-6 py-4 border-b bg-gray-50">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                <Users className="w-5 h-5 text-blue-600" />
                Login Records
              </h3>
              <span className="text-sm text-gray-500">
                Total: {pagination.total} records
              </span>
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Bank
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Login Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Logout Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center">
                      <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto" />
                      <p className="mt-2 text-gray-500">Loading records...</p>
                    </td>
                  </tr>
                ) : records.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                      No login records found
                    </td>
                  </tr>
                ) : (
                  records.map((record) => (
                    <tr key={record.audit_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <div>
                          <div className="font-medium text-gray-900">{record.username}</div>
                          <div className="text-sm text-gray-500">{record.email}</div>
                          <div className="text-xs text-gray-400 mt-1">
                            {record.roles.join(', ')}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="font-medium text-gray-900">{record.bank_name}</div>
                        <div className="text-sm text-gray-500">{record.bank_code}</div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <Clock className="w-4 h-4 text-gray-400" />
                          <span className="text-sm">{formatDateTime(record.login_time)}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {record.logout_time ? (
                          <div className="flex items-center gap-2">
                            <LogOut className="w-4 h-4 text-gray-400" />
                            <span className="text-sm">{formatDateTime(record.logout_time)}</span>
                          </div>
                        ) : (
                          <span className="text-sm text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm font-medium">
                          {formatDuration(record.session_duration_minutes)}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                          record.status === 'active' 
                            ? 'bg-green-100 text-green-800' 
                            : record.status === 'logged_out'
                            ? 'bg-gray-100 text-gray-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {record.status === 'active' ? (
                            <Activity className="w-3 h-3" />
                          ) : record.status === 'logged_out' ? (
                            <CheckCircle2 className="w-3 h-3" />
                          ) : (
                            <AlertCircle className="w-3 h-3" />
                          )}
                          {record.status}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="px-6 py-4 border-t bg-gray-50">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-500">
                Page {currentPage} of {totalPages}
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPagination(prev => ({ ...prev, offset: Math.max(0, prev.offset - prev.limit) }))}
                  disabled={currentPage === 1}
                  className="flex items-center gap-1 px-3 py-2 border rounded-lg bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="w-4 h-4" />
                  Previous
                </button>
                <button
                  onClick={() => setPagination(prev => ({ ...prev, offset: prev.offset + prev.limit }))}
                  disabled={currentPage >= totalPages}
                  className="flex items-center gap-1 px-3 py-2 border rounded-lg bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
