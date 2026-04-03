import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, FileText, Upload, Send, RefreshCw, CheckCircle, Clock, Lock, AlertCircle, Download } from 'lucide-react';
import api from '../api';

const AuditTrail = ({ packId }: { packId: string }) => {
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAuditLogs = async () => {
      try {
        const res = await api.get(`/admin/audit-logs?resource_id=${packId}`);
        setAuditLogs(res.data || []);
      } catch (err) {
        console.error('Failed to fetch audit logs:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchAuditLogs();
  }, [packId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <RefreshCw className="w-6 h-6 animate-spin text-sky-500" />
      </div>
    );
  }

  if (auditLogs.length === 0) {
    return (
      <div className="text-center py-8">
        <FileText className="w-12 h-12 text-slate-300 mx-auto mb-4" />
        <p className="text-slate-500">No audit logs available</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {auditLogs.map((log) => (
        <div key={log.id} className="flex items-start gap-3">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
            log.action === 'CREATED' ? 'bg-emerald-100' :
            log.action === 'SUBMITTED' ? 'bg-sky-100' :
            log.action === 'LOCKED' ? 'bg-amber-100' : 'bg-slate-100'
          }`}>
            {
              log.action === 'CREATED' ? <FileText className="w-4 h-4 text-emerald-600" /> :
              log.action === 'SUBMITTED' ? <Send className="w-4 h-4 text-sky-600" /> :
              log.action === 'LOCKED' ? <Lock className="w-4 h-4 text-amber-600" /> :
              <FileText className="w-4 h-4 text-slate-600" />
            }
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-slate-900">
              {log.action.replace('_', ' ').toLowerCase()}
              {log.user && <span className="text-slate-500 ml-2">by {log.user.username}</span>}
            </p>
            <p className="text-xs text-slate-500">
              {new Date(log.timestamp).toLocaleString()}
            </p>
            {log.old_value && log.new_value && (
              <p className="text-xs text-slate-600 mt-1">
                <span className="text-slate-400">{log.old_value}</span>
                <span className="mx-2 text-sky-400">→</span>
                <span className="text-sky-700 font-medium">{log.new_value}</span>
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

interface KYCPack {
  id: number;
  pack_id: string;
  case_id: string;
  complaint_id: string;
  status: string;
  version: number;
  mandatory_fields: Record<string, any>;
  attachments: any[];
  remarks: string;
  created_at: string;
  submitted_at?: string;
  acknowledgement_ref?: string;
}

export default function KYCPackDetail() {
  const { packId } = useParams<{ packId: string }>();
  const navigate = useNavigate();
  const [pack, setPack] = useState<KYCPack | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [activeTab, setActiveTab] = useState<'fields' | 'attachments' | 'audit'>('fields');

  useEffect(() => {
    loadPack();
  }, [packId]);

  const loadPack = async () => {
    try {
      const res = await api.get(`/operations/kyc-packs/${packId}`);
      setPack(res.data);
    } catch (err) {
      console.error('Failed to load KYC pack:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!confirm('Submit this KYC pack? It will be locked after submission.')) return;
    setSubmitting(true);
    try {
      await api.post(`/operations/kyc-packs/${packId}/submit`);
      loadPack();
    } catch (err) {
      alert('Failed to submit KYC pack');
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', 'KYC_DOCUMENT');
    
    try {
      await api.post(`/operations/kyc-packs/${packId}/attachments`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      loadPack();
    } catch (err) {
      alert('Failed to upload document');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <RefreshCw className="w-8 h-8 animate-spin text-sky-500" />
      </div>
    );
  }

  if (!pack) {
    return (
      <div className="p-6">
        <div className="card p-8 text-center">
          <AlertCircle className="w-12 h-12 text-slate-400 mx-auto mb-4" />
          <p className="text-slate-500">KYC Pack not found</p>
        </div>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      DRAFT: 'bg-slate-100 text-slate-700',
      SUBMITTED: 'bg-emerald-100 text-emerald-700',
      LOCKED: 'bg-amber-100 text-amber-700',
      RETURNED: 'bg-rose-100 text-rose-700'
    };
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${styles[status] || 'bg-slate-100 text-slate-700'}`}>
        {status}
      </span>
    );
  };

  const isEditable = pack.status === 'DRAFT' || pack.status === 'RETURNED';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => navigate('/kyc-packs')}
            className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-slate-600" />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-slate-900">KYC Pack {pack.pack_id}</h1>
              {getStatusBadge(pack.status)}
            </div>
            <p className="text-sm text-slate-500">Case: {pack.case_id} | Complaint: {pack.complaint_id}</p>
          </div>
        </div>
        {isEditable && (
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="btn btn-primary flex items-center gap-2"
          >
            {submitting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            Submit to I4C
          </button>
        )}
      </div>

      {/* Progress */}
      <div className="card p-4">
        <div className="flex items-center justify-between">
          {[
            { label: 'Created', date: pack.created_at, icon: FileText, done: true },
            { label: 'Filled', date: pack.mandatory_fields ? 'Completed' : 'Pending', icon: CheckCircle, done: !!pack.mandatory_fields },
            { label: 'Submitted', date: pack.submitted_at, icon: Send, done: !!pack.submitted_at },
            { label: 'Acknowledged', date: pack.acknowledgement_ref, icon: Lock, done: !!pack.acknowledgement_ref }
          ].map((step, idx) => (
            <div key={idx} className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center ${step.done ? 'bg-sky-500 text-white' : 'bg-slate-200 text-slate-400'}`}>
                <step.icon className="w-5 h-5" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-900">{step.label}</p>
                <p className="text-xs text-slate-500">
                  {step.date ? new Date(step.date).toLocaleDateString() : 'Pending'}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-200">
        {[
          { id: 'fields', label: 'Mandatory Fields', count: Object.keys(pack.mandatory_fields || {}).length },
          { id: 'attachments', label: 'Attachments', count: pack.attachments?.length || 0 },
          { id: 'audit', label: 'Audit Trail' }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-sky-500 text-sky-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            {tab.label}
            {tab.count !== undefined && (
              <span className="ml-2 px-2 py-0.5 bg-slate-100 rounded-full text-xs">{tab.count}</span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="card p-6">
        {activeTab === 'fields' && (
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-widest">Customer Information</h3>
            <div className="grid grid-cols-2 gap-4">
              {[
                { label: 'Customer Name', key: 'customer_name', required: true },
                { label: 'Account Number', key: 'account_number', required: true },
                { label: 'PAN Number', key: 'pan_number', required: true },
                { label: 'Aadhaar Number', key: 'aadhaar_number', required: true },
                { label: 'Mobile Number', key: 'mobile_number', required: true },
                { label: 'Email ID', key: 'email_id', required: false },
                { label: 'Address', key: 'address', required: false },
                { label: 'Date of Birth', key: 'date_of_birth', required: true }
              ].map((field) => (
                <div key={field.key}>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-1">
                    {field.label}
                    {field.required && <span className="text-rose-500 ml-1">*</span>}
                  </label>
                  <input
                    type="text"
                    disabled={!isEditable}
                    defaultValue={pack.mandatory_fields?.[field.key] || ''}
                    className="input w-full"
                    placeholder={`Enter ${field.label}`}
                  />
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'attachments' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-widest">Uploaded Documents</h3>
              {isEditable && (
                <label className="btn btn-secondary flex items-center gap-2 cursor-pointer">
                  <Upload className="w-4 h-4" />
                  Upload Document
                  <input type="file" className="hidden" onChange={handleUpload} />
                </label>
              )}
            </div>
            
            {pack.attachments?.length > 0 ? (
              <div className="space-y-2">
                {pack.attachments.map((att, idx) => (
                  <div key={idx} className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <FileText className="w-8 h-8 text-sky-500" />
                      <div>
                        <p className="text-sm font-medium text-slate-900">{att.filename || att.file_path?.split('/').pop() || 'Document'}</p>
                        <p className="text-xs text-slate-500">
                          {att.document_type || 'KYC_DOCUMENT'} • 
                          {att.file_size ? ` ${(att.file_size / 1024).toFixed(1)} KB` : ''}
                          {att.uploaded_at && ` • ${new Date(att.uploaded_at).toLocaleDateString()}`}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {att.file_path && (
                        <button 
                          onClick={() => window.open(`http://localhost:8000${att.file_path}`, '_blank')}
                          className="p-2 hover:bg-slate-200 rounded-lg"
                          title="Download"
                        >
                          <Download className="w-4 h-4 text-slate-600" />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <FileText className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                <p className="text-slate-500">No documents uploaded</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'audit' && (
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-widest">Audit Trail</h3>
            <AuditTrail packId={pack.pack_id} />
          </div>
        )}
      </div>

      {/* Remarks */}
      <div className="card p-4">
        <label className="block text-xs font-bold text-slate-500 uppercase mb-2">Remarks</label>
        <textarea
          disabled={!isEditable}
          defaultValue={pack.remarks || ''}
          className="input w-full h-24"
          placeholder="Add any additional remarks..."
        />
      </div>
    </div>
  );
}
