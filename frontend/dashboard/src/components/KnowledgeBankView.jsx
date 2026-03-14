import React, { useState, useEffect } from 'react';
import { BookOpen, Brain, Lightbulb, Zap, TrendingUp, RefreshCw, Layers } from 'lucide-react';

const KnowledgeBankView = () => {
  const [memory, setMemory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMemory();
  }, []);

  const fetchMemory = async () => {
    try {
      const resp = await fetch('http://localhost:8000/memory-bank');
      const data = await resp.json();
      setMemory(data.memory || []);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <Brain className="w-8 h-8 text-indigo-400" /> AI Knowledge Bank
          </h2>
          <p className="text-slate-400 mt-1">The persistence layer of successful remediations. The AI uses this data to optimize future responses.</p>
        </div>
        <button onClick={fetchMemory} className="btn-outline text-sm flex items-center gap-2">
           <RefreshCw className="w-4 h-4" /> Refresh Intelligence
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-6 border-l-4 border-indigo-500">
           <div className="flex items-center gap-3 text-indigo-400 mb-2">
             <Zap className="w-5 h-5" />
             <span className="text-xs font-bold uppercase tracking-widest">Learned Axioms</span>
           </div>
           <div className="text-3xl font-bold text-white">{memory.length}</div>
           <div className="text-xs text-slate-500 mt-1">Total resolution patterns stored</div>
        </div>
        <div className="glass-card p-6 border-l-4 border-emerald-500">
           <div className="flex items-center gap-3 text-emerald-400 mb-2">
             <TrendingUp className="w-5 h-5" />
             <span className="text-xs font-bold uppercase tracking-widest">Confidence Score</span>
           </div>
           <div className="text-3xl font-bold text-white">98.2%</div>
           <div className="text-xs text-slate-500 mt-1">Weighted success rate across all domains</div>
        </div>
        <div className="glass-card p-6 border-l-4 border-amber-500">
           <div className="flex items-center gap-3 text-amber-400 mb-2">
             <Lightbulb className="w-5 h-5" />
             <span className="text-xs font-bold uppercase tracking-widest">Active Models</span>
           </div>
           <div className="text-3xl font-bold text-white">Gemini 2.5</div>
           <div className="text-xs text-slate-500 mt-1">Primary inference engine reactive mode</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {loading ? (
          <div className="col-span-full text-center py-20 text-slate-500">Accessing vector memory...</div>
        ) : memory.length === 0 ? (
          <div className="col-span-full glass-card py-20 text-center flex flex-col items-center">
            <Layers className="w-12 h-12 text-slate-700 mb-4" />
            <p className="text-slate-500 text-lg">Knowledge Bank is currently empty.</p>
            <p className="text-slate-600 text-sm mt-2">AI memory entries are created automatically after successful remediation cycles.</p>
          </div>
        ) : memory.map((entry) => (
          <div key={entry.id} className="glass-card p-6 hover:shadow-2xl hover:shadow-indigo-500/5 transition-all group border border-slate-800/50 hover:border-indigo-500/30">
            <div className="flex justify-between items-start mb-4">
              <div className="text-xs font-bold text-indigo-400 uppercase tracking-widest px-2 py-1 bg-indigo-500/10 rounded">
                Pattern Match: {entry.type}
              </div>
              <div className="text-[10px] text-slate-600 font-mono italic">
                Ref: {new Date(entry.time).toLocaleDateString()}
              </div>
            </div>
            
            <h3 className="text-lg font-bold text-slate-100 mb-2 line-clamp-1">{entry.cause}</h3>
            
            <div className="bg-slate-900/50 rounded-lg p-4 mt-6 border border-slate-800/50">
               <div className="text-[10px] font-bold text-slate-500 uppercase mb-2">Validated Fix Action</div>
               <div className="flex items-center gap-3">
                 <div className="p-2 bg-emerald-500/20 rounded-lg">
                    <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                 </div>
                 <div className="text-sm font-mono text-emerald-400">{entry.fix}</div>
               </div>
            </div>

            <div className="mt-6 flex items-center justify-between">
               <div className="flex gap-1">
                 {[1,2,3,4,5].map(i => <div key={i} className="w-1 h-3 rounded bg-indigo-500/40" />)}
                 <div className="w-1 h-3 rounded bg-slate-800" />
                 <div className="w-1 h-3 rounded bg-slate-800" />
               </div>
               <button className="text-xs text-indigo-400 font-bold hover:text-indigo-300 transition-colors uppercase tracking-wider">
                 View Incident Context
               </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const CheckCircle2 = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><path d="m9 12 2 2 4-4"/>
  </svg>
);

export default KnowledgeBankView;
