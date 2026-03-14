import React from 'react';
import { Bot, Terminal, ShieldAlert, Cpu, CheckCircle, Loader, Activity } from 'lucide-react';

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

  // Target is stored in incident.intent.target (mapped from LLM action)
  const intentTarget = incident.intent?.target || incident.target || 'faulty-service';
  const intentAction = incident.intent?.action || 'docker_restart';
  const isActive = incident.status === 'active';
  const isRemediating = incident.status === 'remediating';
  const isRecovered = incident.status === 'recovered';
  const canRemediate = isActive;

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
        {/* Status badge */}
        <div className="ml-auto">
          {isRecovered && <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full flex items-center gap-1"><CheckCircle className="w-3 h-3" /> Recovered</span>}
          {isRemediating && <span className="text-xs bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded-full flex items-center gap-1 animate-pulse"><Loader className="w-3 h-3 animate-spin" /> Applying fix...</span>}
          {isActive && <span className="text-xs bg-rose-500/20 text-rose-400 px-2 py-0.5 rounded-full">Active</span>}
        </div>
      </div>
      
      <div className="p-5 flex-1 min-h-[300px] flex flex-col gap-5 overflow-y-auto">
        <div>
          <h4 className="flex items-center gap-2 text-xs font-bold text-slate-400 mb-2 uppercase tracking-wider">
            <ShieldAlert className="w-3.5 h-3.5" /> Root Cause
          </h4>
          <p className="text-sm text-rose-200 bg-rose-500/5 p-3 rounded-lg border border-rose-500/10 leading-relaxed">
            {incident.root_cause}
          </p>
        </div>

        {incident.explanation && (
          <div>
            <h4 className="flex items-center gap-2 text-xs font-bold text-slate-400 mb-2 uppercase tracking-wider">
              <Cpu className="w-3.5 h-3.5" /> Explanatory Context
            </h4>
            <p className="text-sm text-slate-300 leading-relaxed">{incident.explanation}</p>
          </div>
        )}
        
        {incident.simulation_result && (
          <div className="mb-2">
            <h4 className="flex items-center gap-2 text-xs font-bold text-slate-400 mb-2 uppercase tracking-wider">
              <Activity className="w-3.5 h-3.5" /> Simulation Prediction
            </h4>
            <div className="bg-darker rounded-lg p-4 border border-border shadow-inner text-sm space-y-3">
               <div className="flex justify-between items-center">
                  <span className="text-slate-400">Risk Level:</span>
                  <span className={`font-mono px-2 py-0.5 rounded-full text-xs ${
                    incident.risk_level === 'HIGH' ? 'bg-rose-500/20 text-rose-400' :
                    incident.risk_level === 'MEDIUM' ? 'bg-amber-500/20 text-amber-400' :
                    'bg-emerald-500/20 text-emerald-400'
                  }`}>{incident.risk_level}</span>
               </div>
               <div className="flex justify-between items-center">
                  <span className="text-slate-400">Risk Score:</span>
                  <span className="text-slate-200 font-mono">{incident.risk_score}/100</span>
               </div>
               <div className="flex justify-between items-center">
                  <span className="text-slate-400">Predicted Downtime:</span>
                  <span className="text-slate-200 font-mono">{incident.simulation_result.predicted_downtime}</span>
               </div>
               {incident.simulation_result.affected_services?.length > 0 && (
                 <div className="flex justify-between items-start">
                    <span className="text-slate-400 mt-1">Affected Services:</span>
                    <div className="flex flex-col items-end gap-1">
                      {incident.simulation_result.affected_services.map(s => (
                        <span key={s} className="bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 text-xs px-2 py-0.5 rounded-md">{s}</span>
                      ))}
                    </div>
                 </div>
               )}
               <div className="mt-3 pt-3 border-t border-slate-700/50 flex justify-between items-center">
                  <span className="text-slate-400 uppercase tracking-widest text-[10px]">Recommendation:</span>
                  <span className={`font-medium text-xs ${incident.automation_recommended ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {incident.simulation_result.recommendation}
                  </span>
               </div>
            </div>
          </div>
        )}
        
        <div className="mt-auto">
          <h4 className="flex items-center gap-2 text-xs font-bold text-slate-400 mb-2 uppercase tracking-wider">
            <Terminal className="w-3.5 h-3.5" /> OpenClaw Action Plan
          </h4>
          
          <div className="bg-darker rounded-lg p-3 border border-border shadow-inner mb-4 font-mono text-xs overflow-x-auto">
            <div className="flex text-emerald-400 mb-2">
              <span className="select-none mr-2">$</span>
              <span>openclaw execute</span>
            </div>
            <div className="text-slate-300 pl-4 space-y-0.5">
              <div><span className="text-slate-500">action: </span><span className="text-cyan-400">{intentAction}</span></div>
              <div><span className="text-slate-500">target: </span><span className="text-amber-400">{intentTarget}</span></div>
              <div><span className="text-slate-500">plan:   </span><span className="text-slate-300">{incident.suggested_action}</span></div>
            </div>
          </div>
          
          <div className="flex gap-3">
            <button 
              onClick={() => onRemediate(incident.id)}
              disabled={!canRemediate}
              className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isRemediating ? (
                <><Loader className="w-4 h-4 animate-spin" /> Applying...</>
              ) : isRecovered ? (
                <><CheckCircle className="w-4 h-4" /> Fix Applied</>
              ) : (
                <><Terminal className="w-4 h-4" /> Execute Remediation</>
              )}
            </button>
            
            {isRecovered && (
              <a 
                href={`http://localhost:8000/report/${incident.id}?format=json`}
                download
                className="btn-outline flex items-center justify-center gap-2"
                title="Download JSON Report"
              >
                Report
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
