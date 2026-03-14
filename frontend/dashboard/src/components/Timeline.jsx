import React, { useRef, useEffect } from 'react';
import { Activity, Info, AlertTriangle, CheckCircle } from 'lucide-react';

const typeStyles = {
  error:   { icon: AlertTriangle, cls: 'text-rose-400',    bg: 'bg-rose-500/10 border-rose-500/20' },
  success: { icon: CheckCircle,   cls: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' },
  warning: { icon: Activity,      cls: 'text-amber-400',   bg: 'bg-amber-500/10 border-amber-500/20' },
  info:    { icon: Info,          cls: 'text-blue-400',    bg: 'bg-blue-500/10 border-blue-500/20' },
};

export default function Timeline({ events }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  return (
    <div className="glass-card flex flex-col" style={{ minHeight: '180px', maxHeight: '260px' }}>
      <div className="p-4 border-b border-border bg-card/40 flex justify-between items-center">
        <h3 className="font-semibold text-white flex items-center gap-2">
          <Activity className="w-4 h-4 text-emerald-400" />
          <span>Event Stream</span>
        </h3>
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            {events.length > 0 && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>}
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="text-xs text-slate-500 font-mono">Live · {events.length} events</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        {events.length === 0 ? (
          <div className="h-full flex items-center justify-center text-sm text-slate-500">
            Waiting for events...
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {events.map((e, idx) => {
              const style = typeStyles[e.type] || typeStyles.info;
              const Icon = style.icon;
              return (
                <div key={idx} className={`flex items-start gap-3 px-3 py-2 rounded-lg border text-sm ${style.bg}`}>
                  <Icon className={`w-4 h-4 mt-0.5 flex-shrink-0 ${style.cls}`} />
                  <div className="flex-1 min-w-0">
                    <span className={`font-medium ${style.cls} mr-2`}>{e.msg}</span>
                  </div>
                  <span className="text-xs font-mono text-slate-500 flex-shrink-0">{e.time}</span>
                </div>
              );
            })}
            <div ref={bottomRef} />
          </div>
        )}
      </div>
    </div>
  );
}
