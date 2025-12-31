import type { Draft, DraftStatus } from '../../types/api';

interface DraftListItemProps {
  draft: Draft;
  isSelected: boolean;
  onClick: () => void;
}

export default function DraftListItem({ draft, isSelected, onClick }: DraftListItemProps): JSX.Element {
  const getStatusColor = (status: DraftStatus | string): string => {
    const colors: Record<string, string> = {
      pending: 'bg-blue-500',
      approved: 'bg-green-500',
      rejected: 'bg-red-500',
      sent: 'bg-purple-500',
      edited: 'bg-yellow-500',
    };
    return colors[status] || colors.pending;
  };

  const getPriorityColor = (priority: string): string => {
    const colors: Record<string, string> = {
      critical: 'bg-red-100 text-red-700 border-red-300',
      high: 'bg-orange-100 text-orange-700 border-orange-300',
      medium: 'bg-yellow-100 text-yellow-700 border-yellow-300',
      low: 'bg-gray-100 text-gray-700 border-gray-300',
    };
    return colors[priority] || colors.medium;
  };

  const getRelativeTime = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div
      onClick={onClick}
      className={`
        p-5 border-b border-gray-200 cursor-pointer transition-colors
        ${isSelected
          ? 'bg-blue-50 border-l-4 border-l-blue-600'
          : 'hover:bg-gray-50 border-l-4 border-l-transparent'
        }
      `}
    >
      {/* Top row: Status dot, sender name, timestamp */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <div className={`w-2 h-2 rounded-full flex-shrink-0 ${getStatusColor(draft.status)}`} />
          <span className={`font-semibold text-gray-900 truncate ${isSelected ? 'text-blue-900' : ''}`}>
            {draft.lead?.sender_name || 'Unknown'}
          </span>
        </div>
        <span className="text-xs text-gray-500 flex-shrink-0 ml-2">
          {getRelativeTime(draft.created_at)}
        </span>
      </div>

      {/* Email and confidence score */}
      <div className="flex items-center justify-between mb-2.5">
        <span className="text-xs text-gray-600 truncate">
          {draft.lead?.sender_email}
        </span>
        <span className="text-xs font-semibold text-gray-700 flex-shrink-0 ml-2">
          {(draft.confidence_score || 0).toFixed(1)}
        </span>
      </div>

      {/* Subject line */}
      <p className="text-sm font-medium text-gray-900 truncate mb-3">
        {draft.subject_line}
      </p>

      {/* Tags: Priority and Products */}
      <div className="flex flex-wrap gap-1.5 items-center">
        {draft.lead?.response_priority && (
          <span className={`px-1.5 py-0.5 text-xs font-medium rounded border ${getPriorityColor(draft.lead.response_priority)}`}>
            {draft.lead.response_priority}
          </span>
        )}
        {draft.lead?.product_type?.slice(0, 2).map((product) => (
          <span
            key={product}
            className="px-1.5 py-0.5 bg-blue-50 text-blue-700 text-xs rounded truncate max-w-[100px]"
            title={product}
          >
            {product}
          </span>
        ))}
        {draft.lead?.product_type && draft.lead.product_type.length > 2 && (
          <span className="text-xs text-gray-500">
            +{draft.lead.product_type.length - 2}
          </span>
        )}
        {draft.flags && draft.flags.length > 0 && (
          <span className="text-xs text-yellow-600" title={draft.flags.join(', ')}>
            !
          </span>
        )}
      </div>
    </div>
  );
}
