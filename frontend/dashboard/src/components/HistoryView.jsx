import React, { useState, useEffect } from 'react';
import { History, Search, Download, ExternalLink, ShieldAlert, CheckCircle2, XCircle, Clock } from 'lucide-react';

const HistoryView = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const resp = await fetch('http://localhost:8000/history');
      const data = await resp.json();
      setHistory(data.history || []);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      recovered: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
      failed: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
      active: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
      remediating: 'bg-amber-500/10 text-amber-400 border-amber-500/20 animate-pulse',
    };
    return (
      <span className={`px-2.5 py-1 rounded-full text-xs font-bold border ${styles[status] || 'bg-slate-500/10 text-slate-400 border-slate-500/20'}`}>
        {status.toUpperCase()}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <History className="w-8 h-8 text-indigo-500" /> Incident Repository
          </h2>
          <p className="text-slate-400 mt-1">Audit log of all AI-detected and remediated system incidents.</p>
        </div>
        <button onClick={fetchHistory} className="btn-outline text-sm">Refresh Logs</button>
      </div>

      <div className="glass-card overflow-hidden">
        <div className="p-4 border-b border-slate-800/50 flex items-center gap-4 bg-slate-900/50">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input 
              type="text" 
              placeholder="Filter incidents by type or cause..." 
              className="bg-slate-800/50 border border-slate-700/50 rounded-lg pl-10 pr-4 py-2 w-full text-sm focus:outline-none focus:border-indigo-500/50 transition-colors"
            />
          </div>
          <select className="bg-slate-800/50 border border-slate-700/50 rounded-lg px-3 py-2 text-sm text-slate-300">
            <option>All Severities</option>
            <option>High</option>
            <option>Medium</option>
          </select>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-slate-800/50 text-slate-500 text-xs font-bold uppercase tracking-widest">
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Incident Type</th>
                <th className="px-6 py-4">Timestamp</th>
                <th className="px-6 py-4">Root Cause</th>
                <th className="px-6 py-4">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {loading ? (
                <tr><td colSpan="5" className="px-6 py-12 text-center text-slate-500">Loading history...</td></tr>
              ) : history.length === 0 ? (
                <tr><td colSpan="5" className="px-6 py-12 text-center text-slate-500">No incident history found in persistence layer.</td></tr>
              ) : history.map((inc) => (
                <tr key={inc.id} className="hover:bg-slate-800/20 transition-colors group">
                  <td className="px-6 py-5 whitespace-nowrap">
                    {getStatusBadge(inc.status)}
                  </td>
                  <td className="px-6 py-5">
                    <div className="text-sm font-bold text-slate-200">{inc.type}</div>
                    <div className="text-[10px] text-slate-500 font-mono mt-1">{inc.id}</div>
                  </td>
                  <td className="px-6 py-5 text-sm text-slate-400 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <Clock className="w-3.5 h-3.5" />
                      {new Date(inc.timestamp).toLocaleString()}
                    </div>
                  </td>
                  <td className="px-6 py-5">
                    <div className="text-sm text-slate-400 line-clamp-1 max-w-xs">{inc.root_cause}</div>
                  </td>
                  <td className="px-6 py-5">
                    <div className="flex items-center gap-3">
                       <a href={`http://localhost:8000/report/${inc.id}?format=pdf`} target="_blank" rel="noreferrer" className="text-slate-500 hover:text-indigo-400 transition-colors tooltip" title="Download Audit PDF">
                         <Download className="w-5 h-5" />
                       </a>
                       <button className="text-slate-500 hover:text-slate-200 transition-colors">
                         <ExternalLink className="w-5 h-5" />
                       </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default HistoryView;
