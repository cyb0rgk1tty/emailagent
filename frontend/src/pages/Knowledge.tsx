import { useState, FormEvent, ChangeEvent, ReactNode } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { knowledgeAPI } from '../services/api';
import { Upload, RefreshCw, FileText, Database, Search, Trash2, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import ConfirmModal from '../components/ConfirmModal';

interface KnowledgeStats {
  total_documents?: number;
  total_chunks?: number;
  documents_by_type?: Record<string, number>;
}

interface KnowledgeDocument {
  document_name: string;
  document_type: string;
  chunk_count: number;
  version: number;
  last_updated: string;
  is_active: boolean;
}

interface DocumentsResponse {
  documents?: KnowledgeDocument[];
}

interface QueryResult {
  document_name: string;
  content?: string;
  chunk_text?: string;
  similarity_score?: number;
  metadata?: {
    section?: string;
  };
}

interface QueryResults {
  results: QueryResult[];
  total_results?: number;
}

interface ConfirmModalState {
  isOpen: boolean;
  type: 'reindex' | 'delete' | null;
  documentName: string | null;
}

interface StatCardProps {
  title: string;
  value: number;
  subtitle?: string;
  icon: ReactNode;
  color: 'blue' | 'green' | 'purple';
  loading: boolean;
}

interface DocumentRowProps {
  document: KnowledgeDocument;
  onDelete: (documentName: string) => void;
}

interface UploadModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

interface QueryTestModalProps {
  onClose: () => void;
}

export default function Knowledge(): JSX.Element {
  const queryClient = useQueryClient();
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showQueryModal, setShowQueryModal] = useState(false);
  const [confirmModal, setConfirmModal] = useState<ConfirmModalState>({ isOpen: false, type: null, documentName: null });

  // Fetch knowledge base stats
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['knowledge', 'stats'],
    queryFn: knowledgeAPI.getStats,
  });

  // Fetch documents
  const { data: documentsData, isLoading: docsLoading } = useQuery({
    queryKey: ['knowledge', 'documents'],
    queryFn: knowledgeAPI.getDocuments,
  });

  // Reindex mutation
  const reindexMutation = useMutation({
    mutationFn: knowledgeAPI.reindex,
    onSuccess: () => {
      toast.success('Knowledge base re-indexing started');
      queryClient.invalidateQueries({ queryKey: ['knowledge'] });
    },
    onError: (error: Error) => {
      toast.error(`Re-indexing failed: ${error.message}`);
    },
  });

  // Delete document mutation
  const deleteMutation = useMutation({
    mutationFn: (documentName: string) => knowledgeAPI.deleteDocument(documentName),
    onSuccess: () => {
      toast.success('Document deactivated successfully');
      queryClient.invalidateQueries({ queryKey: ['knowledge'] });
    },
    onError: (error: Error) => {
      toast.error(`Delete failed: ${error.message}`);
    },
  });

  const knowledgeStats = (stats?.data || {}) as KnowledgeStats;
  const documents = ((documentsData?.data as DocumentsResponse)?.documents || []) as KnowledgeDocument[];

  const handleReindex = (): void => {
    setConfirmModal({ isOpen: true, type: 'reindex', documentName: null });
  };

  const handleDelete = (documentName: string): void => {
    setConfirmModal({ isOpen: true, type: 'delete', documentName });
  };

  const handleConfirmReindex = (): void => {
    reindexMutation.mutate();
    setConfirmModal({ isOpen: false, type: null, documentName: null });
  };

  const handleConfirmDelete = (): void => {
    if (confirmModal.documentName) {
      deleteMutation.mutate(confirmModal.documentName);
    }
    setConfirmModal({ isOpen: false, type: null, documentName: null });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Knowledge Base Management</h1>
          <p className="text-gray-600 mt-1">Manage RAG system documents and embeddings</p>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            onClick={() => setShowQueryModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <Search className="w-4 h-4" />
            Test RAG Query
          </button>
          <button
            onClick={() => setShowUploadModal(true)}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
          >
            <Upload className="w-4 h-4" />
            Upload Document
          </button>
          <button
            onClick={handleReindex}
            disabled={reindexMutation.isPending}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${reindexMutation.isPending ? 'animate-spin' : ''}`} />
            Re-index
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          title="Total Documents"
          value={knowledgeStats.total_documents || 0}
          icon={<FileText className="w-6 h-6" />}
          color="blue"
          loading={statsLoading}
        />
        <StatCard
          title="Total Chunks"
          value={knowledgeStats.total_chunks || 0}
          icon={<Database className="w-6 h-6" />}
          color="purple"
          loading={statsLoading}
        />
        <StatCard
          title="Documents by Type"
          value={Object.keys(knowledgeStats.documents_by_type || {}).length}
          subtitle="types"
          icon={<FileText className="w-6 h-6" />}
          color="green"
          loading={statsLoading}
        />
      </div>

      {/* Document Type Breakdown */}
      {knowledgeStats.documents_by_type && Object.keys(knowledgeStats.documents_by_type).length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Documents by Type</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(knowledgeStats.documents_by_type).map(([type, count]) => (
              <div key={type} className="border border-gray-200 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-gray-900">{count}</div>
                <div className="text-sm text-gray-600 mt-1 capitalize">{type}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Documents List */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Indexed Documents</h2>
          <span className="text-sm text-gray-500">{documents.length} documents</span>
        </div>

        {docsLoading && (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-500">Loading documents...</p>
          </div>
        )}

        {!docsLoading && documents.length === 0 && (
          <div className="p-8 text-center text-gray-500">
            <FileText className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <p>No documents in knowledge base</p>
            <p className="text-sm mt-2">Upload documents to get started</p>
          </div>
        )}

        {!docsLoading && documents.length > 0 && (
          <div className="divide-y divide-gray-200">
            {documents.map((doc, idx) => (
              <DocumentRow
                key={idx}
                document={doc}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <UploadModal
          onClose={() => setShowUploadModal(false)}
          onSuccess={() => {
            setShowUploadModal(false);
            queryClient.invalidateQueries({ queryKey: ['knowledge'] });
          }}
        />
      )}

      {/* Query Test Modal */}
      {showQueryModal && (
        <QueryTestModal
          onClose={() => setShowQueryModal(false)}
        />
      )}

      {/* Confirmation Modals */}
      <ConfirmModal
        isOpen={confirmModal.isOpen && confirmModal.type === 'reindex'}
        onClose={() => setConfirmModal({ isOpen: false, type: null, documentName: null })}
        onConfirm={handleConfirmReindex}
        title="Re-index Knowledge Base"
        message="Are you sure you want to re-index the entire knowledge base? This may take some time and will regenerate all embeddings."
        confirmText="Re-index"
        cancelText="Cancel"
        variant="warning"
        loading={reindexMutation.isPending}
      />

      <ConfirmModal
        isOpen={confirmModal.isOpen && confirmModal.type === 'delete'}
        onClose={() => setConfirmModal({ isOpen: false, type: null, documentName: null })}
        onConfirm={handleConfirmDelete}
        title="Deactivate Document"
        message={`Are you sure you want to deactivate "${confirmModal.documentName}"? This will mark it as inactive and it won't be used in RAG queries.`}
        confirmText="Deactivate"
        cancelText="Cancel"
        variant="danger"
        loading={deleteMutation.isPending}
      />
    </div>
  );
}

function StatCard({ title, value, subtitle, icon, color, loading }: StatCardProps): JSX.Element {
  const colorClasses: Record<string, string> = {
    blue: 'from-blue-500 to-blue-600',
    green: 'from-green-500 to-green-600',
    purple: 'from-purple-500 to-purple-600',
  };

  return (
    <div className={`bg-gradient-to-br ${colorClasses[color]} rounded-lg shadow-lg p-6 text-white`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-white text-opacity-80 text-sm font-medium">{title}</p>
          {loading ? (
            <div className="mt-2 animate-pulse bg-white bg-opacity-20 h-8 w-16 rounded"></div>
          ) : (
            <p className="text-3xl font-bold mt-2">
              {value}
              {subtitle && <span className="text-lg ml-1">{subtitle}</span>}
            </p>
          )}
        </div>
        <div className="bg-white bg-opacity-20 rounded-full p-3">
          {icon}
        </div>
      </div>
    </div>
  );
}

function DocumentRow({ document, onDelete }: DocumentRowProps): JSX.Element {
  return (
    <div className="p-6 hover:bg-gray-50 transition-colors">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <FileText className="w-5 h-5 text-blue-600" />
            <h3 className="text-lg font-semibold text-gray-900">{document.document_name}</h3>
            <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded capitalize">
              {document.document_type}
            </span>
            {document.is_active && (
              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                Active
              </span>
            )}
          </div>
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <span>{document.chunk_count} chunks</span>
            <span>•</span>
            <span>Version {document.version}</span>
            <span>•</span>
            <span>Updated {new Date(document.last_updated).toLocaleDateString()}</span>
          </div>
        </div>
        <button
          onClick={() => onDelete(document.document_name)}
          className="ml-4 p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          title="Deactivate document"
        >
          <Trash2 className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}

function UploadModal({ onClose, onSuccess }: UploadModalProps): JSX.Element {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [documentType, setDocumentType] = useState('faq');

  const uploadMutation = useMutation({
    mutationFn: (formData: FormData) => knowledgeAPI.upload(formData),
    onSuccess: () => {
      toast.success('Document upload initiated (feature in development)');
      onSuccess();
    },
    onError: (error: Error) => {
      toast.error(`Upload failed: ${error.message}`);
    },
  });

  const handleSubmit = (e: FormEvent<HTMLFormElement>): void => {
    e.preventDefault();
    if (!selectedFile) {
      toast.error('Please select a file');
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('document_type', documentType);

    uploadMutation.mutate(formData);
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>): void => {
    const files = e.target.files;
    if (files && files.length > 0) {
      setSelectedFile(files[0]);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Upload Document</h2>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Document Type
            </label>
            <select
              value={documentType}
              onChange={(e: ChangeEvent<HTMLSelectElement>) => setDocumentType(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="faq">FAQ</option>
              <option value="process">Process Documentation</option>
              <option value="pricing">Pricing Guide</option>
              <option value="capability">Capability Statement</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select File (PDF or Markdown)
            </label>
            <input
              type="file"
              accept=".pdf,.md,.markdown"
              onChange={handleFileChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            {selectedFile && (
              <p className="text-sm text-gray-600 mt-2">
                Selected: {selectedFile.name}
              </p>
            )}
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex gap-2">
              <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0" />
              <p className="text-sm text-yellow-800">
                Note: Full document upload functionality will be implemented in Phase 2.
                For now, please add documents to the <code className="bg-yellow-100 px-1 rounded">/knowledge</code> directory
                and run the ingestion script.
              </p>
            </div>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={uploadMutation.isPending || !selectedFile}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {uploadMutation.isPending ? 'Uploading...' : 'Upload'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function QueryTestModal({ onClose }: QueryTestModalProps): JSX.Element {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<QueryResults | null>(null);

  const queryMutation = useMutation({
    mutationFn: (data: { query: string; top_k: number; threshold: number }) => knowledgeAPI.query(data),
    onSuccess: (response) => {
      setResults(response.data as QueryResults);
      if ((response.data as QueryResults).results.length === 0) {
        toast('No results found. Feature will be fully functional in Phase 2.', { icon: 'ℹ️' });
      }
    },
    onError: (error: Error) => {
      toast.error(`Query failed: ${error.message}`);
    },
  });

  const handleSubmit = (e: FormEvent<HTMLFormElement>): void => {
    e.preventDefault();
    if (!query.trim()) {
      toast.error('Please enter a query');
      return;
    }
    queryMutation.mutate({ query, top_k: 5, threshold: 0.7 });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[80vh] overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Test RAG Query</h2>
          <p className="text-sm text-gray-600 mt-1">Search the knowledge base using semantic similarity</p>
        </div>

        <div className="p-6 space-y-4 overflow-y-auto max-h-[calc(80vh-160px)]">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Query Text
              </label>
              <textarea
                value={query}
                onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setQuery(e.target.value)}
                placeholder="e.g., What certifications do you support?"
                rows={3}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <button
              type="submit"
              disabled={queryMutation.isPending}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {queryMutation.isPending ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Searching...
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  Search Knowledge Base
                </>
              )}
            </button>
          </form>

          {/* Results */}
          {results && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">
                Results ({results.total_results || 0})
              </h3>

              {results.total_results === 0 ? (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <div className="flex gap-2">
                    <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0" />
                    <div>
                      <p className="text-sm text-yellow-800 font-medium">No results found</p>
                      <p className="text-sm text-yellow-700 mt-1">
                        RAG query functionality will be fully implemented in Phase 2.
                        Make sure documents are indexed in the knowledge base.
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  {results.results.map((result, idx) => (
                    <div key={idx} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-start justify-between mb-2">
                        <span className="text-sm font-medium text-gray-900">
                          {result.document_name}
                        </span>
                        <span className="text-sm text-gray-500">
                          Score: {result.similarity_score?.toFixed(3)}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700">{result.content || result.chunk_text}</p>
                      {result.metadata && (
                        <div className="mt-2 text-xs text-gray-500">
                          Section: {result.metadata.section || 'N/A'}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="px-6 py-4 border-t border-gray-200">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
