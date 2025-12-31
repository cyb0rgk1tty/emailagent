import { useState, ChangeEvent } from 'react';
import DraftListItem from './DraftListItem';
import { emailsAPI } from '../../services/api';
import type { Draft, DraftStats } from '../../types/api';

interface DraftListSidebarProps {
  drafts: Draft[];
  stats: DraftStats | null;
  isLoading: boolean;
  error: Error | null;
  selectedDraftId: number | null;
  onSelectDraft: (id: number) => void;
  statusFilter: string;
  onFilterChange: (filter: string) => void;
}

export default function DraftListSidebar({
  drafts,
  stats,
  isLoading,
  error,
  selectedDraftId,
  onSelectDraft,
  statusFilter,
  onFilterChange,
}: DraftListSidebarProps): JSX.Element {
  const [searchQuery, setSearchQuery] = useState('');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshMessage, setRefreshMessage] = useState('');

  // Handle manual email refresh
  const handleRefresh = async (): Promise<void> => {
    setIsRefreshing(true);
    setRefreshMessage('');
    try {
      await emailsAPI.triggerCheck();
      setRefreshMessage('Checking for new emails...');
      setTimeout(() => setRefreshMessage(''), 3000);
    } catch {
      setRefreshMessage('Failed to trigger email check');
      setTimeout(() => setRefreshMessage(''), 3000);
    } finally {
      setTimeout(() => setIsRefreshing(false), 1000);
    }
  };

  // Filter drafts by search query
  const filteredDrafts = drafts.filter((draft) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      draft.subject_line?.toLowerCase().includes(query) ||
      draft.lead?.sender_name?.toLowerCase().includes(query) ||
      draft.lead?.sender_email?.toLowerCase().includes(query) ||
      draft.lead?.product_type?.some(p => p.toLowerCase().includes(query))
    );
  });

  // Get counts from stats (independent of current filter) - defaults to 0 if stats not loaded
  const pendingCount = stats?.pending_drafts || 0;
  const approvedCount = stats?.approved_drafts || 0;
  const rejectedCount = stats?.rejected_drafts || 0;

  return (
    <div className="flex flex-col h-full bg-white border-r border-gray-200">
      {/* Header with Stats */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">Inbox</h2>
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Check for new emails"
          >
            <svg
              className={`w-5 h-5 ${isRefreshing ? 'animate-spin' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
          </button>
        </div>

        {/* Refresh feedback message */}
        {refreshMessage && (
          <div className="mb-3 px-3 py-2 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-700">
            {refreshMessage}
          </div>
        )}

        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-3 mb-5">
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <div className="text-xs text-blue-600 font-medium">Pending</div>
            <div className="text-xl font-bold text-blue-900 mt-1">{pendingCount}</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-xs text-green-600 font-medium">Approved</div>
            <div className="text-xl font-bold text-green-900 mt-1">{approvedCount}</div>
          </div>
          <div className="text-center p-3 bg-red-50 rounded-lg">
            <div className="text-xs text-red-600 font-medium">Rejected</div>
            <div className="text-xl font-bold text-red-900 mt-1">{rejectedCount}</div>
          </div>
        </div>

        {/* Search Box */}
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setSearchQuery(e.target.value)}
            placeholder="Search drafts..."
            className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
          />
          <svg
            className="absolute left-3 top-3 w-4 h-4 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex border-b border-gray-200 bg-gray-50">
        <button
          onClick={() => onFilterChange('pending')}
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
            statusFilter === 'pending'
              ? 'text-blue-600 border-b-2 border-blue-600 bg-white'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
          }`}
        >
          Pending
          {pendingCount > 0 && (
            <span className="ml-1 text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded-full">
              {pendingCount}
            </span>
          )}
        </button>
        <button
          onClick={() => onFilterChange('approved')}
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
            statusFilter === 'approved'
              ? 'text-green-600 border-b-2 border-green-600 bg-white'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
          }`}
        >
          Approved
        </button>
        <button
          onClick={() => onFilterChange('rejected')}
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
            statusFilter === 'rejected'
              ? 'text-red-600 border-b-2 border-red-600 bg-white'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
          }`}
        >
          Rejected
        </button>
        <button
          onClick={() => onFilterChange('all')}
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
            statusFilter === 'all'
              ? 'text-gray-900 border-b-2 border-gray-900 bg-white'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
          }`}
        >
          All
        </button>
      </div>

      {/* Draft List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading && (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        )}

        {error && (
          <div className="p-4 text-center text-red-600 text-sm">
            Error loading drafts
          </div>
        )}

        {!isLoading && !error && filteredDrafts.length === 0 && (
          <div className="p-8 text-center">
            <svg className="mx-auto h-12 w-12 text-gray-400 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
            </svg>
            <p className="text-sm text-gray-500 mb-4">
              {searchQuery ? 'No drafts match your search' : `No ${statusFilter} drafts found`}
            </p>
            {!searchQuery && (
              <button
                onClick={handleRefresh}
                disabled={isRefreshing}
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg
                  className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                {isRefreshing ? 'Checking...' : 'Check for New Emails'}
              </button>
            )}
          </div>
        )}

        {!isLoading && !error && filteredDrafts.length > 0 && (
          <div>
            {filteredDrafts.map((draft) => (
              <DraftListItem
                key={draft.id}
                draft={draft}
                isSelected={selectedDraftId === draft.id}
                onClick={() => onSelectDraft(draft.id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Footer with keyboard shortcuts hint */}
      <div className="p-3 border-t border-gray-200 bg-gray-50 text-xs text-gray-600">
        <div className="flex items-center justify-center gap-2">
          <span>Shortcuts:</span>
          <kbd className="px-1.5 py-0.5 bg-white rounded border border-gray-300">Up/Down</kbd>
          <kbd className="px-1.5 py-0.5 bg-white rounded border border-gray-300">Enter</kbd>
          <kbd className="px-1.5 py-0.5 bg-white rounded border border-gray-300">E</kbd>
          <kbd className="px-1.5 py-0.5 bg-white rounded border border-gray-300">/</kbd>
        </div>
      </div>
    </div>
  );
}
