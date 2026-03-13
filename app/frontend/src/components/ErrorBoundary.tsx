import { Component, type ReactNode } from 'react';

interface Props { children: ReactNode }
interface State { hasError: boolean; message: string }

export class ErrorBoundary extends Component<Props, State> {
    state: State = { hasError: false, message: '' };

    static getDerivedStateFromError(error: Error): State {
        return { hasError: true, message: error.message || 'Erro inesperado' };
    }

    componentDidCatch(error: Error, info: React.ErrorInfo) {
        console.error('[ErrorBoundary]', error, info.componentStack);
    }

    render() {
        if (!this.state.hasError) return this.props.children;

        return (
            <div style={{
                display: 'flex', flexDirection: 'column', alignItems: 'center',
                justifyContent: 'center', height: '100vh',
                background: 'var(--surface-bg)', color: 'var(--text-primary)',
                gap: 16, padding: 32,
            }}>
                <span style={{ fontSize: 48 }}>⚠</span>
                <h1 style={{ fontSize: 20, fontWeight: 600 }}>Algo deu errado</h1>
                <p style={{ color: 'var(--text-secondary)', maxWidth: 400, textAlign: 'center' }}>
                    {this.state.message}
                </p>
                <button
                    onClick={() => { this.setState({ hasError: false, message: '' }); }}
                    style={{
                        marginTop: 8, padding: '8px 24px', borderRadius: 8,
                        border: 'none', cursor: 'pointer', fontWeight: 600,
                        background: 'linear-gradient(135deg, #8b5cf6, #ec4899)',
                        color: '#fff',
                    }}
                >
                    Tentar novamente
                </button>
            </div>
        );
    }
}
