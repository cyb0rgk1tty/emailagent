export default function EmptyState(): JSX.Element {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-4 py-12">
      <svg
        className="w-24 h-24 text-gray-300 mb-6"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
        />
      </svg>

      <h3 className="text-xl font-semibold text-gray-900 mb-2">
        Select a draft to review
      </h3>

      <p className="text-gray-500 mb-6 max-w-sm">
        Choose a draft from the list on the left to view details and take action
      </p>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 max-w-md text-left">
        <h4 className="font-semibold text-blue-900 mb-2">Quick Tips:</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>
            Use <kbd className="px-1.5 py-0.5 bg-white rounded text-xs border">Up</kbd>{' '}
            <kbd className="px-1.5 py-0.5 bg-white rounded text-xs border">Down</kbd> to navigate
          </li>
          <li>
            Press <kbd className="px-1.5 py-0.5 bg-white rounded text-xs border">Enter</kbd> to approve
          </li>
          <li>
            Press <kbd className="px-1.5 py-0.5 bg-white rounded text-xs border">E</kbd> to edit
          </li>
          <li>
            Press <kbd className="px-1.5 py-0.5 bg-white rounded text-xs border">/</kbd> to search
          </li>
        </ul>
      </div>
    </div>
  );
}
