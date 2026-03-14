import React from 'react';
import { Activity, Info, AlertTriangle, CheckCircle } from 'lucide-react';

export default function Timeline({ events }) {
  return (
    <div className="glass-card flex-1 flex flex-col h-[300px]">
      <div className="p-4 border-b border-border bg-card/40 flex justify-between items-center">
        <h3 className="font-semibold text-white flex items-center gap-2">
          <Activity className="w-4 h-4 text-slate-400" /> Event Stream
        </h3>
        <span className="text-xs text-slate-500 font-mono">Live</span>
      </div>
      
      <div className="p-4 flex-1 overflow-y-auto">
        {events.length === 0 ? (
          <div className="h-full flex items-center justify-center text-sm text-slate-500 font-medium">
            Waiting for events...
          </div>
        ) : (
          <div className="space-y-4">
            {events.map((e, idx) => (
              <div key={idx} className="flex gap-3 text-sm relative">
                {/* Timeline line */}
                {idx !== events.length - 1 && (
                  <div className="absolute left-[9px] top-6 bottom-[-16px] w-[1px] bg-border z-0"></div>
                )}
                
                <div className="relative z-10 pt-0.5">
                  {e.type === 'error' ? <AlertTriangle className="w-5 h-5 text-rose-400" /> :
                   e.type === 'success' ? <CheckCircle className="w-5 h-5 text-emerald-400" /> :
                   e.type === 'warning' ? <Activity className="w-5 h-5 text-amber-400" /> :
                   <Info className="w-5 h-5 text-blue-400" />}
                </div>
                <div className="bg-card/50 border border-border/50 rounded-lg py-2 px-3 flex-1 backdrop-blur-sm -mb-2 shadow-sm">
                  <span className="text-xs font-mono text-slate-500 block mb-1">{e.time}</span>
                  <span className="text-slate-300 font-medium">{e.msg}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
