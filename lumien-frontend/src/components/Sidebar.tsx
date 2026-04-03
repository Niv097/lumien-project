import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
    LayoutDashboard,
    Inbox,
    Coins,
    Clock,
    AlertTriangle,
    FileSearch,
    Settings as SettingsIcon,
    ShieldCheck,
    FileText,
    MessageSquare,
    RotateCcw,
    Scale,
    Shield,
    Database,
    Activity,
    LogOut,
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { useBrand } from '../context/BrandContext';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

const BankLogo: React.FC<{ type: string; color: string }> = ({ type, color }) => {
    switch (type) {
        case 'SBI':
            return (
                <div className="w-8 h-8 rounded-lg flex items-center justify-center font-black text-white text-xs" style={{ backgroundColor: color }}>
                    SBI
                </div>
            );
        case 'HDFC':
            return (
                <div className="w-8 h-8 rounded-lg flex items-center justify-center font-black text-white text-xs bg-[#1e3a8a] border-2 border-red-500">
                    H
                </div>
            );
        case 'ICICI':
            return (
                <div className="w-8 h-8 rounded-full flex items-center justify-center font-black text-white text-xs bg-gradient-to-br from-orange-500 to-orange-700 shadow-lg">
                    i
                </div>
            );
        case 'AXIS':
            return (
                <div className="w-8 h-8 rounded-md flex items-center justify-center font-black text-white text-xs bg-[#881337] transform rotate-45">
                    <span className="transform -rotate-45">A</span>
                </div>
            );
        default:
            return (
                <div className="w-8 h-8 bg-[var(--brand-primary)] rounded-lg flex items-center justify-center shadow-lg shadow-[var(--brand-glow)]">
                    <ShieldCheck className="w-5 h-5 text-white" />
                </div>
            );
    }
};

const Sidebar: React.FC = () => {
    const navigate = useNavigate();
    const { brand } = useBrand();
    const roles = JSON.parse(localStorage.getItem('lumien_roles') || '[]');
    const isSuperAdmin = roles.includes("Lumien Super Admin");
    const isOps = roles.includes("Lumien Operations Manager");
    const isAuditor = roles.includes("Audit & Compliance Officer");
    const isObserver = roles.includes("I4C Observer");
    const isBankUser = roles.includes("Bank HQ Integration User");

    const canSeeSLA = isSuperAdmin || isOps || isObserver;
    const canSeeAudit = isSuperAdmin || isAuditor;
    const canSeeSettings = isSuperAdmin;
    const canSeeMisroute = isSuperAdmin || isOps;

    const navItems = [
        {
            group: 'Core', items: [
                { name: 'Dashboard', path: '/', icon: LayoutDashboard, visible: true },
                { name: 'Case Inbox', path: '/inbox', icon: Inbox, visible: true },
            ]
        },
        {
            group: 'Operations', items: [
                { name: 'KYC Packs', path: '/kyc-packs', icon: FileText, visible: isBankUser },
                { name: 'LEA Requests', path: '/lea-requests', icon: Shield, visible: isBankUser },
                { name: 'Grievances', path: '/grievances', icon: MessageSquare, visible: isBankUser },
                { name: 'Money Restoration', path: '/restoration', icon: RotateCcw, visible: isBankUser },
                { name: 'Reconciliation', path: '/reconciliation', icon: Scale, visible: isBankUser },
            ]
        },
        {
            group: 'Intelligence', items: [
                { name: 'SLA Monitor', path: '/sla', icon: Clock, visible: canSeeSLA },
                { name: 'Misroutes', path: '/misroute', icon: AlertTriangle, visible: canSeeMisroute },
                { name: 'Demo Dataset', path: '/demo-dataset', icon: Database, visible: canSeeMisroute || canSeeSLA || canSeeAudit },
                { name: 'Audit Logs', path: '/admin/audit-logs', icon: FileSearch, visible: canSeeAudit },
                { name: 'Login Records', path: '/admin/login-audit', icon: Activity, visible: isSuperAdmin },
            ]
        },
        {
            group: 'Governance', items: [
                { name: 'Platform Settings', path: '/settings', icon: SettingsIcon, visible: canSeeSettings },
            ]
        }
    ];

    const handleLogout = () => {
        localStorage.clear();
        window.location.href = '/';
    };

    return (
        <div className="w-64 bg-white border-r border-slate-200 h-screen fixed left-0 top-0 flex flex-col z-50">
            <div className="p-8">
                <div className="flex items-center gap-3">
                    <BankLogo type={brand.logoType} color={brand.primaryColor} />
                    <h1 className="text-xl font-bold tracking-tight text-slate-900">
                        {brand.logoType === 'LUMIEN' ? 'LUMIEN' : brand.name.replace(' Bank', '').toUpperCase()}
                    </h1>
                </div>
                <p className="text-[10px] text-slate-400 mt-1 uppercase tracking-widest font-bold">
                    {brand.logoType === 'LUMIEN' ? 'Intermediary Hub' : 'Dedicated Portal node'}
                </p>
            </div>

            <nav className="flex-1 px-4 py-2 space-y-8 overflow-y-auto">
                {navItems.map((group) => {
                    const visibleItems = group.items.filter(i => i.visible);
                    if (visibleItems.length === 0) return null;

                    return (
                        <div key={group.group}>
                            <p className="px-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">{group.group}</p>
                            <div className="space-y-1">
                                {visibleItems.map((item) => (
                                    <NavLink
                                        key={item.name}
                                        to={item.path}
                                        className={({ isActive }) => cn(
                                            "sidebar-link",
                                            isActive && "active"
                                        )}
                                    >
                                        <item.icon className="w-4 h-4 mr-3" />
                                        <span className="text-sm">{item.name}</span>
                                    </NavLink>
                                ))}
                            </div>
                        </div>
                    );
                })}
            </nav>

            <div className="p-4 mt-auto border-t border-slate-100 bg-slate-50/50">
                <div className="flex items-center gap-3 px-4 py-2">
                    <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-xs font-bold text-slate-600">
                        {localStorage.getItem('lumien_user')?.substring(0, 2).toUpperCase()}
                    </div>
                    <div className="flex-1 overflow-hidden">
                        <p className="text-sm font-bold text-slate-900 truncate">
                            {typeof localStorage.getItem('lumien_user') === 'string' && localStorage.getItem('lumien_user')?.startsWith('{')
                                ? JSON.parse(localStorage.getItem('lumien_user') || '{}').name
                                : localStorage.getItem('lumien_user')}
                        </p>
                        <p className="text-[10px] text-slate-500 truncate font-bold uppercase tracking-widest">
                            {(isSuperAdmin || isOps || isAuditor) ? 'Platform Control' : brand.name}
                        </p>
                    </div>
                    <button
                        onClick={handleLogout}
                        className="text-slate-400 hover:text-red-500 transition-colors"
                    >
                        <LogOut className="w-4 h-4" />
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Sidebar;
