import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Critical UI Error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#020617] flex items-center justify-center p-6 text-center">
          <div className="glass-card max-w-md p-8 border-rose-500/30">
            <div className="bg-rose-500/20 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
              <AlertTriangle className="w-8 h-8 text-rose-400" />
            </div>
            <h1 className="text-xl font-bold text-white mb-2">Dashboard Incident</h1>
            <p className="text-slate-400 text-sm mb-6 leading-relaxed">
              The dashboard encountered a critical rendering error. This is likely due to malformed AI analysis data.
            </p>
            <div className="bg-darker p-3 rounded-lg border border-border mb-6 text-left overflow-x-auto">
              <code className="text-[10px] text-rose-300 font-mono">
                {this.state.error?.toString() || "Unknown error"}
              </code>
            </div>
            <button 
              onClick={() => window.location.reload()}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              <RefreshCw className="w-4 h-4" /> Hard Reload Dashboard
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
