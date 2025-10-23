import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { analyticsAPI, leadsAPI } from '../services/api'
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { TrendingUp, Users, Mail, CheckCircle, Clock, AlertTriangle } from 'lucide-react'

const COLORS = {
  critical: '#dc2626',
  high: '#ea580c',
  medium: '#f59e0b',
  low: '#6b7280',
  primary: '#3b82f6',
  success: '#10b981',
  warning: '#f59e0b',
}

export default function Analytics() {
  const [timeRange, setTimeRange] = useState(7)

  // Fetch analytics overview
  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ['analytics', 'overview', timeRange],
    queryFn: () => analyticsAPI.getOverview({ days: timeRange }),
  })

  // Fetch product trends
  const { data: trends, isLoading: trendsLoading } = useQuery({
    queryKey: ['analytics', 'product-trends', timeRange],
    queryFn: () => analyticsAPI.getProductTrends({ days: timeRange }),
  })

  // Fetch all leads for additional metrics
  const { data: allLeads } = useQuery({
    queryKey: ['leads', 'all'],
    queryFn: () => leadsAPI.getAll({ limit: 1000 }),
  })

  const analytics = overview?.data || {}
  const productTrends = trends?.data?.trends || []
  const leads = allLeads?.data || []

  // Calculate priority distribution
  const priorityData = [
    { name: 'Critical', value: analytics.leads_by_priority?.critical || 0, color: COLORS.critical },
    { name: 'High', value: analytics.leads_by_priority?.high || 0, color: COLORS.high },
    { name: 'Medium', value: analytics.leads_by_priority?.medium || 0, color: COLORS.medium },
    { name: 'Low', value: analytics.leads_by_priority?.low || 0, color: COLORS.low },
  ].filter(item => item.value > 0)

  // Calculate product type distribution
  const productTypeMap = {}
  leads.forEach(lead => {
    if (lead.product_type && Array.isArray(lead.product_type)) {
      lead.product_type.forEach(product => {
        productTypeMap[product] = (productTypeMap[product] || 0) + 1
      })
    }
  })
  const productTypeData = Object.entries(productTypeMap)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 10)

  // Calculate quality score distribution
  const qualityDistribution = [
    { range: '9-10 (Excellent)', count: leads.filter(l => l.lead_quality_score >= 9).length },
    { range: '7-8 (Good)', count: leads.filter(l => l.lead_quality_score >= 7 && l.lead_quality_score < 9).length },
    { range: '5-6 (Medium)', count: leads.filter(l => l.lead_quality_score >= 5 && l.lead_quality_score < 7).length },
    { range: '1-4 (Low)', count: leads.filter(l => l.lead_quality_score >= 1 && l.lead_quality_score < 5).length },
  ]

  // Calculate leads over time (daily)
  const leadsOverTime = {}
  leads.forEach(lead => {
    if (lead.received_at) {
      const date = new Date(lead.received_at).toISOString().split('T')[0]
      leadsOverTime[date] = (leadsOverTime[date] || 0) + 1
    }
  })
  const timelineData = Object.entries(leadsOverTime)
    .map(([date, count]) => ({ date, count }))
    .sort((a, b) => a.date.localeCompare(b.date))
    .slice(-30) // Last 30 days

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-600 mt-1">Business intelligence and market insights</p>
        </div>

        {/* Time Range Selector */}
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">Time Range:</label>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(Number(e.target.value))}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value={7}>Last 7 days</option>
            <option value={14}>Last 14 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Leads"
          value={analytics.total_leads || 0}
          icon={<Users className="w-6 h-6" />}
          color="blue"
        />
        <MetricCard
          title="Avg Quality Score"
          value={analytics.avg_quality_score?.toFixed(1) || '0.0'}
          subtitle="/10"
          icon={<TrendingUp className="w-6 h-6" />}
          color="green"
        />
        <MetricCard
          title="Approval Rate"
          value={`${analytics.approval_rate?.toFixed(0) || 0}%`}
          icon={<CheckCircle className="w-6 h-6" />}
          color="purple"
        />
        <MetricCard
          title="Pending Review"
          value={analytics.pending_drafts || 0}
          icon={<Clock className="w-6 h-6" />}
          color="orange"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Priority Distribution */}
        <ChartCard title="Leads by Priority">
          {priorityData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={priorityData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {priorityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[300px] flex items-center justify-center text-gray-500">
              No priority data available
            </div>
          )}
        </ChartCard>

        {/* Quality Score Distribution */}
        <ChartCard title="Lead Quality Distribution">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={qualityDistribution}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="range" angle={-15} textAnchor="end" height={80} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill={COLORS.primary} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Top Product Types */}
        <ChartCard title="Top 10 Product Types">
          {productTypeData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={productTypeData} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" width={120} />
                <Tooltip />
                <Bar dataKey="value" fill={COLORS.success} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[300px] flex items-center justify-center text-gray-500">
              No product data available
            </div>
          )}
        </ChartCard>

        {/* Leads Over Time */}
        <ChartCard title="Leads Timeline (Last 30 Days)">
          {timelineData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={timelineData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" angle={-45} textAnchor="end" height={80} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="count" stroke={COLORS.primary} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[300px] flex items-center justify-center text-gray-500">
              No timeline data available
            </div>
          )}
        </ChartCard>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Recent Activity</h2>
        </div>
        <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
          {analytics.recent_activity && analytics.recent_activity.length > 0 ? (
            analytics.recent_activity.map((activity, idx) => (
              <div key={idx} className="px-6 py-4 hover:bg-gray-50 flex items-center gap-4">
                <div className="bg-blue-100 rounded-full p-2">
                  <Mail className="w-4 h-4 text-blue-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{activity.email}</p>
                  <p className="text-xs text-gray-500">
                    Lead #{activity.id} • Quality: {activity.score}/10
                  </p>
                </div>
                <div className="text-xs text-gray-500">
                  {new Date(activity.timestamp).toLocaleString()}
                </div>
              </div>
            ))
          ) : (
            <div className="px-6 py-8 text-center text-gray-500">
              No recent activity
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function MetricCard({ title, value, subtitle, icon, color = 'blue' }) {
  const colorClasses = {
    blue: 'from-blue-500 to-blue-600',
    green: 'from-green-500 to-green-600',
    purple: 'from-purple-500 to-purple-600',
    orange: 'from-orange-500 to-orange-600',
  }

  return (
    <div className={`bg-gradient-to-br ${colorClasses[color]} rounded-lg shadow-lg p-6 text-white`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-white text-opacity-80 text-sm font-medium">{title}</p>
          <p className="text-3xl font-bold mt-2">
            {value}
            {subtitle && <span className="text-lg ml-1">{subtitle}</span>}
          </p>
        </div>
        <div className="bg-white bg-opacity-20 rounded-full p-3">
          {icon}
        </div>
      </div>
    </div>
  )
}

function ChartCard({ title, children }) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      {children}
    </div>
  )
}
