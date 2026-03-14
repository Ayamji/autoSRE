import React, { useState, useEffect } from 'react';
import { FileText, BarChart2, GitMerge, History, Settings2, Network, CheckCircle, Loader, Package } from 'lucide-react';

const DATA_SOURCES = [
  { id: 'logs',      label: 'Application Logs',      icon: FileText,  color: 'text-amber-400',   delay: 0    },
  { id: 'metrics',   label: 'System Metrics',        icon: BarChart2, color: 'text-cyan-400',    delay: 350  },
  { id: 'traces',    label: 'Distributed Traces',    icon: GitMerge,  color: 'text-violet-400',  delay: 700  },
  { id: 'deploys',   label: 'Deployment History',    icon: Package,   color: 'text-blue-400',    delay: 1050 },
  { id: 'config',    label: 'Config Changes',        icon: Settings2, color: 'text-rose-400',    delay: 1400 },
  { id: 'depgraph',  label: 'Dependency Graph',      icon: Network,   color: 'text-emerald-400', delay: 1750 },
];

export default function AIAnalysisPanel({ analyzing, incident }) {
  const [checkedSources, setCheckedSources] = useState([]);
  const [animatingIdx, setAnimatingIdx] = useState(0);

  useEffect(() => {
    if (analyzing) {
      setCheckedSources([]);
      setAnimatingIdx(0);
      DATA_SOURCES.forEach((src, i) => {
        setTimeout(() => {
          setCheckedSources(prev => [...prev, src.id]);
          setAnimatingIdx(i + 1);
        }, src.delay + 300);
      });
    }
  }, [analyzing]);

  const isComplete = !analyzing && incident;

  return (
    <div className="glass-card flex flex-col h-full">
      <div className="p-4 border-b border-border bg-card/40 flex items-center justify-between">
        <h3 className="font-semibold text-white flex items-center gap-2">
          <Network className="w-4 h-4 text-indigo-400" /> AI Agent Analysis
        </h3>
        {analyzing && (
          <span className="flex items-center gap-1.5 text-xs text-amber-400 font-mono">
            <Loader className="w-3 h-3 animate-spin" /> Reasoning...
          </span>
        )}
        {isComplete && (
          <span className="flex items-center gap-1.5 text-xs text-emerald-400 font-mono">
            <CheckCircle className="w-3 h-3" /> Analysis Complete
          </span>
        )}
        {!analyzing && !incident && (
          <span className="text-xs text-slate-500 font-mono">Idle · Watching</span>
        )}
      </div>

      <div className="p-4 space-y-3">
        <p className="text-xs text-slate-500 font-mono uppercase tracking-wider mb-3">Data Sources Analyzed</p>
        <div className="grid grid-cols-2 gap-2">
          {DATA_SOURCES.map((src) => {
            const Icon = src.icon;
            const isChecked = checkedSources.includes(src.id) || isComplete;
            const isActive = analyzing && !isChecked;
            return (
              <div
                key={src.id}
                className={`flex items-center gap-2.5 p-2 rounded-lg border transition-all duration-300 ${
                  isChecked
                    ? 'border-emerald-500/30 bg-emerald-500/5'
                    : isActive
                    ? 'border-amber-500/30 bg-amber-500/5 animate-pulse'
                    : 'border-border/40 bg-card/20'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 flex-shrink-0 ${isChecked ? 'text-emerald-400' : src.color}`} />
                <span className={`text-xs font-medium flex-1 ${isChecked ? 'text-slate-300' : 'text-slate-500'}`}>
                  {src.label}
                </span>
                {isChecked ? (
                  <CheckCircle className="w-3 h-3 text-emerald-400 flex-shrink-0" />
                ) : analyzing ? (
                  <div className="w-3 h-3 rounded-full border border-slate-600 flex-shrink-0" />
                ) : null}
              </div>
            );
          })}
        </div>

        {(incident || isComplete) && (
          <div className="mt-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 space-y-2">
            <p className="text-xs font-mono text-rose-300 font-semibold uppercase">Finding</p>
            <p className="text-sm text-slate-200 font-medium">{incident?.type}</p>
            <div className="flex items-center gap-2">
              <span className={`text-xs px-2 py-0.5 rounded-full font-mono ${
                incident?.severity === 'Critical' ? 'bg-red-500/20 text-red-400' :
                incident?.severity === 'High' ? 'bg-orange-500/20 text-orange-400' :
                incident?.severity === 'Medium' ? 'bg-amber-500/20 text-amber-400' :
                'bg-blue-500/20 text-blue-400'
              }`}>
                {incident?.severity}
              </span>
              <span className="text-xs text-slate-500 font-mono">{incident?.timestamp?.substring(11, 19)} UTC</span>
            </div>
            {incident?.root_cause && (
              <p className="text-xs text-slate-400 leading-relaxed">{incident.root_cause}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
