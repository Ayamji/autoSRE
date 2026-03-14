import React from 'react';
import { Bot, Terminal, ShieldAlert, Cpu } from 'lucide-react';

export default function RemediationPanel({ incident, onRemediate }) {
  if (!incident) {
    return (
      <div className="glass-card h-full p-6 flex flex-col items-center justify-center text-center text-slate-500">
        <Bot className="w-12 h-12 mb-4 opacity-20" />
        <p className="font-medium text-sm">AI Copilot Standby</p>
        <p className="text-xs mt-2 px-4">Select an incident to view root cause analysis and let OpenClaw suggest a remediation.</p>
      </div>
    );
  }

  return (
    <div className="glass-card h-full flex flex-col">
      <div className="p-4 border-b border-border bg-card/40 flex items-center gap-3">
        <div className="p-1.5 bg-indigo-500/20 text-indigo-400 rounded-md">
          <Bot className="w-5 h-5" />
        </div>
        <div>
          <h3 className="font-semibold text-white">AI Diagnostics</h3>
          <p className="text-xs font-mono text-slate-400">{incident.id}</p>
        </div>
      </div>
      
      <div className="p-5 flex-1 min-h-[300px] flex flex-col gap-6 overflow-y-auto">
        <div>
          <h4 className="flex items-center gap-2 text-xs font-bold text-slate-400 mb-2 uppercase tracking-wider">
            <ShieldAlert className="w-3.5 h-3.5" /> Root Cause
          </h4>
          <p className="text-sm text-rose-200 bg-rose-500/5 p-3 rounded-lg border border-rose-500/10 leading-relaxed shadow-[inset_0_1px_4px_rgba(0,0,0,0.1)]">
            {incident.root_cause}
          </p>
        </div>

        <div>
          <h4 className="flex items-center gap-2 text-xs font-bold text-slate-400 mb-2 uppercase tracking-wider">
            <Cpu className="w-3.5 h-3.5" /> Explanatory Context
          </h4>
          <p className="text-sm text-slate-300 leading-relaxed">
            {incident.explanation}
          </p>
        </div>
        
        <div className="mt-auto">
          <h4 className="flex items-center gap-2 text-xs font-bold text-slate-400 mb-2 uppercase tracking-wider">
            <Terminal className="w-3.5 h-3.5" /> OpenClaw Action Plan
          </h4>
          
          <div className="bg-darker rounded-lg p-3 border border-border shadow-inner mb-4 font-mono text-xs overflow-x-auto">
            <div className="flex text-emerald-400 mb-1">
              <span className="select-none mr-2">$</span> 
              <span>openclaw execute</span>
            </div>
            <div className="text-slate-300 pl-4 whitespace-pre">
              target: {incident.target || "N/A"}<br/>
              action: {incident.suggested_action}<br/>
              {incident.command && `command: ${incident.command}`}
            </div>
          </div>
          
          <div className="flex gap-3">
            <button 
              onClick={() => onRemediate(incident.id)}
              disabled={incident.status !== 'active'}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              <Terminal className="w-4 h-4" /> 
              {incident.status === 'active' ? "Execute Remediation" : 
               incident.status === 'remediating' ? "Executing..." : "Remediation Applied"}
            </button>
            
            {incident.status === 'recovered' && (
               <a 
                 href={`http://localhost:8000/report/${incident.id}?format=json`}
                 download
                 className="btn-outline flex items-center justify-center gap-2"
                 title="Download JSON Report"
               >
                 JSON
               </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
