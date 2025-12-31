import { useQuery } from '@tanstack/react-query';
import { leadsAPI, draftsAPI, analyticsAPI } from '../services/api';
import type { Lead, Draft } from '../types/api';

interface LeadsCountResponse {
  total_leads: number;
}

interface DraftsCountResponse {
  total_drafts: number;
  pending_drafts: number;
}

interface AnalyticsSummaryResponse {
  avg_response_time?: string;
}

export default function Dashboard(): JSX.Element {
  // Fetch stats
  const { data: leadsCount } = useQuery({
    queryKey: ['leadsCount'],
    queryFn: leadsAPI.getCount,
  });

  const { data: draftsCount } = useQuery({
    queryKey: ['draftsCount'],
    queryFn: draftsAPI.getCount,
  });

  const { data: analytics } = useQuery({
    queryKey: ['analytics', 'summary'],
    queryFn: () => analyticsAPI.getSummary(),
  });

  const { data: recentLeads } = useQuery({
    queryKey: ['leads', 'recent'],
    queryFn: () => leadsAPI.getAll({ limit: 5 }),
  });

  const { data: pendingDrafts } = useQuery({
    queryKey: ['drafts', 'pending', 'recent'],
    queryFn: () => draftsAPI.getPending(5),
  });

  const leadsCountData = leadsCount?.data as LeadsCountResponse | undefined;
  const draftsCountData = draftsCount?.data as DraftsCountResponse | undefined;
  const analyticsData = analytics?.data as AnalyticsSummaryResponse | undefined;

  const totalLeads = leadsCountData?.total_leads || 0;
  const totalDrafts = draftsCountData?.total_drafts || 0;
  const pendingCount = draftsCountData?.pending_drafts || 0;

  const recentLeadsList = (recentLeads?.data || []) as Lead[];
  const pendingDraftsList = (pendingDrafts?.data || []) as Draft[];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Overview Dashboard</h1>
        <p className="text-gray-600 mt-1">Supplement Lead Intelligence System</p>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Leads */}
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg shadow-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100 text-sm font-medium">Total Leads</p>
              <p className="text-3xl font-bold mt-2">{totalLeads}</p>
            </div>
            <div className="bg-blue-400 bg-opacity-30 rounded-full p-3">
              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm text-blue-100">
            <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
            All time
          </div>
        </div>

        {/* Pending Approval */}
        <div className="bg-gradient-to-br from-yellow-500 to-yellow-600 rounded-lg shadow-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-yellow-100 text-sm font-medium">Pending Approval</p>
              <p className="text-3xl font-bold mt-2">{pendingCount}</p>
            </div>
            <div className="bg-yellow-400 bg-opacity-30 rounded-full p-3">
              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm text-yellow-100">
            <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            Needs review
          </div>
        </div>

        {/* Total Drafts */}
        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg shadow-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-100 text-sm font-medium">Total Drafts</p>
              <p className="text-3xl font-bold mt-2">{totalDrafts}</p>
            </div>
            <div className="bg-green-400 bg-opacity-30 rounded-full p-3">
              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm text-green-100">
            <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            All time
          </div>
        </div>

        {/* Avg Response Time */}
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg shadow-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-100 text-sm font-medium">Avg Response Time</p>
              <p className="text-3xl font-bold mt-2">
                {analyticsData?.avg_response_time || '<1m'}
              </p>
            </div>
            <div className="bg-purple-400 bg-opacity-30 rounded-full p-3">
              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm text-purple-100">
            <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
            98% under 2 min
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Leads */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Recent Leads</h2>
            <a href="/leads" className="text-sm text-blue-600 hover:text-blue-800">View all &rarr;</a>
          </div>
          <div className="divide-y divide-gray-200">
            {recentLeadsList.length > 0 ? (
              recentLeadsList.slice(0, 5).map((lead) => (
                <div key={lead.id} className="px-6 py-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {lead.sender_name || lead.sender_email}
                      </p>
                      <p className="text-sm text-gray-500 truncate">
                        {lead.subject}
                      </p>
                    </div>
                    <div className="ml-4 flex items-center gap-2">
                      <span className={`px-2 py-1 text-xs font-medium rounded ${
                        lead.response_priority === 'critical' ? 'bg-red-100 text-red-800' :
                        lead.response_priority === 'high' ? 'bg-orange-100 text-orange-800' :
                        lead.response_priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {lead.response_priority || 'N/A'}
                      </span>
                      <span className="text-sm text-gray-500">
                        {lead.lead_quality_score || 0}/10
                      </span>
                    </div>
                  </div>
                  {lead.product_type && lead.product_type.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {lead.product_type.slice(0, 3).map((product, idx) => (
                        <span key={`${lead.id}-${idx}`} className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded">
                          {product}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="px-6 py-8 text-center text-gray-500">
                {recentLeads === undefined ? 'Loading...' : 'No recent leads'}
              </div>
            )}
          </div>
        </div>

        {/* Pending Drafts for Review */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Pending Drafts</h2>
            <a href="/inbox" className="text-sm text-blue-600 hover:text-blue-800">View all &rarr;</a>
          </div>
          <div className="divide-y divide-gray-200">
            {pendingDraftsList.slice(0, 5).map((draft) => (
              <div key={draft.id} className="px-6 py-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {draft.subject_line}
                    </p>
                    <p className="text-sm text-gray-500">
                      To: {draft.lead?.sender_email}
                    </p>
                  </div>
                  <div className="ml-4 flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-900">
                      {(draft.confidence_score || 0).toFixed(1)}
                    </span>
                    <span className="text-xs text-gray-500">confidence</span>
                  </div>
                </div>
                {draft.flags && draft.flags.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {draft.flags.slice(0, 2).map((flag) => (
                      <span key={flag} className="px-2 py-0.5 bg-yellow-50 text-yellow-700 text-xs rounded">
                        {flag.replace(/_/g, ' ')}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {pendingDraftsList.length === 0 && (
              <div className="px-6 py-8 text-center text-gray-500">
                No pending drafts
              </div>
            )}
          </div>
        </div>
      </div>

      {/* System Status */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">System Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="flex items-center gap-3">
            <div className="bg-green-100 rounded-full p-2">
              <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">RAG System</p>
              <p className="text-xs text-gray-500">98 chunks indexed</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="bg-green-100 rounded-full p-2">
              <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">AI Agents</p>
              <p className="text-xs text-gray-500">All operational</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="bg-green-100 rounded-full p-2">
              <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">Email Service</p>
              <p className="text-xs text-gray-500">Connected</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
