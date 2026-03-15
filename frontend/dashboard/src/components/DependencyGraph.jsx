import React, { useState, useEffect } from 'react';
import { GitBranch, RefreshCw } from 'lucide-react';

// Dynamic Layout Styles
const TYPE_STYLES = {
  external: { stroke: '#818cf8', fill: '#1e1b4b', text: '#a5b4fc', glow: '0 0 12px rgba(129,140,248,0.4)' },
  service:  { stroke: '#22d3ee', fill: '#0c1a2e', text: '#67e8f9', glow: '0 0 12px rgba(34,211,238,0.4)' },
  infra:    { stroke: '#475569', fill: '#111827', text: '#94a3b8', glow: 'none' },
};
const ERROR_STYLE = { stroke: '#f43f5e', fill: '#1a0a0e', text: '#fca5a5', glow: '0 0 16px rgba(244,63,94,0.6)' };

export default function DependencyGraph({ incidents }) {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [hoveredNode, setHoveredNode] = useState(null);

  const fetchTopology = async () => {
    setLoading(true);
    try {
      const resp = await fetch('http://localhost:8000/topology');
      const data = await resp.json();
      setNodes(data.nodes || []);
      setEdges(data.edges || []);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchTopology();
    const interval = setInterval(fetchTopology, 30000);
    return () => clearInterval(interval);
  }, []);

  function getNodeById(id) { return nodes.find(n => n.id === id); }
  
  const affectedContainers = incidents
    .filter(i => i.status === 'active' || i.status === 'remediating')
    .flatMap(i => [i.target, i.intent?.target].filter(Boolean));

  const uniqueAffected = [...new Set(affectedContainers)];
  const hasErrors = uniqueAffected.length > 0;
  const affectedSet = new Set(uniqueAffected);

  // Helper for smooth Bezier curves
  const getPathData = (from, to) => {
    const dx = to.cx - from.cx;
    const curvature = Math.abs(dx) * 0.4;
    return `M ${from.cx} ${from.cy} C ${from.cx + curvature} ${from.cy}, ${to.cx - curvature} ${to.cy}, ${to.cx} ${to.cy}`;
  };

  const isConnected = (nodeId) => {
    if (!hoveredNode) return true;
    if (nodeId === hoveredNode) return true;
    return edges.some(e => 
      (e.from === hoveredNode && e.to === nodeId) || 
      (e.to === hoveredNode && e.from === nodeId)
    );
  };

  const isEdgeHighlighted = (edge) => {
    if (!hoveredNode) return true;
    return edge.from === hoveredNode || edge.to === hoveredNode;
  };

  return (
    <div className="glass-card flex flex-col h-full">
      <div className="p-4 border-b border-border bg-card/40 flex items-center justify-between">
        <h3 className="font-semibold text-white flex items-center gap-2">
          <GitBranch className="w-4 h-4 text-indigo-400" /> Infrastructure Topology
        </h3>
        <div className="flex items-center gap-4">
          <button onClick={fetchTopology} className="p-1.5 hover:bg-slate-800 rounded-lg transition-all" title="Refresh Map">
            <RefreshCw className={`w-4 h-4 text-slate-400 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <span className={`text-[10px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full ${hasErrors ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'}`}>
            {hasErrors ? 'Degraded Flow' : 'Optimal Sync'}
          </span>
        </div>
      </div>

      <div className="flex-1 p-4 flex items-center justify-center bg-[#020617]/40 relative overflow-hidden group">
        <div className="absolute inset-0 opacity-[0.03] pointer-events-none" 
             style={{ backgroundImage: 'radial-gradient(circle, #818cf8 1px, transparent 1px)', backgroundSize: '30px 30px' }} />

        <svg width="100%" height="400" viewBox="0 0 780 400" className="drop-shadow-2xl">
          <defs>
            <marker id="arrow-normal" markerWidth="8" markerHeight="8" refX="28" refY="4" orient="auto">
              <path d="M0,0 L0,8 L8,4 z" fill="#475569" />
            </marker>
            <marker id="arrow-active" markerWidth="8" markerHeight="8" refX="28" refY="4" orient="auto">
              <path d="M0,0 L0,8 L8,4 z" fill="#818cf8" />
            </marker>
            <marker id="arrow-error" markerWidth="8" markerHeight="8" refX="28" refY="4" orient="auto">
              <path d="M0,0 L0,8 L8,4 z" fill="#f43f5e" />
            </marker>
            
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Edges Layer */}
          {edges.map((edge, idx) => {
            const from = getNodeById(edge.from);
            const to = getNodeById(edge.to);
            if (!from || !to) return null;
            
            const isAffected = affectedSet.has(from.container) || affectedSet.has(to.container);
            const isHigh = isEdgeHighlighted(edge);
            const pathData = getPathData(from, to);
            
            return (
              <g key={`edge-${idx}`} className="transition-opacity duration-300" opacity={isHigh ? 1 : 0.15}>
                <path
                  d={pathData}
                  fill="none"
                  stroke={isAffected ? '#f43f5e' : isHigh && hoveredNode ? '#818cf8' : '#334155'}
                  strokeWidth={isAffected ? 3 : 1.5}
                  strokeDasharray={isAffected ? "none" : "4,4"} // Dotted for healthy/clean collection
                  markerEnd={isAffected ? 'url(#arrow-error)' : isHigh && hoveredNode ? 'url(#arrow-active)' : 'url(#arrow-normal)'}
                  className={!isAffected ? "animate-flow" : ""}
                />
                
                {/* Edge Label Pill */}
                <g transform={`translate(${(from.cx + to.cx)/2}, ${(from.cy + to.cy)/2})`}>
                  <rect 
                    x={-(edge.label.length * 4 + 8)} 
                    y="-10" 
                    width={edge.label.length * 8 + 16} 
                    height="20" 
                    rx="10" 
                    className={`${isAffected ? 'fill-rose-950 stroke-rose-500' : 'fill-[#020617] stroke-slate-700'} border`}
                  />
                  <text 
                    textAnchor="middle" 
                    dominantBaseline="middle" 
                    className={`text-[9px] font-bold uppercase tracking-wider ${isAffected ? 'fill-rose-300' : 'fill-slate-400'}`}
                  >
                    {edge.label}
                  </text>
                </g>
              </g>
            );
          })}

          {/* Nodes Layer */}
          {nodes.map((node) => {
            const isAffected = affectedSet.has(node.container);
            const isHigh = isConnected(node.id);
            
            return (
              <g 
                key={node.id} 
                className="cursor-pointer transition-all duration-300"
                opacity={isHigh ? 1 : 0.2}
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
              >
                {node.type === 'infra' ? (
                  <rect
                    x={node.cx - node.r} y={node.cy - node.r}
                    width={node.r * 2} height={node.r * 2}
                    rx="12"
                    className={`${isAffected ? 'fill-rose-950 stroke-rose-500' : 'fill-slate-900 stroke-slate-700'} transition-colors duration-500`}
                    strokeWidth={isHigh ? 2 : 1}
                  />
                ) : (
                  <circle
                    cx={node.cx} cy={node.cy} r={node.r}
                    className={`${isAffected ? 'fill-rose-950 stroke-rose-500 stroke-[3px]' : 'fill-[#0c1a2e] stroke-[#22d3ee]'} transition-all`}
                    style={{ filter: isAffected || (isHigh && hoveredNode) ? 'url(#glow)' : 'none' }}
                  />
                )}

                <text x={node.cx} y={node.cy - 2} textAnchor="middle" className={`text-xs font-bold ${isAffected ? 'fill-rose-200' : 'fill-white'}`}>
                  {node.label}
                </text>
                <text x={node.cx} y={node.cy + 14} textAnchor="middle" className={`text-[9px] font-mono ${isAffected ? 'fill-rose-400' : 'fill-slate-500'}`}>
                  {isAffected ? 'CRITICAL' : node.sublabel}
                </text>

                <circle 
                  cx={node.cx + node.r - 8} cy={node.cy - node.r + 8} r="5" 
                  className={isAffected ? 'fill-rose-500 animate-pulse' : 'fill-emerald-500'} 
                />
              </g>
            );
          })}
        </svg>

        <div className="absolute bottom-4 left-4 flex gap-4 bg-[#020617]/80 backdrop-blur-md p-3 rounded-xl border border-border/50 text-[10px] font-medium text-slate-500">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full border border-[#22d3ee] bg-[#0c1a2e]" /> Service
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-lg border border-slate-700 bg-slate-900" /> Infra
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-rose-500" /> Error
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes flow {
          from { stroke-dashoffset: 20; }
          to { stroke-dashoffset: 0; }
        }
        .animate-flow {
          animation: flow 1.5s linear infinite;
        }
      `}</style>
    </div>
  );
}
