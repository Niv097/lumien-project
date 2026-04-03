import React, { useEffect, useState } from 'react';
import { adminApi } from '../api';
import { Shield, Building2, UserPlus, Save, Globe, Lock, Loader2, CheckCircle2 } from 'lucide-react';
import { I4CConfigPanel } from '../components/I4CConfigPanel';
import { cn } from '../utils/cn';

const Settings: React.FC = () => {
    const [banks, setBanks] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('banks');

    useEffect(() => {
        const fetchBanks = async () => {
            try {
                const res = await adminApi.getBanks();
                setBanks(res.data);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchBanks();
    }, []);

    const tabs = [
        { id: 'banks', name: 'Connected Banks', icon: Building2 },
        { id: 'users', name: 'User Directory', icon: UserPlus },
        { id: 'security', name: 'Security Policy', icon: Lock },
        { id: 'integration', name: 'I4C Integration', icon: Globe },
    ];

    return (
        <div className="space-y-8 max-w-7xl mx-auto pb-20">
            <header>
                <h1 className="text-3xl font-bold tracking-tight text-slate-900 font-heading">Platform Administration</h1>
                <p className="text-slate-500 mt-1">Global governance, bank integrations, and security parameters.</p>
            </header>

            <div className="flex flex-col lg:flex-row gap-8">
                {/* Tabs Sidebar */}
                <div className="lg:w-64 flex flex-col gap-1">
                    {tabs.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={cn(
                                "flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all text-left",
                                activeTab === tab.id
                                    ? "bg-slate-900 text-white shadow-lg shadow-slate-900/10"
                                    : "text-slate-500 hover:bg-slate-100"
                            )}
                        >
                            <tab.icon className="w-4 h-4" />
                            {tab.name}
                        </button>
                    ))}
                </div>

                {/* Content Area */}
                <div className="flex-1 space-y-8">
                    {activeTab === 'banks' && (
                        <div className="space-y-6">
                            <div className="flex justify-between items-center">
                                <h2 className="text-xl font-bold text-slate-900">Synchronized Banking Nodes</h2>
                                <button className="btn btn-primary text-xs font-bold py-2 bg-sky-600">Connect New Bank</button>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {loading ? (
                                    <div className="col-span-2 py-20 text-center"><Loader2 className="w-8 h-8 animate-spin text-sky-600 mx-auto" /></div>
                                ) : banks.map((bank) => (
                                    <div key={bank.id} className="card p-5 border-slate-100 hover:border-sky-200 transition-all flex justify-between items-center group">
                                        <div className="flex items-center gap-4">
                                            <div className="w-12 h-12 bg-slate-50 rounded-xl flex items-center justify-center group-hover:bg-sky-50 transition-colors">
                                                <Building2 className="w-6 h-6 text-slate-400 group-hover:text-sky-600" />
                                            </div>
                                            <div>
                                                <h3 className="text-sm font-bold text-slate-900">{bank.name}</h3>
                                                <div className="flex gap-2 items-center mt-1">
                                                    <span className="text-[10px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded font-mono font-bold">{bank.code}</span>
                                                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">{bank.integration_model}</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex flex-col items-end">
                                            <span className="flex items-center gap-1 text-[10px] font-black text-emerald-600 uppercase tracking-widest bg-emerald-50 px-2 py-1 rounded">
                                                <CheckCircle2 className="w-3 h-3" /> Operational
                                            </span>
                                            <p className="text-[10px] text-slate-400 mt-2 font-bold">24h SLA Guarantee</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {activeTab === 'integration' && <I4CConfigPanel />}

                    {activeTab !== 'banks' && activeTab !== 'integration' && (
                        <div className="card p-12 text-center bg-slate-50/50 border-dashed border-2 border-slate-200">
                            <Shield className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                            <h3 className="text-lg font-bold text-slate-900">Section Under Governance</h3>
                            <p className="text-slate-500 text-sm mt-2 max-w-sm mx-auto">
                                This administrative module is currently in read-only mode for the current session. Contact platform architect for write access.
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Settings;
