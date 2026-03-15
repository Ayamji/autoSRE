import React, { useState, useEffect } from 'react';
import { Activity, ShieldAlert, Terminal, MessageSquare } from 'lucide-react';
import IncidentTable from './components/IncidentTable';
import MetricCards from './components/MetricCards';
import Timeline from './components/Timeline';
import RemediationPanel from './components/RemediationPanel';
import DependencyGraph from './components/DependencyGraph';
import AIAnalysisPanel from './components/AIAnalysisPanel';
import IncidentTimeline from './components/IncidentTimeline';
import SideNav from './components/SideNav';
import HistoryView from './components/HistoryView';
import KnowledgeBankView from './components/KnowledgeBankView';
import ErrorBoundary from './components/ErrorBoundary';

function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [incidents, setIncidents] = useState([]);
  const [metrics, setMetrics] = useState({ cpu: 0, mem: 0, running: 0, total: 1 });
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [events, setEvents] = useState([]);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    // Initial fetch
    fetchIncidents();

    // Connect to websocket
    const ws = new WebSocket('ws://localhost:8000/ws/events');
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.event === 'new_incident') {
          fetchIncidents();
          addEvent(`AI detected: ${data.payload.type || 'new incident'}`, 'error');
          setSelectedIncident(data.payload);
          setAnalyzing(false);
          // If not in dashboard, maybe show a toast or notification? 
          // For now just keep it simple.
        } else if (data.event === 'incident_update') {
          fetchIncidents();
          addEvent(`Incident ${data.payload.id} status changed to ${data.payload.status}`, 'info');
          if (data.payload.status === 'recovered') {
            addEvent(`✓ Service recovered successfully`, 'success');
          }
        } else if (data.event === 'system_recovered') {
          fetchIncidents();
          addEvent('✓ All systems recovered. AI agent returning to monitoring.', 'success');
          setTimeout(() => {
            setSelectedIncident(null);
            setAnalyzing(false);
          }, 5000);
        }
      } catch (err) {
        console.error(err);
      }
    };

    const metricInterval = setInterval(async () => {
      try {
        const res = await fetch('http://localhost:8000/metrics');
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();
        setMetrics({
          cpu: data.cpu !== undefined ? data.cpu : 0,
          mem: data.mem !== undefined ? data.mem : 0,
          running: data.running_containers !== undefined ? data.running_containers : 0,
          total: data.total_containers !== undefined ? data.total_containers : 1
        });
      } catch (err) {
        console.error("Failed to fetch metrics", err);
      }
    }, 5000);

    return () => {
      ws.close();
      clearInterval(metricInterval);
    };
  }, []);

  const fetchIncidents = async () => {
    try {
      const res = await fetch('http://localhost:8000/incidents');
      const data = await res.json();
      setIncidents(data.incidents || []);

      if (selectedIncident) {
        const updated = (data.incidents || []).find(i => i.id === selectedIncident.id);
        if (updated) setSelectedIncident(updated);
      }
    } catch (e) {
      console.error("Failed to fetch incidents", e);
    }
  };

  const addEvent = (msg, type = 'info') => {
    setEvents(prev => [{ time: new Date().toLocaleTimeString(), msg, type }, ...prev].slice(0, 50));
  };

  const handleRemediate = async (incidentId, approved = true) => {
    addEvent(`Triggering AI remediation for ${incidentId}...`, 'warning');
    try {
      const res = await fetch('http://localhost:8000/remediate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ incident_id: incidentId, approved })
      });
      const data = await res.json();
      if (data.status === 'success') {
        addEvent(`✅ Remediation successful: ${data.result?.output || 'Fix applied.'}`, 'success');
        fetchIncidents();
      } else if (data.status === 'skipped') {
        addEvent(`⏭ Remediation skipped: ${data.message}`, 'info');
      } else {
        addEvent(`❌ Remediation failed: ${data.result?.output || data.message}`, 'error');
      }
    } catch (e) {
      addEvent(`Failed to call remediation API: ${e.message}`, 'error');
    }
  };


  const triggerAnalysis = async () => {
    addEvent("AI agent starting analysis...", "info");
    setAnalyzing(true);
    try {
      const res = await fetch('http://localhost:8000/ai-analyze');
      const data = await res.json();
      setAnalyzing(false);
      if (data.incident) {
        addEvent(`AI found: ${data.incident.type} (${data.incident.severity})`, 'error');
        setSelectedIncident(data.incident);
        if (currentView !== 'dashboard') setCurrentView('dashboard');
      } else {
        addEvent("Analysis complete: All systems healthy.", 'success');
      }
      if (data.all_active) setIncidents(data.all_active);
    } catch (e) {
      setAnalyzing(false);
      addEvent(`Analysis failed: ${e.message}`, 'error');
    }
  };

  const renderView = () => {
    switch (currentView) {
      case 'history':
        return <HistoryView />;
      case 'memory':
        return <KnowledgeBankView />;
      default:
        return (
          <div className="space-y-6">
            {/* Top row: Metrics */}
            <MetricCards metrics={metrics} incidentCount={incidents.length} />

            {/* Main area: Dependency Graph + AI Analysis Panel */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              <div className="lg:col-span-3">
                <DependencyGraph incidents={incidents} />
              </div>
              <div>
                <AIAnalysisPanel analyzing={analyzing} incident={selectedIncident} />
              </div>
            </div>

            {/* Incident Causal Chain */}
            {selectedIncident && <IncidentTimeline incident={selectedIncident} />}

            {/* Active Incidents Table + Remediation Panel */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              <div className="lg:col-span-3">
                <div className="glass-card flex flex-col min-h-[360px]">
                  <div className="border-b border-border p-4 flex justify-between items-center bg-card/40">
                    <h2 className="text-lg font-semibold flex items-center gap-2 text-white">
                      <ShieldAlert className="w-5 h-5 text-rose-400" /> Active Incidents
                    </h2>
                    <div className="flex items-center gap-2 text-sm">
                      <span className="relative flex h-3 w-3">
                        {incidents.length > 0 && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75" />}
                        <span className={`relative inline-flex rounded-full h-3 w-3 ${incidents.length > 0 ? 'bg-rose-500' : 'bg-green-500'}`} />
                      </span>
                      <span className="text-slate-300">{incidents.length > 0 ? 'System Degraded' : 'System Healthy'}</span>
                    </div>
                  </div>
                  <div className="p-0 flex-1">
                    <IncidentTable
                      incidents={incidents}
                      selected={selectedIncident}
                      onSelect={setSelectedIncident}
                      onRemediate={handleRemediate}
                    />
                  </div>
                </div>
              </div>
              <div>
                <RemediationPanel incident={selectedIncident} onRemediate={handleRemediate} />
              </div>
            </div>

            {/* Event Stream */}
            <Timeline events={events} />
          </div>
        );
    }
  };

  return (
    <ErrorBoundary>
      <div className="flex min-h-screen bg-[#020617]">
        {/* Sidebar Navigation */}
        <SideNav activeView={currentView} onViewChange={setCurrentView} />

        {/* Main Content Area */}
        <main className="flex-1 ml-64 p-8 overflow-y-auto">
          <div className="max-w-7xl mx-auto space-y-6">

            {/* Top Navbar */}
            <div className="flex items-center justify-between mb-8">
              <div>
                <h2 className="text-sm font-bold text-slate-500 uppercase tracking-widest">{currentView}</h2>
                <div className="h-1 w-12 bg-indigo-500 mt-1 rounded-full"></div>
              </div>

              <div className="flex gap-4 items-center">
                <button
                  onClick={triggerAnalysis}
                  disabled={analyzing}
                  className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-sm transition-all ${analyzing
                      ? 'bg-indigo-500/20 text-indigo-400 cursor-not-allowed'
                      : 'bg-indigo-600 text-white hover:bg-indigo-500 shadow-lg shadow-indigo-500/20 active:scale-95'
                    }`}
                >
                  <Terminal className="w-4 h-4" /> {analyzing ? 'AI Analysis in Progress...' : 'Manually Trigger AI Audit'}
                </button>
                <div className="p-2.5 glass-card text-slate-400 hover:text-white transition-colors cursor-pointer">
                  <MessageSquare className="w-5 h-5" />
                </div>
              </div>
            </div>

            {/* View Content */}
            {renderView()}

          </div>
        </main>
      </div>
    </ErrorBoundary>
  );
}

export default App;
