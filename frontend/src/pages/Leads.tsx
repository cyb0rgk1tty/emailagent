import { useState, ChangeEvent, MouseEvent } from 'react';
import { useQuery } from '@tanstack/react-query';
import { leadsAPI, conversationsAPI } from '../services/api';
import { Search, X, MessageCircle, Mail, Calendar, Star, ArrowUpDown } from 'lucide-react';
import type { Lead, ConversationTimeline, TimelineEvent } from '../types/api';

interface StatCardProps {
  label: string;
  value: string | number;
  color: 'blue' | 'green' | 'purple' | 'orange' | 'indigo';
  subtitle?: string;
}

interface SortButtonProps {
  active: boolean;
  onClick: () => void;
  label: string;
}

interface LeadRowProps {
  lead: Lead;
  onClick: () => void;
}

interface LeadDetailModalProps {
  lead: Lead;
  timeline?: ConversationTimeline;
  onClose: () => void;
}

interface DetailFieldProps {
  label: string;
  value: string;
}

interface TimelineEventProps {
  event: TimelineEvent;
}

export default function Leads(): JSX.Element {
  const [searchTerm, setSearchTerm] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sortBy, setSortBy] = useState('received_at');
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);

  // Fetch all leads
  const { data: leadsData, isLoading } = useQuery({
    queryKey: ['leads', 'all'],
    queryFn: () => leadsAPI.getAll({ limit: 1000 }),
  });

  // Fetch conversation timeline for selected lead
  const { data: timeline } = useQuery({
    queryKey: ['conversation', 'timeline', selectedLead?.id],
    queryFn: () => conversationsAPI.getTimeline(selectedLead!.id),
    enabled: !!selectedLead?.id,
  });

  const leads = (leadsData?.data || []) as Lead[];

  // Filter and sort leads
  const filteredLeads = leads
    .filter(lead => {
      // Search filter
      const searchLower = searchTerm.toLowerCase();
      const matchesSearch = !searchTerm ||
        lead.sender_email?.toLowerCase().includes(searchLower) ||
        lead.sender_name?.toLowerCase().includes(searchLower) ||
        lead.subject?.toLowerCase().includes(searchLower) ||
        lead.company_name?.toLowerCase().includes(searchLower) ||
        lead.body?.toLowerCase().includes(searchLower);

      // Priority filter
      const matchesPriority = !priorityFilter || lead.response_priority === priorityFilter;

      // Status filter
      const matchesStatus = !statusFilter || lead.lead_status === statusFilter;

      return matchesSearch && matchesPriority && matchesStatus;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'received_at':
          return new Date(b.received_at).getTime() - new Date(a.received_at).getTime();
        case 'quality_score':
          return (b.lead_quality_score || 0) - (a.lead_quality_score || 0);
        case 'priority': {
          const priorityOrder: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };
          return (priorityOrder[a.response_priority || ''] ?? 4) - (priorityOrder[b.response_priority || ''] ?? 4);
        }
        default:
          return 0;
      }
    });

  // Calculate stats
  const stats = {
    total: filteredLeads.length,
    new: filteredLeads.filter(l => l.lead_status === 'new').length,
    responded: filteredLeads.filter(l => l.lead_status === 'responded').length,
    customerReplied: filteredLeads.filter(l => l.lead_status === 'customer_replied').length,
    avgQuality: filteredLeads.length > 0
      ? (filteredLeads.reduce((sum, l) => sum + (l.lead_quality_score || 0), 0) / filteredLeads.length).toFixed(1)
      : '0.0',
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Lead Browser</h1>
        <p className="text-gray-600 mt-1">Search and manage all supplement lead inquiries</p>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <StatCard label="Total Leads" value={stats.total} color="blue" />
        <StatCard label="New" value={stats.new} color="green" />
        <StatCard label="Responded" value={stats.responded} color="purple" />
        <StatCard label="Customer Replied" value={stats.customerReplied} color="orange" />
        <StatCard label="Avg Quality" value={stats.avgQuality} color="indigo" subtitle="/10" />
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div className="md:col-span-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search by email, name, company, subject..."
                value={searchTerm}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              {searchTerm && (
                <button
                  onClick={() => setSearchTerm('')}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>

          {/* Priority Filter */}
          <div>
            <select
              value={priorityFilter}
              onChange={(e: ChangeEvent<HTMLSelectElement>) => setPriorityFilter(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Priorities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={statusFilter}
              onChange={(e: ChangeEvent<HTMLSelectElement>) => setStatusFilter(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Statuses</option>
              <option value="new">New</option>
              <option value="responded">Responded</option>
              <option value="customer_replied">Customer Replied</option>
              <option value="conversation_active">Conversation Active</option>
              <option value="closed">Closed</option>
            </select>
          </div>
        </div>

        {/* Sort Options */}
        <div className="mt-4 flex items-center gap-4">
          <div className="flex items-center gap-2">
            <ArrowUpDown className="w-4 h-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-700">Sort by:</span>
          </div>
          <div className="flex gap-2">
            <SortButton
              active={sortBy === 'received_at'}
              onClick={() => setSortBy('received_at')}
              label="Date"
            />
            <SortButton
              active={sortBy === 'quality_score'}
              onClick={() => setSortBy('quality_score')}
              label="Quality"
            />
            <SortButton
              active={sortBy === 'priority'}
              onClick={() => setSortBy('priority')}
              label="Priority"
            />
          </div>
        </div>
      </div>

      {/* Leads List */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        {isLoading && (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-500">Loading leads...</p>
          </div>
        )}

        {!isLoading && filteredLeads.length === 0 && (
          <div className="p-8 text-center text-gray-500">
            <Search className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <p>No leads found matching your filters</p>
          </div>
        )}

        {!isLoading && filteredLeads.length > 0 && (
          <div className="divide-y divide-gray-200">
            {filteredLeads.map((lead) => (
              <LeadRow
                key={lead.id}
                lead={lead}
                onClick={() => setSelectedLead(lead)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Lead Detail Modal */}
      {selectedLead && (
        <LeadDetailModal
          lead={selectedLead}
          timeline={timeline?.data}
          onClose={() => setSelectedLead(null)}
        />
      )}
    </div>
  );
}

function StatCard({ label, value, color, subtitle }: StatCardProps): JSX.Element {
  const colorClasses: Record<string, string> = {
    blue: 'border-blue-200 bg-blue-50',
    green: 'border-green-200 bg-green-50',
    purple: 'border-purple-200 bg-purple-50',
    orange: 'border-orange-200 bg-orange-50',
    indigo: 'border-indigo-200 bg-indigo-50',
  };

  const textClasses: Record<string, string> = {
    blue: 'text-blue-900',
    green: 'text-green-900',
    purple: 'text-purple-900',
    orange: 'text-orange-900',
    indigo: 'text-indigo-900',
  };

  return (
    <div className={`border rounded-lg p-4 ${colorClasses[color]}`}>
      <div className={`text-sm font-medium ${textClasses[color]} opacity-80`}>{label}</div>
      <div className={`text-2xl font-bold ${textClasses[color]} mt-1`}>
        {value}
        {subtitle && <span className="text-sm ml-1">{subtitle}</span>}
      </div>
    </div>
  );
}

function SortButton({ active, onClick, label }: SortButtonProps): JSX.Element {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
        active
          ? 'bg-blue-600 text-white'
          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
      }`}
    >
      {label}
    </button>
  );
}

function LeadRow({ lead, onClick }: LeadRowProps): JSX.Element {
  const getPriorityColor = (priority: string | undefined): string => {
    const colors: Record<string, string> = {
      critical: 'bg-red-100 text-red-800 border-red-300',
      high: 'bg-orange-100 text-orange-800 border-orange-300',
      medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      low: 'bg-gray-100 text-gray-800 border-gray-300',
    };
    return colors[priority || ''] || colors.medium;
  };

  const getStatusColor = (status: string | undefined): string => {
    const colors: Record<string, string> = {
      new: 'bg-blue-100 text-blue-800',
      responded: 'bg-green-100 text-green-800',
      customer_replied: 'bg-purple-100 text-purple-800',
      conversation_active: 'bg-indigo-100 text-indigo-800',
      closed: 'bg-gray-100 text-gray-800',
    };
    return colors[status || ''] || colors.new;
  };

  return (
    <div
      onClick={onClick}
      className="p-6 hover:bg-gray-50 cursor-pointer transition-colors"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-lg font-semibold text-gray-900 truncate">
              {lead.sender_name || lead.sender_email}
            </h3>
            <span className={`px-2 py-1 text-xs font-medium rounded border ${getPriorityColor(lead.response_priority)}`}>
              {lead.response_priority}
            </span>
            <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusColor(lead.lead_status as string)}`}>
              {(lead.lead_status as string)?.replace(/_/g, ' ')}
            </span>
            {lead.is_duplicate && (
              <span className="px-2 py-1 text-xs font-medium rounded bg-yellow-100 text-yellow-800">
                Duplicate
              </span>
            )}
          </div>

          {/* Meta Info */}
          <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
            <div className="flex items-center gap-1">
              <Mail className="w-4 h-4" />
              <span>{lead.sender_email}</span>
            </div>
            {lead.company_name && (
              <div className="flex items-center gap-1">
                <span>-</span>
                <span>{lead.company_name}</span>
              </div>
            )}
            <div className="flex items-center gap-1">
              <Calendar className="w-4 h-4" />
              <span>{new Date(lead.received_at).toLocaleDateString()}</span>
            </div>
            {lead.conversation_id && (
              <div className="flex items-center gap-1">
                <MessageCircle className="w-4 h-4" />
                <span>Has thread</span>
              </div>
            )}
          </div>

          {/* Subject */}
          <p className="text-sm font-medium text-gray-700 mb-2">{lead.subject}</p>

          {/* Body Preview */}
          <p className="text-sm text-gray-600 line-clamp-2 mb-3">{lead.body}</p>

          {/* Product Tags */}
          {lead.product_type && lead.product_type.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {lead.product_type.slice(0, 5).map((product) => (
                <span key={product} className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded">
                  {product}
                </span>
              ))}
              {lead.product_type.length > 5 && (
                <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                  +{lead.product_type.length - 5} more
                </span>
              )}
            </div>
          )}
        </div>

        {/* Right Side - Quality Score */}
        <div className="ml-4 text-center">
          <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-lg p-3 min-w-[80px]">
            <div className="text-2xl font-bold">{lead.lead_quality_score}</div>
            <div className="text-xs opacity-80">Quality</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function LeadDetailModal({ lead, timeline, onClose }: LeadDetailModalProps): JSX.Element {
  const handleBackdropClick = (e: MouseEvent<HTMLDivElement>): void => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={handleBackdropClick}
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between bg-gradient-to-r from-blue-500 to-blue-600 text-white">
          <div>
            <h2 className="text-2xl font-bold">{lead.sender_name || lead.sender_email}</h2>
            <p className="text-blue-100 text-sm">Lead #{lead.id}</p>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:bg-white hover:bg-opacity-20 rounded-full p-2 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(90vh-80px)]">
          {/* Lead Details */}
          <div className="p-6 space-y-4 border-b border-gray-200 bg-gray-50">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <DetailField label="Email" value={lead.sender_email} />
              <DetailField label="Company" value={lead.company_name || 'N/A'} />
              <DetailField label="Quality Score" value={`${lead.lead_quality_score}/10`} />
              <DetailField label="Priority" value={lead.response_priority || 'N/A'} />
              <DetailField label="Status" value={(lead.lead_status as string)?.replace(/_/g, ' ') || 'N/A'} />
              <DetailField label="Received" value={new Date(lead.received_at).toLocaleString()} />
            </div>

            {lead.product_type && lead.product_type.length > 0 && (
              <div>
                <div className="text-sm font-medium text-gray-700 mb-2">Products Interested:</div>
                <div className="flex flex-wrap gap-2">
                  {lead.product_type.map((product) => (
                    <span key={product} className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                      {product}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {lead.certifications_requested && lead.certifications_requested.length > 0 && (
              <div>
                <div className="text-sm font-medium text-gray-700 mb-2">Certifications Needed:</div>
                <div className="flex flex-wrap gap-2">
                  {lead.certifications_requested.map((cert) => (
                    <span key={cert} className="px-3 py-1 bg-green-100 text-green-800 text-sm rounded-full">
                      {cert}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Original Message */}
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Original Message</h3>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm font-medium text-gray-700 mb-2">{lead.subject}</div>
              <p className="text-sm text-gray-600 whitespace-pre-wrap">{lead.body}</p>
            </div>
          </div>

          {/* Conversation Timeline */}
          {timeline && timeline.timeline && timeline.timeline.length > 0 && (
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <MessageCircle className="w-5 h-5" />
                Conversation Timeline
              </h3>
              <div className="space-y-4">
                {timeline.timeline.map((event, idx) => (
                  <TimelineEventComponent key={idx} event={event} />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function DetailField({ label, value }: DetailFieldProps): JSX.Element {
  return (
    <div>
      <div className="text-xs font-medium text-gray-500 uppercase">{label}</div>
      <div className="text-sm font-semibold text-gray-900 mt-1">{value}</div>
    </div>
  );
}

function TimelineEventComponent({ event }: TimelineEventProps): JSX.Element {
  const getEventIcon = (type: string): JSX.Element => {
    switch (type) {
      case 'lead_created':
        return <Star className="w-4 h-4 text-blue-600" />;
      case 'email_received':
      case 'email_sent':
        return <Mail className="w-4 h-4 text-green-600" />;
      case 'draft_created':
      case 'draft_approved':
        return <MessageCircle className="w-4 h-4 text-purple-600" />;
      default:
        return <MessageCircle className="w-4 h-4 text-gray-600" />;
    }
  };

  return (
    <div className="flex gap-3">
      <div className="bg-gray-100 rounded-full p-2 h-fit">
        {getEventIcon(event.event_type)}
      </div>
      <div className="flex-1">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-medium text-gray-900">
            {event.event_type?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </span>
          <span className="text-xs text-gray-500">
            {new Date(event.timestamp).toLocaleString()}
          </span>
        </div>
        {event.description && (
          <p className="text-sm text-gray-600">{event.description}</p>
        )}
        {event.email_subject && (
          <p className="text-sm text-gray-700 font-medium mt-1">{event.email_subject}</p>
        )}
        {event.email_body && (
          <p className="text-sm text-gray-600 mt-1 line-clamp-3">{event.email_body}</p>
        )}
      </div>
    </div>
  );
}
