import React from 'react';
import { LayoutDashboard, History, BookOpen, Settings, ExternalLink } from 'lucide-react';

const SideNav = ({ activeView, onViewChange }) => {
  const navItems = [
    { id: 'dashboard', label: 'Real-time Dashboard', icon: LayoutDashboard },
    { id: 'history', label: 'Incident History', icon: History },
    { id: 'memory', label: 'Knowledge Base', icon: BookOpen },
  ];

  return (
    <div className="w-64 h-screen bg-[#0f172a] border-r border-slate-800/50 flex flex-col fixed left-0 top-0">
      <div className="p-6 border-b border-slate-800/50">
        <div className="flex items-center gap-3">
          <div className="bg-indigo-500 rounded-lg p-1.5 shadow-lg shadow-indigo-500/20">
            <LayoutDashboard className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">AutoSRE</h1>
            <p className="text-[10px] text-indigo-400 font-bold uppercase tracking-widest">Enterprise AI</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-2 mt-4">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onViewChange(item.id)}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group ${
              activeView === item.id 
                ? 'bg-indigo-600/10 text-indigo-400 border border-indigo-500/20' 
                : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
            }`}
          >
            <item.icon className={`w-5 h-5 ${activeView === item.id ? 'text-indigo-400' : 'text-slate-400 group-hover:text-slate-200'}`} />
            <span className="font-semibold text-sm">{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="p-4 border-t border-slate-800/50 space-y-4">
        <a 
          href="http://localhost:3000" 
          target="_blank" 
          rel="noreferrer"
          className="flex items-center justify-between px-4 py-3 text-sm text-slate-400 hover:text-slate-200 transition-colors bg-slate-800/20 rounded-xl"
        >
          <span className="font-medium">Grafana Dashboard</span>
          <ExternalLink className="w-4 h-4" />
        </a>
        <div className="flex items-center gap-3 px-4 py-2 opacity-50">
           <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
           <span className="text-xs text-slate-400 font-medium tracking-wide">System Online</span>
        </div>
      </div>
    </div>
  );
};

export default SideNav;
