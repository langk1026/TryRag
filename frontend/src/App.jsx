import { useState } from 'react';
import { Search, Database } from 'lucide-react';
import SearchInterface from './components/SearchInterface';
import IndexManager from './components/IndexManager';

function App() {
  const [activeTab, setActiveTab] = useState('search');

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold text-gray-900">
              RAG Document Assistant
            </h1>
            <div className="text-sm text-gray-600">
              SharePoint Knowledge Base
            </div>
          </div>
        </div>
      </header>

      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex gap-1">
            <button
              onClick={() => setActiveTab('search')}
              className={`flex items-center gap-2 px-6 py-3 font-medium transition-colors border-b-2 ${
                activeTab === 'search'
                  ? 'text-primary-600 border-primary-600'
                  : 'text-gray-600 border-transparent hover:text-gray-900'
              }`}
            >
              <Search className="w-5 h-5" />
              Search
            </button>
            <button
              onClick={() => setActiveTab('index')}
              className={`flex items-center gap-2 px-6 py-3 font-medium transition-colors border-b-2 ${
                activeTab === 'index'
                  ? 'text-primary-600 border-primary-600'
                  : 'text-gray-600 border-transparent hover:text-gray-900'
              }`}
            >
              <Database className="w-5 h-5" />
              Index Management
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {activeTab === 'search' && <SearchInterface />}
        {activeTab === 'index' && <IndexManager />}
      </main>

      <footer className="mt-16 bg-white border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4 text-center text-sm text-gray-600">
          RAG Application - Powered by OpenAI & ChromaDB
        </div>
      </footer>
    </div>
  );
}

export default App;
