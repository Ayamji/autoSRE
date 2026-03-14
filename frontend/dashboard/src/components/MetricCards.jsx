import React from 'react';
import { Cpu, MemoryStick, ShieldAlert, Server } from 'lucide-react';

const Card = ({ title, value, icon: Icon, unit, sparklineColor, critical }) => (
  <div className={`glass-card p-5 relative overflow-hidden group ${critical ? 'border-rose-500/30' : ''}`}>
    <div className={`absolute top-0 right-0 w-32 h-32 blur-[50px] -mr-16 -mt-16 transition-opacity opacity-20 group-hover:opacity-40 ${sparklineColor}`} />
    
    <div className="flex justify-between items-start mb-4 relative z-10">
      <div className={`p-2.5 rounded-lg ${sparklineColor.replace('bg-', 'bg-').replace('500', '500/20')}`}>
        <Icon className={`w-5 h-5 ${sparklineColor.replace('bg-', 'text-')}`} />
      </div>
      {critical && <span className="flex h-2.5 w-2.5 absolute top-3 right-3">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-rose-500"></span>
      </span>}
    </div>
    
    <div className="relative z-10">
      <h3 className="text-slate-400 text-sm font-medium mb-1">{title}</h3>
      <div className="flex items-baseline gap-1">
        <span className={`text-3xl font-bold tracking-tight ${critical ? 'text-rose-400' : 'text-slate-50'}`}>
          {value}
        </span>
        <span className="text-slate-500 font-medium text-sm">{unit}</span>
      </div>
    </div>
  </div>
);

export default function MetricCards({ metrics, incidentCount }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Card 
        title="System Load (CPU)" 
        value={metrics.cpu.toFixed(1)} 
        unit="%" 
        icon={Cpu} 
        sparklineColor="bg-blue-500"
        critical={metrics.cpu > 85}
      />
      <Card 
        title="Memory Usage" 
        value={metrics.mem.toFixed(1)} 
        unit="%" 
        icon={MemoryStick} 
        sparklineColor="bg-purple-500"
        critical={metrics.mem > 90}
      />
      <Card 
        title="Active Incidents" 
        value={incidentCount || '0'} 
        unit="issues" 
        icon={ShieldAlert} 
        sparklineColor={incidentCount > 0 ? "bg-rose-500" : "bg-emerald-500"}
        critical={incidentCount > 0}
      />
      <Card 
        title="Containers" 
        value={`${metrics.running}/${metrics.total}`} 
        unit="running" 
        icon={Server} 
        sparklineColor={metrics.running < metrics.total ? "bg-amber-500" : "bg-emerald-500"}
        critical={metrics.running < metrics.total}
      />
    </div>
  );
}
