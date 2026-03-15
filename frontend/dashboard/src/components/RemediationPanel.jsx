import React, { useState } from 'react';
import { Bot, Terminal, ShieldAlert, Cpu, CheckCircle, Loader, Activity, AlertTriangle, Zap, User, PlayCircle } from 'lucide-react';

export default function RemediationPanel({ incident, onRemediate }) {
  const [overrideConfirm, setOverrideConfirm] = useState(false);

  if (!incident) {
    return (
      <div className="glass-card h-full p-6 flex flex-col items-center justify-center text-center text-slate-500">
        <Bot className="w-12 h-12 mb-4 opacity-20" />
        <p className="font-medium text-sm">AI Copilot Standby</p>
        <p className="text-xs mt-2 px-4">Select an incident to view root cause analysis and let OpenClaw suggest a remediation.</p>
      </div>
    );
  }

  const intentTarget = incident.intent?.target || incident.target || 'faulty-service';
  const intentAction = incident.intent?.action || 'docker_restart';
  const isActive     = incident.status === 'active';
  const isPending    = incident.status === 'pending_approval';
  const isRemediating = incident.status === 'remediating';
  const isRecovered  = incident.status === 'recovered';
  const canFix       = isActive || isPending;

  const needsManualReview = !incident.automation_recommended ||
                             incident.risk_level === 'HIGH' ||
                             incident.risk_level === 'MEDIUM';

  const handleFix = () => {
    setOverrideConfirm(false);
    onRemediate(incident.id, true); // true = approved
  };

  return (
    <div className="glass-card h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-border bg-card/40 flex items-center gap-3">
        <div className="p-1.5 bg-indigo-500/20 text-indigo-400 rounded-md">
          <Bot className="w-5 h-5" />
        </div>
        <div>
          <h3 className="font-semibold text-white">AI Diagnostics</h3>
          <p className="text-xs font-mono text-slate-400">{incident.id}</p>
        </div>
        <div className="ml-auto">
          {isRecovered  && <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full flex items-center gap-1"><CheckCircle className="w-3 h-3" /> Recovered</span>}
          {isRemediating && <span className="text-xs bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded-full flex items-center gap-1 animate-pulse"><Loader className="w-3 h-3 animate-spin" /> Applying fix...</span>}
          {isActive     && <span className="text-xs bg-rose-500/20 text-rose-400 px-2 py-0.5 rounded-full">Active</span>}
          {isPending    && <span className="text-xs bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded-full flex items-center gap-1"><User className="w-3 h-3" /> Pending Approval</span>}
        </div>
      </div>

      <div className="p-5 flex-1 min-h-[300px] flex flex-col gap-5 overflow-y-auto">

        {/* ── Root Cause ───────────────────────────────────────── */}
        <div>
          <h4 className="flex items-center gap-2 text-xs font-bold text-slate-400 mb-2 uppercase tracking-wider">
            <ShieldAlert className="w-3.5 h-3.5" /> Root Cause
          </h4>
          <p className="text-sm text-rose-200 bg-rose-500/5 p-3 rounded-lg border border-rose-500/10 leading-relaxed">
            {incident.root_cause}
          </p>
        </div>

        {/* ── Explanation ─────────────────────────────────────── */}
        {incident.explanation && (
          <div>
            <h4 className="flex items-center gap-2 text-xs font-bold text-slate-400 mb-2 uppercase tracking-wider">
              <Cpu className="w-3.5 h-3.5" /> Explanatory Context
            </h4>
            <p className="text-sm text-slate-300 leading-relaxed">{incident.explanation}</p>
          </div>
        )}

        {/* ── OpenClaw Action Plan + Buttons ───────────────────── */}
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
            {/* Primary fix button — always shown for active/pending incidents */}
            {(isRecovered || isRemediating || canFix) && (
              <button
                onClick={handleFix}
                disabled={!canFix}
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
            )}

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
