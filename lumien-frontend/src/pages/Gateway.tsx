import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { ShieldCheck, Building2, Landmark, CreditCard, Landmark as BankIcon, ArrowRight, Loader2 } from 'lucide-react';
import { useBrand } from '../context/BrandContext';
import { tenantApi } from '../api';

interface GatewayProps {
    onBankSelect: () => void;
}

interface Bank {
    id: number;
    name: string;
    code: string;
    branch_count: number;
}

const Gateway: React.FC<GatewayProps> = ({ onBankSelect }) => {
    const { setBankBrand } = useBrand();
    const [banks, setBanks] = useState<Bank[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Icon mapping based on bank code
    const getBankIcon = (code: string) => {
        const code_upper = code.toUpperCase();
        if (code_upper.includes('SBI')) return Building2;
        if (code_upper.includes('HDFC')) return Landmark;
        if (code_upper.includes('ICICI')) return CreditCard;
        if (code_upper.includes('AXIS')) return BankIcon;
        return Building2;
    };

    // Color mapping based on bank code
    const getBankColor = (code: string) => {
        const code_upper = code.toUpperCase();
        if (code_upper.includes('SBI')) return 'bg-[#003399]';
        if (code_upper.includes('HDFC')) return 'bg-[#1e3a8a]';
        if (code_upper.includes('ICICI')) return 'bg-[#ea580c]';
        if (code_upper.includes('AXIS')) return 'bg-[#881337]';
        if (code_upper.includes('PNB')) return 'bg-[#b91c1c]';
        if (code_upper.includes('BOB')) return 'bg-[#059669]';
        return 'bg-slate-700';
    };

    // Description mapping
    const getBankDescription = (code: string) => {
        const code_upper = code.toUpperCase();
        if (code_upper.includes('SBI')) return 'Nodal Banking Control';
        if (code_upper.includes('HDFC')) return 'Fraud Monitoring Node';
        if (code_upper.includes('ICICI')) return 'Operational Intelligence';
        if (code_upper.includes('AXIS')) return 'Risk Management Hub';
        return 'Banking Node';
    };

    useEffect(() => {
        const fetchBanks = async () => {
            try {
                const response = await tenantApi.getBanks();
                setBanks(response.data);
                setError(null);
            } catch (err: any) {
                console.error('Failed to fetch banks:', err);
                setError('Failed to load banks. Please try again.');
            } finally {
                setLoading(false);
            }
        };

        fetchBanks();
    }, []);

    const handleSelect = (bank: Bank) => {
        // Store selected bank info in localStorage
        localStorage.setItem('lumien_selected_bank_id', bank.id.toString());
        localStorage.setItem('lumien_selected_bank_code', bank.code);
        localStorage.setItem('lumien_selected_bank_name', bank.name);
        setBankBrand(bank.code);
        onBankSelect();
    };

    const handleLumienAdmin = () => {
        localStorage.setItem('lumien_selected_bank_code', 'LUMIEN');
        localStorage.setItem('lumien_selected_bank_id', '0');
        setBankBrand('LUMIEN');
        onBankSelect();
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-white flex flex-col items-center justify-center p-6">
                <div className="w-20 h-20 bg-slate-900 rounded-3xl flex items-center justify-center shadow-2xl shadow-slate-900/40 mb-8">
                    <Loader2 className="w-12 h-12 text-white animate-spin" />
                </div>
                <h1 className="text-2xl font-bold text-slate-900 font-heading">Loading Banking Nodes...</h1>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-white flex flex-col items-center justify-center p-6">
                <div className="w-20 h-20 bg-rose-100 rounded-3xl flex items-center justify-center mb-8">
                    <ShieldCheck className="w-12 h-12 text-rose-600" />
                </div>
                <h1 className="text-2xl font-bold text-slate-900 font-heading mb-4">Error Loading Banks</h1>
                <p className="text-slate-500 mb-6">{error}</p>
                <button 
                    onClick={() => window.location.reload()} 
                    className="btn btn-primary px-8 py-3"
                >
                    Retry
                </button>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-white flex flex-col items-center justify-center p-6 bg-grid-slate-100">
            {/* Background decorative elements */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-0 -left-1/4 w-1/2 h-1/2 bg-sky-50 rounded-full blur-[120px] opacity-60"></div>
                <div className="absolute bottom-0 -right-1/4 w-1/2 h-1/2 bg-indigo-50 rounded-full blur-[120px] opacity-60"></div>
            </div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-4xl w-full relative z-10"
            >
                <div className="text-center mb-16">
                    <div className="w-20 h-20 bg-slate-900 rounded-3xl flex items-center justify-center shadow-2xl shadow-slate-900/40 mb-8 mx-auto">
                        <ShieldCheck className="w-12 h-12 text-white" />
                    </div>
                    <h1 className="text-5xl font-black text-slate-900 tracking-tighter mb-4 font-heading">
                        Welcome to LUMIEN
                    </h1>
                    <p className="text-xl text-slate-500 font-medium max-w-2xl mx-auto">
                        The Intermediary Financial Intelligence Network. Select your banking node to enter the secure surveillance terminal.
                    </p>
                    <p className="text-sm text-slate-400 mt-4">
                        {banks.length} banking nodes available
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {banks.map((bank, index) => {
                        const Icon = getBankIcon(bank.code);
                        const color = getBankColor(bank.code);
                        const description = getBankDescription(bank.code);
                        
                        return (
                            <motion.button
                                key={bank.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: index * 0.1 }}
                                onClick={() => handleSelect(bank)}
                                className="group relative bg-white border border-slate-100 rounded-[32px] p-8 text-left shadow-lg shadow-slate-200/50 hover:shadow-2xl hover:border-slate-200 transition-all duration-500 hover:-translate-y-2 overflow-hidden"
                            >
                                <div className={`absolute top-0 right-0 w-32 h-32 ${color} opacity-[0.03] group-hover:opacity-[0.08] rounded-full -mr-16 -mt-16 transition-all duration-500 group-hover:scale-150`}></div>

                                <div className="flex items-center gap-6 relative z-10">
                                    <div className={`w-16 h-16 ${color} rounded-2xl flex items-center justify-center shadow-lg shadow-slate-900/10 group-hover:scale-110 transition-transform duration-500`}>
                                        <Icon className="w-8 h-8 text-white" />
                                    </div>
                                    <div className="flex-1">
                                        <h3 className="text-2xl font-black text-slate-900 tracking-tight group-hover:text-slate-900 transition-colors">
                                            {bank.name}
                                        </h3>
                                        <p className="text-slate-500 font-bold uppercase tracking-widest text-[10px] mt-1 group-hover:text-slate-700">
                                            {description}
                                        </p>
                                        <p className="text-slate-400 text-xs mt-1">
                                            {bank.branch_count} branches
                                        </p>
                                    </div>
                                    <div className="w-10 h-10 rounded-full border border-slate-100 flex items-center justify-center group-hover:bg-slate-900 group-hover:border-slate-900 transition-all duration-500">
                                        <ArrowRight className="w-5 h-5 text-slate-400 group-hover:text-white" />
                                    </div>
                                </div>
                            </motion.button>
                        );
                    })}

                    <motion.button
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: banks.length * 0.1 }}
                        onClick={handleLumienAdmin}
                        className="md:col-span-2 group flex items-center justify-between bg-slate-50 border border-slate-100 rounded-[32px] p-8 hover:bg-slate-100 transition-all duration-500"
                    >
                        <div className="flex items-center gap-6">
                            <div className="w-14 h-14 bg-white rounded-2xl flex items-center justify-center shadow-sm">
                                <ShieldCheck className="w-7 h-7 text-sky-600" />
                            </div>
                            <div>
                                <h3 className="text-xl font-black text-slate-900 tracking-tight">Lumien Platform Administration</h3>
                                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mt-1">Universal Network Mastery View</p>
                            </div>
                        </div>
                        <ArrowRight className="w-6 h-6 text-slate-400 group-hover:translate-x-2 transition-transform" />
                    </motion.button>
                </div>

                <div className="mt-16 text-center">
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.4em]">
                        Secure Intermediary Gateway • Multi-Tenant System • Node ID: FID-MASTER
                    </p>
                </div>
            </motion.div>
        </div>
    );
};

export default Gateway;
