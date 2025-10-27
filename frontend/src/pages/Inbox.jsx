import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { draftsAPI } from '../services/api'
import DraftListSidebar from '../components/inbox/DraftListSidebar'
import DraftDetailView from '../components/inbox/DraftDetailView'
import EmptyState from '../components/inbox/EmptyState'

export default function Inbox() {
  const queryClient = useQueryClient()
  const [selectedDraftId, setSelectedDraftId] = useState(null)
  const [statusFilter, setStatusFilter] = useState('pending')
  const [showSidebar, setShowSidebar] = useState(true) // For mobile

  // Fetch drafts based on filter
  const { data: drafts, isLoading, error } = useQuery({
    queryKey: ['drafts', statusFilter],
    queryFn: () => statusFilter === 'pending'
      ? draftsAPI.getPending(100)
      : draftsAPI.getAll({ status: statusFilter === 'all' ? undefined : statusFilter, limit: 100 }),
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  })

  // Fetch draft stats (independent of filter)
  const { data: stats } = useQuery({
    queryKey: ['draft-stats'],
    queryFn: () => draftsAPI.getCount(),
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  })

  const draftsList = Array.isArray(drafts?.data) ? drafts.data : (Array.isArray(drafts) ? drafts : [])

  // Get selected draft
  const selectedDraft = draftsList.find(d => d.id === selectedDraftId)

  // Auto-select first draft when list changes
  useEffect(() => {
    if (draftsList.length > 0 && !selectedDraftId) {
      setSelectedDraftId(draftsList[0].id)
    }
    // If selected draft is no longer in the list, select first available
    if (selectedDraftId && !draftsList.find(d => d.id === selectedDraftId)) {
      setSelectedDraftId(draftsList.length > 0 ? draftsList[0].id : null)
    }
  }, [draftsList, selectedDraftId])

  // Handle draft selection
  const handleSelectDraft = (draftId) => {
    setSelectedDraftId(draftId)
    // Hide sidebar on mobile after selection
    if (window.innerWidth < 1024) {
      setShowSidebar(false)
    }
  }

  // Handle filter change
  const handleFilterChange = (newFilter) => {
    setStatusFilter(newFilter)
    setSelectedDraftId(null) // Clear selection when changing filters
  }

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Don't trigger shortcuts if user is typing in an input
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        // Allow / to focus search even when in an input (unless it's the search input itself)
        if (e.key === '/' && e.target.placeholder !== 'Search drafts...') {
          e.preventDefault()
          document.querySelector('input[placeholder="Search drafts..."]')?.focus()
        }
        return
      }

      // Focus search with /
      if (e.key === '/') {
        e.preventDefault()
        document.querySelector('input[placeholder="Search drafts..."]')?.focus()
        return
      }

      // Navigation shortcuts only work when a draft is selected
      if (!selectedDraftId) return

      const currentIndex = draftsList.findIndex(d => d.id === selectedDraftId)

      switch (e.key) {
        case 'ArrowUp':
          e.preventDefault()
          if (currentIndex > 0) {
            setSelectedDraftId(draftsList[currentIndex - 1].id)
          }
          break
        case 'ArrowDown':
          e.preventDefault()
          if (currentIndex < draftsList.length - 1) {
            setSelectedDraftId(draftsList[currentIndex + 1].id)
          }
          break
        case 'Enter':
          e.preventDefault()
          if (selectedDraft?.status === 'pending') {
            // Trigger approve action
            const approveButton = document.querySelector('button:has(svg) + button:has(svg):last-of-type')
            approveButton?.click()
          }
          break
        case 'e':
        case 'E':
          e.preventDefault()
          if (selectedDraft?.status === 'pending') {
            // Trigger edit action
            const editButton = document.querySelector('button:has(svg):first-of-type')
            editButton?.click()
          }
          break
        case 'Delete':
        case 'Backspace':
          e.preventDefault()
          if (selectedDraft?.status === 'pending') {
            // Trigger reject action
            const rejectButton = document.querySelector('button:has(svg) + button:has(svg)')
            rejectButton?.click()
          }
          break
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [selectedDraftId, draftsList, selectedDraft])

  return (
    <div className="-mx-6 lg:-mx-8 -my-6 flex h-[calc(100vh-4rem)] overflow-hidden">
      {/* Mobile: Back button when sidebar is hidden */}
      {!showSidebar && (
        <button
          onClick={() => setShowSidebar(true)}
          className="lg:hidden fixed top-20 left-4 z-20 p-2 bg-white border border-gray-300 rounded-lg shadow-lg"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      )}

      {/* Left Sidebar - Draft List */}
      <div className={`
        w-full lg:w-[450px] xl:w-[500px] flex-shrink-0
        ${showSidebar ? 'block' : 'hidden lg:block'}
      `}>
        <DraftListSidebar
          drafts={draftsList}
          stats={stats?.data || stats}
          isLoading={isLoading}
          error={error}
          selectedDraftId={selectedDraftId}
          onSelectDraft={handleSelectDraft}
          statusFilter={statusFilter}
          onFilterChange={handleFilterChange}
        />
      </div>

      {/* Main Content Area - Draft Detail */}
      <div className={`
        flex-1 bg-gray-50 overflow-hidden
        ${showSidebar ? 'hidden lg:block' : 'block'}
      `}>
        {selectedDraft ? (
          <DraftDetailView draft={selectedDraft} />
        ) : (
          <EmptyState />
        )}
      </div>
    </div>
  )
}
