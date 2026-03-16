import { Activity, BarChart3, Network, ExternalLink } from 'lucide-react';
import PipelineFlowChart from './PipelineFlowChart';

export default function ObservabilityView() {
  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* LangGraph Visualization Section */}
      <div className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden">
        <div className="p-6 border-b border-gray-100 bg-gray-50 flex items-center gap-3">
          <Network className="w-6 h-6 text-primary-600" />
          <div>
            <h2 className="text-xl font-bold text-gray-800">Agentic Orchestration Flow</h2>
            <p className="text-sm text-gray-500 mt-1">
              Live representation of the LangGraph state machine handling your RAG queries.
            </p>
          </div>
        </div>

        <div className="p-8 flex justify-center items-center min-h-[400px] bg-white overflow-x-auto">
          <PipelineFlowChart />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Langfuse Section */}
        <div className="bg-white rounded-xl shadow-md border border-gray-200 p-6 flex flex-col pt-8 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-green-500" />
          <h3 className="text-lg font-bold text-gray-800 mb-2 flex items-center gap-2">
            <Network className="w-5 h-5 text-green-500" /> LLM Observability (Langfuse)
          </h3>
          <p className="text-gray-600 mb-6 text-sm flex-1">
            Purpose-built LLM tracing with token costs, conversation sessions, quality metrics, and per-node latency breakdowns.
          </p>
          <a
            href="https://cloud.langfuse.com"
            target="_blank"
            rel="noopener noreferrer"
            className="w-full flex justify-center items-center gap-2 px-4 py-3 bg-white border-2 border-green-500 text-green-600 font-semibold rounded-lg hover:bg-green-50 transition-colors"
          >
            Open Langfuse Cloud <ExternalLink className="w-4 h-4" />
          </a>
        </div>

        {/* Jaeger Section */}
        <div className="bg-white rounded-xl shadow-md border border-gray-200 p-6 flex flex-col pt-8 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-blue-500" />
          <h3 className="text-lg font-bold text-gray-800 mb-2 flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-500" /> Distributed Tracing (Jaeger)
          </h3>
          <p className="text-gray-600 mb-6 text-sm flex-1">
            OpenTelemetry-powered traces across FastAPI, LangChain, and ChromaDB boundaries for latency analysis.
          </p>
          <a
            href="http://localhost:16686"
            target="_blank"
            rel="noopener noreferrer"
            className="w-full flex justify-center items-center gap-2 px-4 py-3 bg-white border-2 border-blue-500 text-blue-600 font-semibold rounded-lg hover:bg-blue-50 transition-colors"
          >
            Open Jaeger UI <ExternalLink className="w-4 h-4" />
          </a>
        </div>

        {/* Grafana Section */}
        <div className="bg-white rounded-xl shadow-md border border-gray-200 p-6 flex flex-col pt-8 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-orange-500" />
          <h3 className="text-lg font-bold text-gray-800 mb-2 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-orange-500" /> Infrastructure Metrics (Grafana)
          </h3>
          <p className="text-gray-600 mb-6 text-sm flex-1">
            Aggregated system metrics from backend, vector store, and container health via OTEL Collector.
          </p>
          <a
            href="http://localhost:3001"
            target="_blank"
            rel="noopener noreferrer"
            className="w-full flex justify-center items-center gap-2 px-4 py-3 bg-white border-2 border-orange-500 text-orange-600 font-semibold rounded-lg hover:bg-orange-50 transition-colors"
          >
            Open Grafana Dashboards <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </div>
    </div>
  );
}
