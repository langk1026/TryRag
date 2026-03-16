import { useState, useRef, useEffect } from 'react';
import { Search, Loader2, FileText, ExternalLink, BookOpen, Bot, User } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { queryDocuments } from '../services/api';

export default function SearchInterface() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversation, setConversation] = useState([]);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation, loading]);

  const handleSearch = async (e) => {
    e.preventDefault();

    if (!question.trim()) {
      return;
    }

    const currentQuestion = question.trim();
    setConversation((prev) => [...prev, { role: 'user', content: currentQuestion }]);
    setQuestion('');
    setLoading(true);

    try {
      const data = await queryDocuments(currentQuestion);
      setConversation((prev) => [...prev, { role: 'assistant', data }]);
    } catch (err) {
      setConversation((prev) => [...prev, { role: 'assistant', error: err.response?.data?.detail || 'Failed to process query' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto flex flex-col h-[75vh]">
      <div className="flex-1 overflow-y-auto p-4 space-y-6 bg-white rounded-xl shadow-sm border border-gray-200 mb-6">
        {conversation.length === 0 && !loading && (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <Bot className="w-16 h-16 mb-4 text-gray-300" />
            <p className="text-xl font-medium text-gray-500 mb-2">How can I help you today?</p>
            <p className="text-sm">Ask questions about your uploaded documents.</p>
          </div>
        )}
        
        {conversation.map((msg, index) => (
          <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] rounded-2xl p-6 shadow-sm border ${
              msg.role === 'user' 
                ? 'bg-primary-600 text-white border-primary-700 rounded-br-sm' 
                : 'bg-gray-50 text-gray-800 border-gray-200 rounded-bl-sm'
            }`}>
              {msg.role === 'user' ? (
                <div className="flex items-start gap-3">
                  <User className="w-5 h-5 shrink-0 text-primary-200 mt-1" />
                  <p className="text-lg leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                </div>
              ) : (
                <div className="flex items-start gap-4">
                  <Bot className="w-6 h-6 shrink-0 text-primary-500 mt-1" />
                  <div className="flex-1 min-w-0">
                    {msg.error ? (
                       <p className="text-red-500 font-medium">{msg.error}</p>
                    ) : (
                      <>
                        <div className="prose prose-blue max-w-none text-gray-800">
                          <ReactMarkdown>{msg.data.answer}</ReactMarkdown>
                        </div>
                        
                        {msg.data.sources && msg.data.sources.length > 0 && (
                          <div className="mt-6 pt-4 border-t border-gray-200">
                            <h4 className="text-sm font-semibold text-gray-800 mb-3 flex items-center gap-2">
                              <FileText className="w-4 h-4" />
                              Sources Used
                            </h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                              {msg.data.sources.map((source, sIdx) => (
                                <div key={sIdx} className="p-3 bg-white rounded-lg border border-gray-200 shadow-sm text-sm hover:border-primary-300 transition-colors">
                                  <div className="flex justify-between items-start gap-2 mb-2">
                                    <span className="font-semibold text-gray-900 truncate" title={source.document_name}>
                                      {source.document_name}
                                    </span>
                                    <span className="inline-flex shrink-0 items-center gap-1 px-1.5 py-0.5 bg-primary-50 text-primary-700 border border-primary-100 text-xs font-semibold rounded">
                                      <BookOpen className="w-3 h-3" /> P.{source.page_number}
                                    </span>
                                  </div>
                                  <div className="flex items-center justify-between text-xs text-gray-500">
                                    <span>Relevance: {(source.relevance_score * 100).toFixed(1)}%</span>
                                    {source.url && (
                                       <a href={source.url} target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:text-primary-700 flex items-center gap-1 font-medium bg-primary-50 px-2 py-1 rounded">
                                         Open URL <ExternalLink className="w-3 h-3"/>
                                       </a>
                                    )}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-50 max-w-[85%] rounded-2xl p-6 shadow-sm border border-gray-200 rounded-bl-sm flex items-center gap-4">
              <Bot className="w-6 h-6 text-primary-500 shrink-0" />
              <div className="flex items-center gap-3 text-gray-600">
                <Loader2 className="w-5 h-5 animate-spin text-primary-500" />
                <span className="font-medium animate-pulse">Searching knowledge base...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSearch} className="shrink-0 relative">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about your documents..."
          className="w-full px-6 py-4 pr-16 text-lg border-2 border-gray-300 rounded-xl focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-100 transition-all shadow-sm bg-white"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !question.trim()}
          className="absolute right-3 top-1/2 -translate-y-1/2 p-2.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <Search className="w-6 h-6" />
        </button>
      </form>
    </div>
  );
}
