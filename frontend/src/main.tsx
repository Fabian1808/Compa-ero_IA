import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles/globals.css'

class ErrorBoundary extends React.Component<{children: React.ReactNode}, {error: Error | null}> {
  constructor(props: any) {
    super(props);
    this.state = { error: null };
  }
  static getDerivedStateFromError(error: Error) {
    return { error };
  }
  render() {
    if (this.state.error) {
      return (
        <div style={{padding: '20px', fontFamily: 'monospace', background: '#fee', color: '#900', borderRadius: '8px', margin: '20px'}}>
          <h2>Error de la aplicacion</h2>
          <pre style={{whiteSpace: 'pre-wrap', wordBreak: 'break-word'}}>
            {this.state.error.toString()}
            {'\n'}
            {(this.state.error as any).stack}
          </pre>
        </div>
      );
    }
    return this.props.children;
  }
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
)
