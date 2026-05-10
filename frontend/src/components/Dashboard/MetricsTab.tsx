import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Activity, Server, Database, Clock, Cpu, RefreshCcw } from 'lucide-react';
import { api } from '@/lib/api';
import { GlassPanel } from './GlassPanel';
import type { MetricsResponse, HealthResponse } from '@/lib/types';

export function MetricsTab() {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchStats = async () => {
    setIsLoading(true);
    try {
      const [metricsData, healthData] = await Promise.all([
        api.getMetrics(),
        api.getHealth()
      ]);
      setMetrics(metricsData);
      setHealth(healthData);
    } catch (error) {
      console.error('Failed to fetch system stats', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    // Auto refresh every 30s
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const StatCard = ({ title, value, icon: Icon, delay = 0, suffix = '' }: any) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
    >
      <GlassPanel className="flex flex-col h-full border-t-4 border-t-blue-500">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-gray-400 font-medium">{title}</h3>
          <div className="p-2 bg-blue-500/10 rounded-lg">
            <Icon className="w-5 h-5 text-blue-400" />
          </div>
        </div>
        <div className="flex items-baseline gap-2 mt-auto">
          <span className="text-3xl font-bold text-white">{value}</span>
          <span className="text-sm text-gray-500">{suffix}</span>
        </div>
      </GlassPanel>
    </motion.div>
  );

  return (
    <div className="flex flex-col h-full max-w-6xl mx-auto space-y-6">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h2 className="text-3xl font-bold mb-2">System Metrics</h2>
          <p className="text-gray-400">Real-time health and performance monitoring.</p>
        </div>
        <button 
          onClick={fetchStats}
          className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg border border-white/10 transition-colors"
        >
          <RefreshCcw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Total Requests" 
          value={metrics?.performance.total_requests || 0} 
          icon={Activity} 
          delay={0.1} 
        />
        <StatCard 
          title="Extraction Requests" 
          value={metrics?.performance.extraction_count || 0} 
          icon={Server} 
          delay={0.2} 
        />
        <StatCard 
          title="Verify Requests" 
          value={metrics?.performance.verification_count || 0} 
          icon={ShieldCheck} 
          delay={0.3} 
        />
        <StatCard 
          title="Errors" 
          value={metrics?.performance.errors_total || 0} 
          icon={Activity} 
          delay={0.4} 
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        {/* Services Health */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
        >
          <GlassPanel className="h-full">
            <div className="flex items-center gap-2 mb-6">
              <Server className="w-5 h-5 text-blue-400" />
              <h3 className="text-xl font-semibold">Service Status</h3>
            </div>
            
            <div className="space-y-4">
              <div className="flex justify-between items-center p-4 bg-black/20 rounded-xl border border-white/5">
                <div className="flex items-center gap-3">
                  <Cpu className="w-5 h-5 text-gray-400" />
                  <span>Primary LLM</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-mono text-gray-400">{health?.primary_llm}</span>
                  <div className={`w-2 h-2 rounded-full ${health?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'}`} />
                </div>
              </div>

              <div className="flex justify-between items-center p-4 bg-black/20 rounded-xl border border-white/5">
                <div className="flex items-center gap-3">
                  <Database className="w-5 h-5 text-gray-400" />
                  <span>Vector Database</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-mono text-gray-400">{health?.services.vector_store || 'unknown'}</span>
                  <div className={`w-2 h-2 rounded-full ${health?.services.vector_store !== 'error' ? 'bg-green-500' : 'bg-red-500'}`} />
                </div>
              </div>

              <div className="flex justify-between items-center p-4 bg-black/20 rounded-xl border border-white/5">
                <div className="flex items-center gap-3">
                  <Database className="w-5 h-5 text-gray-400" />
                  <span>Graph Database</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-mono text-gray-400">{health?.services.graph_store || 'unknown'}</span>
                  <div className={`w-2 h-2 rounded-full ${health?.services.graph_store !== 'error' ? 'bg-green-500' : 'bg-red-500'}`} />
                </div>
              </div>
            </div>
          </GlassPanel>
        </motion.div>

        {/* System Info */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.6 }}
        >
          <GlassPanel className="h-full">
            <div className="flex items-center gap-2 mb-6">
              <Clock className="w-5 h-5 text-blue-400" />
              <h3 className="text-xl font-semibold">System Info</h3>
            </div>
            
            <div className="space-y-6">
              <div>
                <p className="text-sm text-gray-400 mb-1">Environment</p>
                <p className="font-mono text-lg capitalize">{metrics?.system_info.environment || 'unknown'}</p>
              </div>
              
              <div>
                <p className="text-sm text-gray-400 mb-1">Uptime</p>
                <p className="font-mono text-lg">{metrics?.performance.uptime_seconds ? Math.floor(metrics.performance.uptime_seconds / 60) : 0} minutes</p>
              </div>
              
              <div>
                <p className="text-sm text-gray-400 mb-1">Average Latency</p>
                <p className="font-mono text-lg">{metrics?.performance.avg_latency_ms || 0} ms</p>
              </div>
            </div>
          </GlassPanel>
        </motion.div>
      </div>
    </div>
  );
}

// Simple workaround since I forgot to import ShieldCheck above
import { ShieldCheck } from 'lucide-react';
