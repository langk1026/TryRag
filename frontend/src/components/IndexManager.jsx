import { useState, useEffect, useRef } from 'react';
import { RefreshCw, Database, Calendar, Loader2, UploadCloud, Trash2, FileText } from 'lucide-react';
import { getIndexStats, triggerFullReindex, triggerIncrementalIndex, uploadDocument, getIndexedDocuments, deleteIndexedDocument } from '../services/api';

export default function IndexManager() {
  const [stats, setStats] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [indexing, setIndexing] = useState(false);
  const [message, setMessage] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const statsData = await getIndexStats();
      const docsData = await getIndexedDocuments();
      setStats(statsData);
      setDocuments(docsData);
    } catch (err) {
      console.error('Failed to load stats or documents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
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
      await loadData();
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
      await loadData();
    } catch (err) {
      setMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Indexing failed'
      });
    } finally {
      setIndexing(false);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      await handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = async (e) => {
    if (e.target.files && e.target.files.length > 0) {
      await handleFileUpload(e.target.files[0]);
    }
  };

  const handleFileUpload = async (file) => {
    setUploading(true);
    setMessage(null);
    try {
      const result = await uploadDocument(file);
      setMessage({
        type: 'success',
        text: `File uploaded & indexed: ${result.documents_processed} docs, ${result.chunks_created} chunks`
      });
      await loadData();
    } catch (err) {
      setMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Upload failed'
      });
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDeleteDocument = async (id) => {
    if (!confirm('Are you sure you want to delete this document from the index?')) {
      return;
    }
    setIndexing(true);
    setMessage(null);
    try {
      await deleteIndexedDocument(id);
      setMessage({
        type: 'success',
        text: 'Document deleted successfully'
      });
      await loadData();
    } catch (err) {
      setMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to delete document'
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

            <div className="flex flex-wrap gap-3 mb-6">
              <button
                onClick={handleIncrementalIndex}
                disabled={indexing || uploading}
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
                disabled={indexing || uploading}
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

            <div 
              className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${isDragging ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:bg-gray-50'}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <input 
                type="file" 
                ref={fileInputRef} 
                className="hidden" 
                onChange={handleFileInput} 
              />
              <UploadCloud className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-1">Upload & Index Document</h3>
              <p className="text-sm text-gray-500 mb-4">Drag and drop your file here, or click to browse</p>
              <button 
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading || indexing}
                className="px-4 py-2 bg-white border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed"
              >
                {uploading ? (
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Uploading...
                  </div>
                ) : 'Select File'}
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
            
            <div className="mt-8 border-t border-gray-200 pt-8">
              <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                <FileText className="w-5 h-5 text-gray-500" />
                Indexed Documents
              </h3>
              
              {documents.length === 0 ? (
                <div className="text-center text-gray-500 py-8 bg-gray-50 rounded-lg">
                  No documents found in the index.
                </div>
              ) : (
                <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="bg-gray-50 border-b border-gray-200 text-sm font-semibold text-gray-700">
                        <th className="p-4">Document Name</th>
                        <th className="p-4">Path</th>
                        <th className="p-4">Chunks</th>
                        <th className="p-4 text-center">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {documents.map((doc, idx) => (
                        <tr key={doc.id || idx} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="p-4 font-medium text-gray-900">{doc.name}</td>
                          <td className="p-4 text-sm text-gray-500 truncate max-w-xs" title={doc.path}>{doc.path}</td>
                          <td className="p-4 text-sm text-gray-700">{doc.chunks_count}</td>
                          <td className="p-4 text-center">
                            <button
                              onClick={() => handleDeleteDocument(doc.id)}
                              disabled={indexing || uploading}
                              className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                              title="Delete from index"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
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
