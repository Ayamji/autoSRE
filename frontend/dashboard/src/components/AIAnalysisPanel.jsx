import React, { useState, useEffect } from 'react';
import { 
  FileText, BarChart2, GitMerge, History, Settings2, Network, 
  CheckCircle, Loader, Package, Info, ChevronDown, ChevronUp, BrainCircuit, Terminal
} from 'lucide-react';

const DATA_SOURCES = [
  { id: 'metrics',   label: 'System Metrics',        icon: BarChart2, color: 'text-cyan-400'    },
  { id: 'logs',      label: 'Application Logs',      icon: FileText,  color: 'text-amber-400'   },
  { id: 'traces',    label: 'Distributed Traces',    icon: GitMerge,  color: 'text-violet-400'  },
  { id: 'deploys',   label: 'Deployment History',    icon: Package,   color: 'text-blue-400'    },
  { id: 'config',    label: 'Config Changes',        icon: Settings2, color: 'text-rose-400'    },
];

export default function AIAnalysisPanel({ analyzing, incident }) {
  const [showPromptBlueprint, setShowPromptBlueprint] = useState(false);
  const [showInternalLogic, setShowInternalLogic] = useState(false);

  const isComplete = !analyzing && incident;

  return (
    <div className="glass-card flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-white/5 bg-white/[0.02] flex items-center justify-between">
        <h3 className="font-semibold text-white flex items-center gap-2">
          <BrainCircuit className="w-4 h-4 text-indigo-400" /> AI Diagnostic Engine
        </h3>
        {analyzing ? (
          <span className="flex items-center gap-1.5 text-[10px] text-amber-400 font-bold uppercase tracking-widest">
            <Loader className="w-3 h-3 animate-spin" /> Analyzing Context...
          </span>
        ) : isComplete ? (
          <span className="flex items-center gap-1.5 text-[10px] text-emerald-400 font-bold uppercase tracking-widest">
            <CheckCircle className="w-3 h-3" /> Analysis Ready
          </span>
        ) : (
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Awaiting Trigger</span>
        )}
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar">
        <div className="p-4 space-y-4">
          {/* Prompt Blueprint Toggle */}
          <div className="rounded-xl border border-white/5 bg-white/[0.01] overflow-hidden">
            <button 
              onClick={() => setShowPromptBlueprint(!showPromptBlueprint)}
              className="w-full flex items-center justify-between p-3 hover:bg-white/[0.02] transition-colors"
            >
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                <Terminal className="w-3 h-3" /> Prompt Blueprint
              </span>
              {showPromptBlueprint ? <ChevronUp className="w-3 h-3 text-slate-500" /> : <ChevronDown className="w-3 h-3 text-slate-500" />}
            </button>
            {showPromptBlueprint && (
              <div className="p-3 pt-0 grid grid-cols-1 gap-1.5 border-t border-white/5 bg-black/20">
                <p className="text-[9px] text-slate-500 mb-2 leading-relaxed">
                  These 5 diagnostic streams are aggregated and injected into the Gemini-2.0-Flash prompt context:
                </p>
                {DATA_SOURCES.map((src) => {
                  const Icon = src.icon;
                  return (
                    <div key={src.id} className="flex items-center gap-2.5 p-1.5 rounded-md bg-white/[0.02]">
                      <Icon className={`w-3 h-3 ${src.color}`} />
                      <span className="text-[10px] font-medium text-slate-300">{src.label}</span>
                      <div className="ml-auto flex items-center gap-1">
                        <div className="w-1 h-1 rounded-full bg-emerald-500 animate-pulse" />
                        <span className="text-[8px] text-emerald-500/70 font-mono uppercase">Streaming</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Finding Section */}
          {(incident || isComplete) && (
            <div className="space-y-4">
              <div className="p-4 rounded-xl relative overflow-hidden bg-rose-500/5 border border-rose-500/20">
                <div className="absolute top-0 left-0 w-1 h-full bg-rose-500" />
                <p className="text-[10px] font-bold text-rose-400 uppercase tracking-widest mb-2">Finding</p>
                <p className="text-base font-bold text-white mb-2">{incident?.type}</p>
                
                {incident?.executive_summary && (
                  <p className="text-xs text-slate-300 italic mb-4 border-l-2 border-white/10 pl-3 py-1 bg-white/[0.02]">
                    "{incident.executive_summary}"
                  </p>
                )}

                <div className="flex items-center gap-3 mb-4">
                  <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                    incident?.severity === 'Critical' ? 'bg-red-500/20 text-red-400' :
                    incident?.severity === 'High' ? 'bg-orange-500/20 text-orange-400' :
                    'bg-amber-500/20 text-amber-400'
                  }`}>
                    {incident?.severity} Severity
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">{incident?.timestamp?.substring(11, 16)} UTC</span>
                </div>

                <div className="space-y-2">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Root Cause</p>
                  <p className="text-xs text-slate-400 leading-relaxed font-normal bg-black/20 p-2.5 rounded-lg border border-white/5">
                    {incident?.root_cause}
                  </p>
                </div>
              </div>

              {/* Internal Reasoning Toggle */}
              {incident?.internal_reasoning && (
                <div className="rounded-xl border border-white/5 bg-indigo-500/[0.02] overflow-hidden">
                  <button 
                    onClick={() => setShowInternalLogic(!showInternalLogic)}
                    className="w-full flex items-center justify-between p-3 hover:bg-white/[0.02] transition-colors"
                  >
                    <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest flex items-center gap-2">
                      <Info className="w-3 h-3" /> AI Internal Logic
                    </span>
                    {showInternalLogic ? <ChevronUp className="w-3 h-3 text-slate-500" /> : <ChevronDown className="w-3 h-3 text-slate-500" />}
                  </button>
                  {showInternalLogic && (
                    <div className="p-4 pt-0 text-xs text-slate-400 leading-relaxed font-mono whitespace-pre-wrap animate-in fade-in slide-in-from-top-1 duration-300">
                      {incident.internal_reasoning}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {!analyzing && !incident && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="w-12 h-12 rounded-full bg-white/[0.02] border border-white/5 flex items-center justify-center mb-4">
                <Network className="w-6 h-6 text-slate-600" />
              </div>
              <p className="text-xs text-slate-500 font-medium">AutoSRE is observing cluster telemetry.</p>
              <p className="text-[10px] text-slate-600 font-mono mt-1 uppercase tracking-tighter">Passive Audit Mode Active</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
