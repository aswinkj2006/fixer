import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import axios from 'axios';

import type { Machine, SensorDataPoint } from './types';
import { Navbar } from './components/Navbar';
import { Dashboard } from './pages/Dashboard';
import { MachineDetail } from './pages/MachineDetail';

export function App() {
  const [machines, setMachines] = useState<Machine[]>([]);
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [isTriggerModalOpen, setIsTriggerModalOpen] = useState<boolean>(false);
  const [realtimePoints, setRealtimePoints] = useState<Record<string, SensorDataPoint[]>>({});
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    return (localStorage.getItem('fixer_theme') as 'light' | 'dark') || 'dark';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('fixer_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const fetchMachines = async () => {
    try {
      const res = await axios.get('/api/machines');
      setMachines(res.data || []);
    } catch (e) {
      console.warn('Could not fetch machines list:', e);
    }
  };

  useEffect(() => {
    fetchMachines();
    const timer = setInterval(fetchMachines, 4000);
    return () => clearInterval(timer);
  }, []);

  // Set up WebSocket connections for all 4 machines
  useEffect(() => {
    const wsSockets: WebSocket[] = [];
    const machineIds = ['M-01', 'M-02', 'M-03', 'M-04'];

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.port === '5173' ? 'localhost:8000' : window.location.host;

    machineIds.forEach((mid) => {
      try {
        const ws = new WebSocket(`${wsProtocol}//${wsHost}/ws/sensors/${mid}`);

        ws.onopen = () => {
          setWsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.readings && data.machine_id) {
              const point: SensorDataPoint = {
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
                timestamp: Date.now(),
                ...data.readings,
              };

              setRealtimePoints((prev) => {
                const existing = prev[data.machine_id] || [];
                const updated = [...existing, point].slice(-35); // Keep last 35 points
                return { ...prev, [data.machine_id]: updated };
              });

              // Update machine instantaneous current_readings
              setMachines((prev) =>
                prev.map((m) => (m.machine_id === data.machine_id ? { ...m, current_readings: data.readings } : m))
              );
            }
          } catch (err) {
            // keepalive or non-json message
          }
        };

        ws.onclose = () => {
          setWsConnected(false);
        };

        wsSockets.push(ws);
      } catch (err) {
        console.warn(`WebSocket connection failed for ${mid}:`, err);
      }
    });

    return () => {
      wsSockets.forEach((s) => s.close());
    };
  }, []);

  const activeTriggerCount = machines.filter((m) => m.trigger_active).length;

  return (
    <BrowserRouter>
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <Navbar
          wsConnected={wsConnected}
          onOpenTriggerModal={() => setIsTriggerModalOpen(true)}
          activeTriggerCount={activeTriggerCount}
          theme={theme}
          onToggleTheme={toggleTheme}
        />

        <div style={{ flex: 1 }}>
          <Routes>
            <Route
              path="/"
              element={
                <Dashboard
                  machines={machines}
                  onRefresh={fetchMachines}
                  isModalOpen={isTriggerModalOpen}
                  onCloseModal={() => setIsTriggerModalOpen(false)}
                />
              }
            />
            <Route
              path="/machine/:id"
              element={<MachineDetail realtimePoints={realtimePoints} />}
            />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
