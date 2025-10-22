const Leads = () => {
  return (
    <div className="px-4 sm:px-0">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold text-gray-900">Leads</h1>
          <p className="mt-2 text-sm text-gray-700">
            Browse and search all supplement lead inquiries
          </p>
        </div>
      </div>

      <div className="mt-8 bg-white shadow rounded-lg p-6">
        <div className="text-center py-12">
          <h3 className="text-lg font-medium text-gray-900">Lead Browser</h3>
          <p className="mt-2 text-sm text-gray-500">
            Lead browsing interface will be implemented in Phase 5
          </p>
          <ul className="mt-4 text-sm text-gray-500 space-y-1">
            <li>Search and filter leads</li>
            <li>Sort by quality score, date, priority</li>
            <li>View extracted supplement data</li>
            <li>Export capabilities</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default Leads
