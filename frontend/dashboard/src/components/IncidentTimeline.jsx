import React from 'react';
import { AlertTriangle } from 'lucide-react';

const SEVERITY_COLORS = ['bg-yellow-500', 'bg-orange-500', 'bg-red-600', 'bg-red-700'];

export default function IncidentTimeline({ incident }) {
  if (!incident) return null;

  const chain = incident.causal_chain && incident.causal_chain.length > 0
    ? incident.causal_chain
    : ['Anomaly detected', 'Service degraded', 'Health check failed', 'Incident triggered'];

  return (
    <div className="glass-card flex flex-col">
      <div className="p-4 border-b border-border bg-card/40 flex items-center justify-between">
        <h3 className="font-semibold text-white flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-400" /> Incident Causal Chain
        </h3>
        <span className="text-xs text-slate-500 font-mono">AI-Generated Timeline</span>
      </div>

      <div className="p-4">
        {/* Horizontal timeline rail */}
        <div className="relative">
          {/* Connecting line */}
          <div className="absolute top-5 left-5 right-5 h-0.5 bg-gradient-to-r from-yellow-500 via-orange-500 to-red-600 opacity-50" />

          {/* Steps */}
          <div className="relative flex justify-between gap-2">
            {chain.map((step, idx) => {
              const progress = idx / Math.max(chain.length - 1, 1);
              const dotColor = idx === chain.length - 1 ? 'bg-red-500 ring-red-500/30' :
                               idx === 0 ? 'bg-yellow-400 ring-yellow-400/30' :
                               'bg-orange-500 ring-orange-500/30';
              return (
                <div key={idx} className="flex flex-col items-center gap-2 flex-1 min-w-0">
                  {/* Dot */}
                  <div className={`w-10 h-10 rounded-full ${dotColor} ring-4 flex items-center justify-center flex-shrink-0 z-10 shadow-lg`}>
                    <span className="text-white text-xs font-bold">{idx + 1}</span>
                  </div>
                  {/* Label */}
                  <p className="text-center text-xs text-slate-300 font-medium leading-tight">{step}</p>
                  {/* Time indicator (relative) */}
                  <p className="text-center text-xs text-slate-600 font-mono">
                    {idx === 0 ? 'T+0s' : `T+${idx * 15}s`}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
