import React from 'react';
import { AlertCircle, ArrowRight, Play, Download, Clock, Zap } from 'lucide-react';

const Badge = ({ children, color }) => {
  const colors = {
    critical: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    high: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
    medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
    low: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    active: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
    remediating: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    recovered: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
  };
  
  return (
    <span className={`px-2.5 py-1 text-xs font-medium border rounded-full ${colors[color.toLowerCase()] || colors.medium}`}>
      {children}
    </span>
  );
};

export default function IncidentTable({ incidents, selected, onSelect, onRemediate }) {
  if (incidents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-slate-400 min-h-[300px]">
        <div className="bg-emerald-500/10 p-4 rounded-full mb-4">
          <Zap className="w-8 h-8 text-emerald-400" />
        </div>
        <p className="font-medium text-slate-300">All systems operational</p>
        <p className="text-sm mt-1">No active incidents detected by AI.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm text-slate-300">
        <thead className="text-xs uppercase bg-darker/50 text-slate-400 border-b border-border">
          <tr>
            <th className="px-6 py-4 font-semibold">Incident ID</th>
            <th className="px-6 py-4 font-semibold">Type</th>
            <th className="px-6 py-4 font-semibold">Severity</th>
            <th className="px-6 py-4 font-semibold">Status</th>
            <th className="px-6 py-4 font-semibold">Time Detected</th>
            <th className="px-6 py-4 font-semibold text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {incidents.map((incident) => (
            <tr 
              key={incident.id} 
              className={`hover:bg-card/50 transition-colors cursor-pointer ${selected?.id === incident.id ? 'bg-indigo-500/5' : ''}`}
              onClick={() => onSelect(incident)}
            >
              <td className="px-6 py-4 font-mono text-xs">{incident.id}</td>
              <td className="px-6 py-4 font-medium text-slate-200">{incident.type}</td>
              <td className="px-6 py-4"><Badge color={incident.severity}>{incident.severity}</Badge></td>
              <td className="px-6 py-4">
                <Badge color={incident.status}>
                  {incident.status.charAt(0).toUpperCase() + incident.status.slice(1)}
                  {incident.status === 'remediating' && <span className="inline-block ml-1 animate-pulse">...</span>}
                </Badge>
              </td>
              <td className="px-6 py-4 text-slate-400 flex items-center gap-2">
                <Clock className="w-3 h-3" />
                {new Date(incident.timestamp).toLocaleTimeString()}
              </td>
              <td className="px-6 py-4 text-right">
                <div className="flex items-center justify-end gap-3">
                  {incident.status === 'active' && (
                    <button 
                      onClick={(e) => { e.stopPropagation(); onRemediate(incident.id); }}
                      className="group flex items-center gap-1.5 text-xs font-medium text-indigo-400 hover:text-indigo-300 transition-colors bg-indigo-400/10 px-3 py-1.5 rounded-md hover:bg-indigo-400/20"
                    >
                      <Play className="w-3 h-3 fill-current" />
                      Fix
                    </button>
                  )}
                  {incident.status === 'recovered' && (
                    <a 
                      href={`http://localhost:8000/report/${incident.id}?format=pdf`}
                      target="_blank"
                      rel="noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="text-xs flex items-center gap-1.5 text-slate-400 hover:text-white transition-colors p-1.5 hover:bg-slate-700/50 rounded"
                      title="Download PDF Report"
                    >
                      <Download className="w-4 h-4" />
                    </a>
                  )}
                  <ArrowRight className={`w-4 h-4 text-slate-500 transition-transform ${selected?.id === incident.id ? 'translate-x-1 text-indigo-400' : ''}`} />
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
