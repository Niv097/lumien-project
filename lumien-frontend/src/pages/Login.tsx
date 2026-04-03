import React, { useState } from 'react';
import { ShieldCheck, Lock, User as UserIcon, Loader2 } from 'lucide-react';
import { authApi } from '../api';
import { useBrand } from '../context/BrandContext';

const Login: React.FC<{ onLogin: () => void }> = ({ onLogin }) => {
    const { setBankBrand, resetBrand } = useBrand();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        localStorage.clear();
        setLoading(true);
        setError('');
        try {
            const res = await authApi.login(new URLSearchParams({
                username,
                password,
            }));
            localStorage.setItem('lumien_token', res.data.access_token);
            localStorage.setItem('lumien_user', res.data.user);
            localStorage.setItem('lumien_roles', JSON.stringify(res.data.roles));

            // Store bank and branch IDs for multi-tenant filtering
            if (res.data.bank_id) {
                localStorage.setItem('lumien_bank_id', res.data.bank_id.toString());
            }
            if (res.data.branch_id) {
                localStorage.setItem('lumien_branch_id', res.data.branch_id.toString());
            }

            if (res.data.bank_code) {
                localStorage.setItem('lumien_bank_code', res.data.bank_code);
                localStorage.setItem('lumien_bank_name', res.data.bank_name);
                localStorage.setItem('lumien_brand_set', 'true'); // Flag for BrandContext
                setBankBrand(res.data.bank_code);
            } else {
                resetBrand();
            }

            onLogin();
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Authentication failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen premium-gradient flex items-center justify-center p-4">
            <div className="max-w-md w-full relative">
                {/* Decorative Elements */}
                <div className="absolute -top-20 -left-20 w-64 h-64 bg-sky-500/20 rounded-full blur-3xl animate-pulse-slow"></div>
                <div className="absolute -bottom-20 -right-20 w-64 h-64 bg-emerald-500/20 rounded-full blur-3xl animate-pulse-slow"></div>

                <div className="text-center mb-10 relative z-10">
                    <div className="inline-flex p-4 rounded-3xl bg-white/5 border border-white/10 backdrop-blur-xl shadow-2xl mb-6">
                        <div className="w-16 h-16 bg-sky-600 rounded-2xl flex items-center justify-center shadow-lg shadow-sky-500/40">
                            <ShieldCheck className="w-10 h-10 text-white" />
                        </div>
                    </div>
                    <h1 className="text-4xl font-black text-sky-900 tracking-tighter font-heading mb-2">LUMIEN</h1>
                    <div className="flex items-center justify-center gap-2">
                        <span className="h-px w-8 bg-slate-200"></span>
                        <p className="text-sky-600 text-[10px] font-black uppercase tracking-[0.2em]">INNOVATE-AUTOMATE-ELEVATE</p>
                        <span className="h-px w-8 bg-slate-200"></span>
                    </div>
                </div>

                <div className="glass-card rounded-[32px] p-10 relative z-10">
                    <form onSubmit={handleSubmit} className="space-y-6">
                        {error && (
                            <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl text-rose-400 text-xs font-bold flex items-center gap-3">
                                <div className="w-1 h-1 bg-rose-500 rounded-full"></div>
                                {error}
                            </div>
                        )}
                        <div className="space-y-2">
                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Operator Identity</label>
                            <div className="relative group">
                                <UserIcon className="w-3 h-3 absolute left-2 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-sky-400 transition-colors" />
                                <input
                                    type="text"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    className="w-full pl-7 pr-2 py-4 bg-slate-50 border border-slate-200 rounded text-xs text-slate-700 placeholder:text-slate-400 focus:ring-1 focus:ring-sky-500/30 focus:border-sky-400 transition-all outline-none"
                                    placeholder="email"
                                    required
                                />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Security Keyphrase</label>
                            <div className="relative group">
                                <Lock className="w-3 h-3 absolute left-2 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-sky-400 transition-colors" />
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full pl-7 pr-2 py-4 bg-slate-50 border border-slate-200 rounded text-xs text-slate-700 placeholder:text-slate-400 focus:ring-1 focus:ring-sky-500/30 focus:border-sky-400 transition-all outline-none"
                                    placeholder="password"
                                    required
                                />
                            </div>
                        </div>
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-[var(--brand-primary)] hover:opacity-90 text-white font-black py-4 rounded-2xl shadow-xl shadow-[var(--brand-glow)] transition-all flex items-center justify-center gap-3 disabled:opacity-50 active:scale-95 group"
                        >
                            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : (
                                <>
                                    <span>Initialize Session</span>
                                    <ShieldCheck className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-all -translate-x-2 group-hover:translate-x-0" />
                                </>
                            )}
                        </button>
                    </form>
                    <div className="mt-10 pt-8 border-t border-slate-100 text-center">
                        <p className="text-[9px] text-slate-400 font-black uppercase tracking-[0.3em]">
                            End-to-End Encryption • Node: FID-0129-PX
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Login;
