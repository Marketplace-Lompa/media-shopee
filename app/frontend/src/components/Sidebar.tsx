import './Sidebar.css';
import { Images, Database, Settings, Sparkles } from 'lucide-react';

interface Props {
    activeTab: 'generate' | 'pool' | 'settings';
    onTabChange: (tab: 'generate' | 'pool' | 'settings') => void;
}

const nav = [
    { id: 'generate' as const, icon: Sparkles, label: 'Gerar' },
    { id: 'pool' as const, icon: Database, label: 'Pool' },
    { id: 'settings' as const, icon: Settings, label: 'Config' },
];

export function Sidebar({ activeTab, onTabChange }: Props) {
    return (
        <aside className="sidebar" role="navigation" aria-label="Navegação principal">
            <div className="sidebar-brand">
                <div className="brand-icon" aria-hidden="true">
                    <Images size={20} />
                </div>
                <span className="brand-name">Studio</span>
            </div>

            <nav className="sidebar-nav">
                {nav.map(({ id, icon: Icon, label }) => (
                    <button
                        key={id}
                        className={`nav-item ${activeTab === id ? 'active' : ''}`}
                        onClick={() => onTabChange(id)}
                        aria-current={activeTab === id ? 'page' : undefined}
                        aria-label={label}
                    >
                        <Icon size={18} aria-hidden="true" />
                        <span>{label}</span>
                    </button>
                ))}
            </nav>

            <div className="sidebar-footer">
                <span className="t-xs text-tertiary">v0.1 · Nano Banana 2</span>
            </div>
        </aside>
    );
}
