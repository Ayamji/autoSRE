import React, { useState, useEffect } from 'react';
import { Activity, ShieldAlert, CheckCircle2, ServerCrash, Terminal } from 'lucide-react';
import IncidentTable from './components/IncidentTable';
import MetricCards from './components/MetricCards';
import Timeline from './components/Timeline';
import RemediationPanel from './components/RemediationPanel';

function App() {
  const [incidents, setIncidents] = useState([]);
  const [metrics, setMetrics] = useState({ cpu: 0, mem: 0, running: 0, total: 1 });
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [events, setEvents] = useState([]);

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
          addEvent(`Detected new incident(s)`, 'error');
        } else if (data.event === 'incident_update') {
          fetchIncidents();
          addEvent(`Incident ${data.payload.id} status changed to ${data.payload.status}`, 'info');
        }
      } catch (err) {
        console.error(err);
      }
    };
    
    // Fallback polling for metrics just in case we don't scrape directly in React
    // In a real app Grafana handles the metrics, but we want some eye candy here too
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
      
      // Update selected incident if it exists
      if (selectedIncident) {
        const updated = data.incidents.find(i => i.id === selectedIncident.id);
        if (updated) setSelectedIncident(updated);
      }
    } catch (e) {
      console.error("Failed to fetch incidents", e);
    }
  };

  const addEvent = (msg, type='info') => {
    setEvents(prev => [{ time: new Date().toLocaleTimeString(), msg, type }, ...prev].slice(0, 50));
  };

  const handleRemediate = async (incidentId) => {
    addEvent(`Triggering AI remediation for ${incidentId}...`, 'warning');
    try {
      const res = await fetch('http://localhost:8000/remediate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ incident_id: incidentId })
      });
      const data = await res.json();
      if (data.status === 'success') {
        addEvent(`Remediation successful: ${data.result.output}`, 'success');
      } else {
        addEvent(`Remediation failed: ${data.result?.output || data.message}`, 'error');
      }
    } catch (e) {
      addEvent(`Failed to call remediation API: ${e.message}`, 'error');
    }
  };

  const triggerAnalysis = async () => {
    addEvent("Forcing log analysis run...", "info");
    try {
      const res = await fetch('http://localhost:8000/analyze');
      const data = await res.json();
      if (data.new_incidents && data.new_incidents.length > 0) {
        addEvent(`Analysis complete: Found ${data.new_incidents.length} new incidents.`, 'error');
      } else {
        addEvent("Analysis complete: System healthy.", 'success');
      }
      setIncidents(data.all_active || []);
    } catch (e) {
      addEvent(`Analysis failed: ${e.message}`, 'error');
    }
  };

  return (
    <div className="min-h-screen p-6 font-sans">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <header className="flex items-center justify-between glass-card p-4">
          <div className="flex items-center gap-3">
            <div className="bg-indigo-500/20 p-2 rounded-lg">
              <Activity className="w-6 h-6 text-indigo-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white tracking-wide">AutoSRE</h1>
              <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">AI Site Reliability Engineer</p>
            </div>
          </div>
          <div className="flex gap-4 items-center">
            <a href="http://localhost:3000" target="_blank" rel="noreferrer" className="text-sm text-slate-400 hover:text-indigo-400 transition-colors flex items-center gap-2">
              <Activity className="w-4 h-4" /> Grafana Metrics
            </a>
            <button onClick={triggerAnalysis} className="btn-outline flex items-center gap-2 text-sm">
              <Terminal className="w-4 h-4" /> Run AI Analysis
            </button>
          </div>
        </header>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          
          {/* Main Left Column */}
          <div className="lg:col-span-3 space-y-6">
            <MetricCards metrics={metrics} incidentCount={incidents.length} />
            
            <div className="glass-card flex flex-col min-h-[400px]">
              <div className="border-b border-border p-4 flex justify-between items-center bg-card/40">
                <h2 className="text-lg font-semibold flex items-center gap-2 text-white">
                  <ShieldAlert className="w-5 h-5 text-rose-400" /> Active Incidents
                </h2>
                <div className="flex items-center gap-2 text-sm">
                  <span className="relative flex h-3 w-3">
                    {incidents.length > 0 && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>}
                    <span className={`relative inline-flex rounded-full h-3 w-3 ${incidents.length > 0 ? 'bg-rose-500' : 'bg-green-500'}`}></span>
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

          {/* Right Sidebar */}
          <div className="space-y-6">
            <RemediationPanel 
              incident={selectedIncident} 
              onRemediate={handleRemediate} 
            />
            <Timeline events={events} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
