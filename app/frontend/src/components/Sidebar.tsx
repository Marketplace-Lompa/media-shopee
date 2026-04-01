import './Sidebar.css';
import { Images, BookOpen, Sparkles } from 'lucide-react';

export type Tab = 'criar' | 'historico' | 'biblioteca';

interface Props {
    activeTab: Tab;
    onTabChange: (tab: Tab) => void;
}

const nav = [
    { id: 'criar' as const, icon: Sparkles, label: 'Criar' },
    { id: 'historico' as const, icon: Images, label: 'Histórico' },
    { id: 'biblioteca' as const, icon: BookOpen, label: 'Biblioteca' },
];

export function Sidebar({ activeTab, onTabChange }: Props) {
    return (
        <aside className="sidebar" aria-label="Barra lateral">
            <header className="sidebar-brand">
                <div className="brand-logo" aria-hidden="true">
                    <img src="/studio-logo.png" alt="" />
                </div>
                <span className="brand-name">Studio</span>
            </header>

            <nav className="sidebar-nav" aria-label="Navegação principal">
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

            <footer className="sidebar-footer">
                <span className="t-xs text-tertiary">v0.2</span>
            </footer>
        </aside>
    );
}
