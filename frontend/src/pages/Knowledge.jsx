const Knowledge = () => {
  return (
    <div className="px-4 sm:px-0">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold text-gray-900">Knowledge Base</h1>
          <p className="mt-2 text-sm text-gray-700">
            Manage RAG system documents and embeddings
          </p>
        </div>
      </div>

      <div className="mt-8 bg-white shadow rounded-lg p-6">
        <div className="text-center py-12">
          <h3 className="text-lg font-medium text-gray-900">Document Management</h3>
          <p className="mt-2 text-sm text-gray-500">
            Knowledge base management will be implemented in Phase 2 & 5
          </p>
          <ul className="mt-4 text-sm text-gray-500 space-y-1">
            <li>Upload new documents</li>
            <li>Re-index knowledge base</li>
            <li>View document statistics</li>
            <li>Test RAG queries</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default Knowledge
