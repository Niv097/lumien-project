import { useState, useEffect } from 'react';
import { Save, TestTube, Server, Key, Globe, Bell, Database } from 'lucide-react';
import { operationsApi } from '../api';

export function I4CConfigPanel() {
  const [config, setConfig] = useState({
    api_endpoint: '',
    api_key: '',
    client_id: '',
    client_secret: '',
    environment: 'sandbox',
    webhook_url: '',
    enable_notifications: true,
    auto_sync: true
  });
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [logs, setLogs] = useState<any[]>([]);

  useEffect(() => {
    loadConfig();
    loadLogs();
  }, []);

  const loadConfig = async () => {
    try {
      const res = await operationsApi.getI4CConfig();
      if (res.data) {
        setConfig({ ...config, ...res.data });
      }
    } catch (err) {
      console.log('Config not found, using defaults');
    }
  };

  const loadLogs = async () => {
    try {
      const res = await operationsApi.getI4CAPILogs();
      setLogs(res.data?.slice(0, 10) || []);
    } catch (err) {
      console.log('Logs not available');
    }
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      await operationsApi.updateI4CConfig(config);
      alert('I4C configuration saved successfully');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to save configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    try {
      const res = await operationsApi.testI4CConnection();
      alert(res.data?.success ? 'Connection successful!' : `Connection failed: ${res.data?.message}`);
    } catch (err: any) {
      alert('Connection test failed');
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <Globe className="w-5 h-5 text-sky-500" />
            I4C API Integration
          </h3>
          <div className="flex gap-2">
            <button
              onClick={handleTest}
              disabled={testing}
              className="btn btn-secondary flex items-center gap-2"
            >
              <TestTube className="w-4 h-4" />
              {testing ? 'Testing...' : 'Test Connection'}
            </button>
            <button
              onClick={handleSave}
              disabled={loading}
              className="btn btn-primary flex items-center gap-2"
            >
              <Save className="w-4 h-4" />
              {loading ? 'Saving...' : 'Save Config'}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="col-span-2">
            <label className="text-xs font-bold text-slate-500 uppercase flex items-center gap-1">
              <Server className="w-3 h-3" /> API Endpoint
            </label>
            <input
              type="text"
              className="input w-full mt-1"
              placeholder="https://api.i4c.gov.in/v1"
              value={config.api_endpoint}
              onChange={(e) => setConfig({ ...config, api_endpoint: e.target.value })}
            />
          </div>

          <div>
            <label className="text-xs font-bold text-slate-500 uppercase">Client ID</label>
            <input
              type="text"
              className="input w-full mt-1"
              value={config.client_id}
              onChange={(e) => setConfig({ ...config, client_id: e.target.value })}
            />
          </div>

          <div>
            <label className="text-xs font-bold text-slate-500 uppercase flex items-center gap-1">
              <Key className="w-3 h-3" /> Client Secret
            </label>
            <input
              type="password"
              className="input w-full mt-1"
              value={config.client_secret}
              onChange={(e) => setConfig({ ...config, client_secret: e.target.value })}
            />
          </div>

          <div>
            <label className="text-xs font-bold text-slate-500 uppercase">Environment</label>
            <select
              className="input w-full mt-1"
              value={config.environment}
              onChange={(e) => setConfig({ ...config, environment: e.target.value })}
            >
              <option value="sandbox">Sandbox (Testing)</option>
              <option value="production">Production (Live)</option>
            </select>
          </div>

          <div className="col-span-2">
            <label className="text-xs font-bold text-slate-500 uppercase">Webhook URL</label>
            <input
              type="text"
              className="input w-full mt-1"
              placeholder="https://your-domain.com/api/webhooks/i4c"
              value={config.webhook_url}
              onChange={(e) => setConfig({ ...config, webhook_url: e.target.value })}
            />
          </div>

          <div className="flex items-center gap-4 mt-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={config.enable_notifications}
                onChange={(e) => setConfig({ ...config, enable_notifications: e.target.checked })}
              />
              <span className="text-sm text-slate-600 flex items-center gap-1">
                <Bell className="w-4 h-4" /> Enable Notifications
              </span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={config.auto_sync}
                onChange={(e) => setConfig({ ...config, auto_sync: e.target.checked })}
              />
              <span className="text-sm text-slate-600 flex items-center gap-1">
                <Database className="w-4 h-4" /> Auto Sync
              </span>
            </label>
          </div>
        </div>
      </div>

      {/* API Logs */}
      {logs.length > 0 && (
        <div className="card p-6">
          <h4 className="text-sm font-bold text-slate-900 mb-4">Recent API Calls</h4>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {logs.map((log, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <span className={`w-2 h-2 rounded-full ${log.success ? 'bg-emerald-500' : 'bg-rose-500'}`} />
                  <span className="text-sm font-medium text-slate-900">{log.endpoint}</span>
                </div>
                <span className="text-xs text-slate-500">{new Date(log.timestamp).toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
