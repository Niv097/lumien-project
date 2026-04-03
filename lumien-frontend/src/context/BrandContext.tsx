import React, { createContext, useContext, useState, useEffect } from 'react';

interface BrandConfig {
    name: string;
    logoType: 'SBI' | 'HDFC' | 'ICICI' | 'AXIS' | 'LUMIEN';
    primaryColor: string;
    darkColor: string;
    accentColor: string;
    themePreference: 'light' | 'soft-dark' | 'glass';
    logoPosition: 'left' | 'center';
}

const defaultBrand: BrandConfig = {
    name: 'LUMIEN',
    logoType: 'LUMIEN',
    primaryColor: '#0ea5e9',
    darkColor: '#0c4a6e',
    accentColor: '#38bdf8',
    themePreference: 'light',
    logoPosition: 'left'
};

const bankBrands: Record<string, BrandConfig> = {
    'SBI': {
        name: 'State Bank of India',
        logoType: 'SBI',
        primaryColor: '#003399',
        darkColor: '#001a4d',
        accentColor: '#3b82f6',
        themePreference: 'light',
        logoPosition: 'left'
    },
    'HDFC': {
        name: 'HDFC Bank',
        logoType: 'HDFC',
        primaryColor: '#1e3a8a',
        darkColor: '#172554',
        accentColor: '#ef4444',
        themePreference: 'glass',
        logoPosition: 'left'
    },
    'ICICI': {
        name: 'ICICI Bank',
        logoType: 'ICICI',
        primaryColor: '#ea580c',
        darkColor: '#9a3412',
        accentColor: '#f97316',
        themePreference: 'light',
        logoPosition: 'left'
    },
    'AXIS': {
        name: 'Axis Bank',
        logoType: 'AXIS',
        primaryColor: '#881337',
        darkColor: '#4c0519',
        accentColor: '#9d174d',
        themePreference: 'glass',
        logoPosition: 'left'
    },
};

interface BrandContextType {
    brand: BrandConfig;
    setBankBrand: (bankCode: string, customConfig?: Partial<BrandConfig>) => void;
    resetBrand: () => void;
}

const BrandContext = createContext<BrandContextType | undefined>(undefined);

export const BrandProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [brand, setBrand] = useState<BrandConfig>(defaultBrand);

    const applyTheme = (config: BrandConfig) => {
        const root = document.documentElement;
        root.style.setProperty('--brand-primary', config.primaryColor);
        root.style.setProperty('--brand-dark', config.darkColor);
        root.style.setProperty('--brand-accent', config.accentColor);
        root.style.setProperty('--brand-glow', `${config.primaryColor}33`); // 20% opacity

        // Handle theme preferences
        if (config.themePreference === 'glass') {
            root.classList.add('theme-glass');
        } else {
            root.classList.remove('theme-glass');
        }
    };

    const setBankBrand = (bankCode: string, customConfig?: Partial<BrandConfig>) => {
        const baseConfig = bankBrands[bankCode.toUpperCase()] || defaultBrand;
        const config = { ...baseConfig, ...customConfig };
        setBrand(config);
        applyTheme(config);
    };

    const resetBrand = () => {
        setBrand(defaultBrand);
        applyTheme(defaultBrand);
    };

    useEffect(() => {
        const checkAndApplyBrand = () => {
            // Check if user is logged in and has a bank
            const roles = JSON.parse(localStorage.getItem('lumien_roles') || '[]');
            const bankName = localStorage.getItem('lumien_bank_name');
            const bankCode = localStorage.getItem('lumien_bank_code');
            
            // Check if user has any bank-related role
            const isBankUser = roles.some((role: string) => 
                role.includes('Bank') || role.includes('Branch')
            );
            
            if (isBankUser && bankName && bankName !== 'LUMIEN') {
                // Try to match by bank code first, then by bank name
                const code = bankCode?.toUpperCase() || '';
                const name = bankName.toUpperCase();
                
                // Check if bank code matches known banks
                if (code.includes('SBI') || name.includes('SBI') || name.includes('STATE BANK')) {
                    setBankBrand('SBI');
                } else if (code.includes('HDFC') || name.includes('HDFC')) {
                    setBankBrand('HDFC');
                } else if (code.includes('ICICI') || name.includes('ICICI')) {
                    setBankBrand('ICICI');
                } else if (code.includes('AXIS') || name.includes('AXIS')) {
                    setBankBrand('AXIS');
                } else {
                    // For unknown banks, create a generic brand based on bank name
                    const genericBrand: BrandConfig = {
                        name: bankName,
                        logoType: 'LUMIEN',
                        primaryColor: '#003399',
                        darkColor: '#001a4d',
                        accentColor: '#3b82f6',
                        themePreference: 'light',
                        logoPosition: 'left'
                    };
                    setBrand(genericBrand);
                    applyTheme(genericBrand);
                }
            } else {
                resetBrand();
            }
        };

        // Check immediately on mount
        checkAndApplyBrand();

        // Listen for storage changes (e.g., after login in another tab)
        const handleStorageChange = (e: StorageEvent) => {
            if (e.key === 'lumien_bank_code' || e.key === 'lumien_bank_name' || e.key === 'lumien_brand_set') {
                checkAndApplyBrand();
            }
        };

        window.addEventListener('storage', handleStorageChange);
        return () => window.removeEventListener('storage', handleStorageChange);
    }, []);

    return (
        <BrandContext.Provider value={{ brand, setBankBrand, resetBrand }}>
            {children}
        </BrandContext.Provider>
    );
};

export const useBrand = () => {
    const context = useContext(BrandContext);
    if (!context) throw new Error('useBrand must be used within a BrandProvider');
    return context;
};
