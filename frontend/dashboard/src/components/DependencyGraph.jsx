import React from 'react';
import { GitBranch } from 'lucide-react';

// Layout uses a hub-and-spoke model like Dynatrace
// Each node has: id, label, sublabel, cx, cy (center), type, container
const NODES = [
  { id: 'user',           label: 'Browser',         sublabel: 'External',        cx: 100, cy: 200, r: 38, type: 'external' },
  { id: 'backend',        label: 'AutoSRE',         sublabel: 'Backend :8000',   cx: 300, cy: 200, r: 42, type: 'service',  container: 'autosre-backend' },
  { id: 'faulty-service', label: 'Faulty Svc',      sublabel: 'Service :8080',   cx: 500, cy: 110, r: 40, type: 'service',  container: 'faulty-service' },
  { id: 'prometheus',     label: 'Prometheus',      sublabel: 'Infra :9090',     cx: 500, cy: 290, r: 36, type: 'infra',    container: 'prometheus' },
  { id: 'loki',           label: 'Loki',            sublabel: 'Logs :3100',      cx: 680, cy: 200, r: 34, type: 'infra',    container: 'loki' },
  { id: 'grafana',        label: 'Grafana',         sublabel: 'Dashboards :3000',cx: 680, cy: 330, r: 34, type: 'infra',    container: 'grafana' },
  { id: 'promtail',       label: 'Promtail',        sublabel: 'Log Shipper',     cx: 680, cy: 80,  r: 32, type: 'infra',    container: 'promtail' },
];

const EDGES = [
  { from: 'user',       to: 'backend',        label: 'HTTP' },
  { from: 'backend',    to: 'faulty-service', label: 'health check' },
  { from: 'backend',    to: 'prometheus',     label: 'metrics' },
  { from: 'promtail',   to: 'loki',           label: 'logs' },
  { from: 'prometheus', to: 'grafana',        label: 'query' },
  { from: 'loki',       to: 'grafana',        label: 'query' },
];

const TYPE_STYLES = {
  external: { stroke: '#818cf8', fill: '#1e1b4b', text: '#a5b4fc', glow: '0 0 12px rgba(129,140,248,0.4)' },
  service:  { stroke: '#22d3ee', fill: '#0c1a2e', text: '#67e8f9', glow: '0 0 12px rgba(34,211,238,0.4)' },
  infra:    { stroke: '#475569', fill: '#111827', text: '#94a3b8', glow: 'none' },
};
const ERROR_STYLE = { stroke: '#f43f5e', fill: '#1a0a0e', text: '#fca5a5', glow: '0 0 16px rgba(244,63,94,0.6)' };

function getNodeById(id) { return NODES.find(n => n.id === id); }

function getEdgePoints(from, to) {
  const dx = to.cx - from.cx;
  const dy = to.cy - from.cy;
  const dist = Math.sqrt(dx * dx + dy * dy);
  const ux = dx / dist, uy = dy / dist;
  return {
    x1: from.cx + ux * from.r,
    y1: from.cy + uy * from.r,
    x2: to.cx - ux * to.r,
    y2: to.cy - uy * to.r,
  };
}

export default function DependencyGraph({ incidents }) {
  // Extract all affected containers from incidents — check both incident.target AND incident.intent?.target
  const affectedContainers = incidents
    .filter(i => i.status === 'active' || i.status === 'remediating')
    .flatMap(i => [i.target, i.intent?.target].filter(Boolean));

  const uniqueAffected = [...new Set(affectedContainers)];
  const hasErrors = uniqueAffected.length > 0;

  // Also mark upstream nodes that depend on affected services
  const affectedSet = new Set(uniqueAffected);

  return (
    <div className="glass-card flex flex-col">
      <div className="p-4 border-b border-border bg-card/40 flex items-center justify-between">
        <h3 className="font-semibold text-white flex items-center gap-2">
          <GitBranch className="w-4 h-4 text-indigo-400" /> Service Dependency Map
        </h3>
        <div className="flex items-center gap-3">
          {hasErrors && (
            <span className="flex items-center gap-1.5 text-xs text-rose-400 font-mono animate-pulse">
              <span className="w-2 h-2 rounded-full bg-rose-500 inline-block" />
              {uniqueAffected.length} service(s) affected
            </span>
          )}
          <span className={`text-xs font-mono px-2 py-0.5 rounded-full ${hasErrors ? 'bg-rose-500/20 text-rose-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
            {hasErrors ? 'Degraded' : 'All Healthy'}
          </span>
        </div>
      </div>

      <div className="p-3 overflow-x-auto">
        <svg width="780" height="420" viewBox="0 0 780 420" style={{ minWidth: '600px' }}>
          <defs>
            {/* Arrowhead markers */}
            <marker id="arrow-normal" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
              <path d="M0,0 L0,6 L8,3 z" fill="#334155" />
            </marker>
            <marker id="arrow-error" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
              <path d="M0,0 L0,6 L8,3 z" fill="#f43f5e" />
            </marker>
            {/* Glow filters */}
            <filter id="glow-error" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="4" result="coloredBlur" />
              <feMerge><feMergeNode in="coloredBlur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
            <filter id="glow-service" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="3" result="coloredBlur" />
              <feMerge><feMergeNode in="coloredBlur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
          </defs>

          {/* Edges */}
          {EDGES.map((edge, idx) => {
            const from = getNodeById(edge.from);
            const to = getNodeById(edge.to);
            if (!from || !to) return null;
            const pts = getEdgePoints(from, to);
            const isAffected = affectedSet.has(from.container) || affectedSet.has(to.container);
            const midX = (pts.x1 + pts.x2) / 2;
            const midY = (pts.y1 + pts.y2) / 2;
            return (
              <g key={idx}>
                <line
                  x1={pts.x1} y1={pts.y1} x2={pts.x2} y2={pts.y2}
                  stroke={isAffected ? '#f43f5e' : '#1e293b'}
                  strokeWidth={isAffected ? 2.5 : 1.5}
                  strokeDasharray={isAffected ? '8 4' : undefined}
                  markerEnd={isAffected ? 'url(#arrow-error)' : 'url(#arrow-normal)'}
                />
                {/* Edge label */}
                <text x={midX} y={midY - 5} textAnchor="middle" fill={isAffected ? '#f87171' : '#475569'} fontSize="9" fontFamily="monospace">
                  {edge.label}
                </text>
                {/* Animated pulse on error edges */}
                {isAffected && (
                  <circle r="4" fill="#f43f5e" opacity="0.9">
                    <animateMotion dur="1.2s" repeatCount="indefinite" path={`M${pts.x1},${pts.y1} L${pts.x2},${pts.y2}`} />
                  </circle>
                )}
              </g>
            );
          })}

          {/* Nodes */}
          {NODES.map((node) => {
            const isAffected = affectedSet.has(node.container);
            const style = isAffected ? ERROR_STYLE : TYPE_STYLES[node.type] || TYPE_STYLES.infra;
            return (
              <g key={node.id} filter={isAffected ? 'url(#glow-error)' : node.type === 'service' ? 'url(#glow-service)' : undefined}>
                {/* Outer pulse ring for errors */}
                {isAffected && (
                  <circle cx={node.cx} cy={node.cy} r={node.r + 8} fill="none" stroke="#f43f5e" strokeWidth="1">
                    <animate attributeName="r" values={`${node.r + 4};${node.r + 14};${node.r + 4}`} dur="1.4s" repeatCount="indefinite" />
                    <animate attributeName="opacity" values="0.6;0;0.6" dur="1.4s" repeatCount="indefinite" />
                  </circle>
                )}

                {/* Main circle */}
                <circle
                  cx={node.cx} cy={node.cy} r={node.r}
                  fill={style.fill}
                  stroke={style.stroke}
                  strokeWidth={isAffected ? 2.5 : 1.5}
                />

                {/* Service name */}
                <text cx={node.cx} cy={node.cy - 6} textAnchor="middle" dominantBaseline="middle"
                  x={node.cx} y={node.cy - 6}
                  fill={style.text} fontSize="11" fontWeight="700" fontFamily="system-ui">
                  {node.label}
                </text>

                {/* Sub-label */}
                <text x={node.cx} y={node.cy + 10}
                  textAnchor="middle" fill={isAffected ? '#f87171' : '#64748b'}
                  fontSize="9" fontFamily="monospace">
                  {isAffected ? '⚠ ERROR' : node.sublabel}
                </text>

                {/* Status dot */}
                <circle
                  cx={node.cx + node.r - 7} cy={node.cy - node.r + 7} r="6"
                  fill={isAffected ? '#f43f5e' : '#22c55e'}
                  stroke={style.fill} strokeWidth="1.5"
                />
              </g>
            );
          })}

          {/* Legend */}
          <g transform="translate(16, 390)">
            <circle cx="8" cy="6" r="5" fill="#0c1a2e" stroke="#22d3ee" strokeWidth="1.5" />
            <text x="18" y="10" fill="#64748b" fontSize="9">Service</text>
            <circle cx="68" cy="6" r="5" fill="#111827" stroke="#475569" strokeWidth="1.5" />
            <text x="78" y="10" fill="#64748b" fontSize="9">Infra</text>
            <circle cx="115" cy="6" r="5" fill="#1a0a0e" stroke="#f43f5e" strokeWidth="1.5" />
            <text x="125" y="10" fill="#64748b" fontSize="9">Error</text>
            <circle cx="156" cy="6" r="4" fill="#22c55e" stroke="#111" strokeWidth="1" />
            <text x="166" y="10" fill="#64748b" fontSize="9">Healthy</text>
            <circle cx="204" cy="6" r="4" fill="#f43f5e" stroke="#111" strokeWidth="1" />
            <text x="214" y="10" fill="#64748b" fontSize="9">Degraded</text>
          </g>
        </svg>
      </div>
    </div>
  );
}
