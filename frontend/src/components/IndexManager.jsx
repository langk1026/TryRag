import { useState, useEffect } from 'react';
import { RefreshCw, Database, Calendar, Loader2 } from 'lucide-react';
import { getIndexStats, triggerFullReindex, triggerIncrementalIndex } from '../services/api';

export default function IndexManager() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [indexing, setIndexing] = useState(false);
  const [message, setMessage] = useState(null);

  const loadStats = async () => {
    setLoading(true);
    try {
      const data = await getIndexStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to load stats:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  const handleFullReindex = async () => {
    if (!confirm('This will reindex all documents. Continue?')) {
      return;
    }

    setIndexing(true);
    setMessage(null);

    try {
      const result = await triggerFullReindex();
      setMessage({
        type: 'success',
        text: `Full reindex completed: ${result.documents_processed} documents, ${result.chunks_created} chunks`
      });
      await loadStats();
    } catch (err) {
      setMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Reindex failed'
      });
    } finally {
      setIndexing(false);
    }
  };

  const handleIncrementalIndex = async () => {
    setIndexing(true);
    setMessage(null);

    try {
      const result = await triggerIncrementalIndex();
      setMessage({
        type: 'success',
        text: `Incremental index completed: ${result.documents_processed} documents, ${result.chunks_created} chunks`
      });
      await loadStats();
    } catch (err) {
      setMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Indexing failed'
      });
    } finally {
      setIndexing(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="max-w-5xl mx-auto">
      <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
        <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
          <Database className="w-6 h-6" />
          Index Management
        </h2>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
          </div>
        ) : stats ? (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-primary-50 rounded-lg">
                <div className="text-sm text-primary-700 font-medium mb-1">
                  Total Chunks
                </div>
                <div className="text-3xl font-bold text-primary-900">
                  {stats.total_chunks.toLocaleString()}
                </div>
              </div>

              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-sm text-gray-700 font-medium mb-1 flex items-center gap-2">
                  <Calendar className="w-4 h-4" />
                  Last Indexed
                </div>
                <div className="text-lg font-semibold text-gray-900">
                  {formatDate(stats.last_indexed)}
                </div>
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
              <button
                onClick={handleIncrementalIndex}
                disabled={indexing}
                className="flex items-center gap-2 px-6 py-3 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium"
              >
                {indexing ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <RefreshCw className="w-5 h-5" />
                )}
                Incremental Index
              </button>

              <button
                onClick={handleFullReindex}
                disabled={indexing}
                className="flex items-center gap-2 px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium"
              >
                {indexing ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Database className="w-5 h-5" />
                )}
                Full Reindex
              </button>
            </div>

            {message && (
              <div className={`p-4 rounded-lg ${
                message.type === 'success'
                  ? 'bg-green-50 border border-green-200 text-green-700'
                  : 'bg-red-50 border border-red-200 text-red-700'
              }`}>
                {message.text}
              </div>
            )}
          </div>
        ) : (
          <div className="text-center text-gray-500 py-8">
            Failed to load index statistics
          </div>
        )}
      </div>
    </div>
  );
}
