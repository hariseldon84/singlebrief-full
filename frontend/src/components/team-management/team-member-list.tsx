'use client'

import React, { useState, useEffect } from 'react'
import { 
  Users, 
  Search, 
  Filter, 
  Plus, 
  Edit, 
  MoreVertical, 
  Mail, 
  Slack, 
  MessageSquare,
  UserCheck,
  UserX,
  Clock
} from 'lucide-react'

interface TeamMember {
  id: string
  user_id: string
  custom_role?: string
  custom_designation?: string
  bio?: string
  location?: string
  status: 'active' | 'inactive' | 'on_leave' | 'pending_invitation'
  current_workload: number
  capacity_percentage: number
  query_contact_preference: 'in_app' | 'email' | 'slack' | 'teams'
  urgent_contact_preference: 'in_app' | 'email' | 'slack' | 'teams'
  response_time_expectation_hours: number
  total_queries_received: number
  total_queries_responded: number
  average_response_time_hours: number
  response_quality_score: number
  slack_verified: boolean
  teams_verified: boolean
  email_verified: boolean
  expertise_tags?: Array<{
    id: string
    name: string
    display_name: string
    color?: string
    category: string
  }>
  created_at: string
  updated_at: string
}

interface SearchFilters {
  search_query?: string
  statuses?: Array<'active' | 'inactive' | 'on_leave' | 'pending_invitation'>
  min_capacity?: number
  max_capacity?: number
  slack_verified?: boolean
  teams_verified?: boolean
  email_verified?: boolean
  sort_by?: 'name' | 'created_at' | 'response_quality_score'
  sort_order?: 'asc' | 'desc'
}

interface TeamMemberListProps {
  onAddMember?: () => void
  onEditMember?: (member: TeamMember) => void
}

export function TeamMemberList({ onAddMember, onEditMember }: TeamMemberListProps) {
  const [members, setMembers] = useState<TeamMember[]>([])
  const [loading, setLoading] = useState(true)
  const [searchFilters, setSearchFilters] = useState<SearchFilters>({
    sort_by: 'created_at',
    sort_order: 'desc'
  })
  const [showFilters, setShowFilters] = useState(false)
  const [selectedMembers, setSelectedMembers] = useState<Set<string>>(new Set())

  // Fetch team members
  const fetchMembers = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      
      if (searchFilters.search_query) {
        params.append('search_query', searchFilters.search_query)
      }
      if (searchFilters.statuses?.length) {
        searchFilters.statuses.forEach(status => params.append('statuses', status))
      }
      if (searchFilters.min_capacity !== undefined) {
        params.append('min_capacity', searchFilters.min_capacity.toString())
      }
      if (searchFilters.max_capacity !== undefined) {
        params.append('max_capacity', searchFilters.max_capacity.toString())
      }
      if (searchFilters.slack_verified !== undefined) {
        params.append('slack_verified', searchFilters.slack_verified.toString())
      }
      if (searchFilters.teams_verified !== undefined) {
        params.append('teams_verified', searchFilters.teams_verified.toString())
      }
      if (searchFilters.email_verified !== undefined) {
        params.append('email_verified', searchFilters.email_verified.toString())
      }
      if (searchFilters.sort_by) {
        params.append('sort_by', searchFilters.sort_by)
      }
      if (searchFilters.sort_order) {
        params.append('sort_order', searchFilters.sort_order)
      }

      const response = await fetch(`/api/v1/team-management/members/search?${params.toString()}`, {
        headers: {
          'Authorization': `Bearer ${JSON.parse(localStorage.getItem('sb_tokens') || '{}')?.access_token || ''}` // Get correct token
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        setMembers(data.results || [])
      }
    } catch (error) {
      console.error('Failed to fetch team members:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchMembers()
  }, [searchFilters])

  const getStatusBadge = (status: 'active' | 'inactive' | 'on_leave' | 'pending_invitation') => {
    const statusStyles: Record<'active' | 'inactive' | 'on_leave' | 'pending_invitation', string> = {
      active: 'bg-green-100 text-green-800',
      inactive: 'bg-gray-100 text-gray-800', 
      on_leave: 'bg-yellow-100 text-yellow-800',
      pending_invitation: 'bg-blue-100 text-blue-800'
    }
    
    return (
      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${statusStyles[status] || statusStyles.inactive}`}>
        {status.replace('_', ' ')}
      </span>
    )
  }

  const getWorkloadIndicator = (workload: number) => {
    const percentage = Math.round(workload * 100)
    const color = workload < 0.3 ? 'bg-green-500' : workload < 0.7 ? 'bg-yellow-500' : 'bg-red-500'
    
    return (
      <div className="flex items-center space-x-2">
        <div className="w-16 bg-gray-200 rounded-full h-2">
          <div className={`${color} h-2 rounded-full`} style={{ width: `${percentage}%` }}></div>
        </div>
        <span className="text-xs text-gray-600">{percentage}%</span>
      </div>
    )
  }

  const getContactPreferenceIcon = (preference: string) => {
    switch (preference) {
      case 'email': return <Mail className="h-4 w-4" />
      case 'slack': return <Slack className="h-4 w-4" />
      case 'teams': return <MessageSquare className="h-4 w-4" />
      default: return <Users className="h-4 w-4" />
    }
  }

  const getVerificationStatus = (member: TeamMember) => {
    const verified = []
    if (member.email_verified) verified.push('Email')
    if (member.slack_verified) verified.push('Slack')
    if (member.teams_verified) verified.push('Teams')
    
    return verified.length > 0 ? verified.join(', ') : 'None'
  }

  const handleSearchChange = (value: string) => {
    setSearchFilters(prev => ({ ...prev, search_query: value }))
  }

  const handleStatusFilter = (statuses: string[]) => {
    setSearchFilters(prev => ({ 
      ...prev, 
      statuses: statuses as Array<'active' | 'inactive' | 'on_leave' | 'pending_invitation'>
    }))
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Team Members</h1>
          <p className="text-neutral">Manage team member profiles and settings</p>
        </div>
        <div className="flex items-center space-x-3">
          <button 
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </button>
          <button 
            onClick={onAddMember}
            className="flex items-center px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary-600"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Member
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="flex items-center space-x-4">
        <div className="flex-1 relative">
          <Search className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search team members by role, skills, or bio..."
            value={searchFilters.search_query || ''}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary focus:border-transparent"
          />
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-gray-50 p-4 rounded-lg border">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Status Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
              <select 
                multiple
                className="w-full border border-gray-300 rounded-md p-2 text-sm"
                onChange={(e) => {
                  const values = Array.from(e.target.selectedOptions, option => option.value)
                  handleStatusFilter(values)
                }}
              >
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="on_leave">On Leave</option>
                <option value="pending_invitation">Pending Invitation</option>
              </select>
            </div>

            {/* Capacity Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Capacity Range</label>
              <div className="flex space-x-2">
                <input
                  type="number"
                  placeholder="Min %"
                  min="0"
                  max="100"
                  className="w-full border border-gray-300 rounded-md p-2 text-sm"
                  onChange={(e) => setSearchFilters(prev => ({ 
                    ...prev, 
                    min_capacity: e.target.value ? parseInt(e.target.value) : undefined 
                  }))}
                />
                <input
                  type="number"
                  placeholder="Max %"
                  min="0"
                  max="100"
                  className="w-full border border-gray-300 rounded-md p-2 text-sm"
                  onChange={(e) => setSearchFilters(prev => ({ 
                    ...prev, 
                    max_capacity: e.target.value ? parseInt(e.target.value) : undefined 
                  }))}
                />
              </div>
            </div>

            {/* Verification Status */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Platform Verification</label>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input 
                    type="checkbox" 
                    className="mr-2"
                    onChange={(e) => setSearchFilters(prev => ({ 
                      ...prev, 
                      slack_verified: e.target.checked ? true : undefined 
                    }))}
                  />
                  <Slack className="h-4 w-4 mr-1" />
                  Slack Verified
                </label>
                <label className="flex items-center">
                  <input 
                    type="checkbox" 
                    className="mr-2"
                    onChange={(e) => setSearchFilters(prev => ({ 
                      ...prev, 
                      teams_verified: e.target.checked ? true : undefined 
                    }))}
                  />
                  <MessageSquare className="h-4 w-4 mr-1" />
                  Teams Verified
                </label>
                <label className="flex items-center">
                  <input 
                    type="checkbox" 
                    className="mr-2"
                    onChange={(e) => setSearchFilters(prev => ({ 
                      ...prev, 
                      email_verified: e.target.checked ? true : undefined 
                    }))}
                  />
                  <Mail className="h-4 w-4 mr-1" />
                  Email Verified
                </label>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Team Members Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center">
            <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
            <p className="mt-2 text-sm text-gray-500">Loading team members...</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <input type="checkbox" className="rounded" />
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Member
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Workload
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Contact
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Performance
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Verification
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {members.map((member) => (
                  <tr key={member.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <input 
                        type="checkbox" 
                        className="rounded"
                        checked={selectedMembers.has(member.id)}
                        onChange={(e) => {
                          const newSelected = new Set(selectedMembers)
                          if (e.target.checked) {
                            newSelected.add(member.id)
                          } else {
                            newSelected.delete(member.id)
                          }
                          setSelectedMembers(newSelected)
                        }}
                      />
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <div className="h-10 w-10 bg-primary-100 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-primary">
                            {(member.custom_role || 'U')[0].toUpperCase()}
                          </span>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">
                            {member.custom_role || 'Unknown Role'}
                          </div>
                          <div className="text-sm text-gray-500">
                            {member.custom_designation || 'No designation'}
                          </div>
                          <div className="flex items-center mt-1">
                            {member.expertise_tags?.slice(0, 3).map((tag) => (
                              <span 
                                key={tag.id}
                                className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800 mr-1"
                                style={{ backgroundColor: tag.color ? `${tag.color}20` : undefined }}
                              >
                                {tag.display_name}
                              </span>
                            ))}
                            {(member.expertise_tags?.length || 0) > 3 && (
                              <span className="text-xs text-gray-400">
                                +{(member.expertise_tags?.length || 0) - 3} more
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {getStatusBadge(member.status)}
                    </td>
                    <td className="px-6 py-4">
                      <div className="space-y-1">
                        {getWorkloadIndicator(member.current_workload)}
                        <div className="text-xs text-gray-500">
                          {member.capacity_percentage}% capacity
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-2">
                        {getContactPreferenceIcon(member.query_contact_preference)}
                        <span className="text-sm text-gray-500">
                          {member.query_contact_preference}
                        </span>
                      </div>
                      <div className="flex items-center mt-1 text-xs text-gray-400">
                        <Clock className="h-3 w-3 mr-1" />
                        {member.response_time_expectation_hours}h response
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm">
                        <div className="text-gray-900">
                          {member.total_queries_responded}/{member.total_queries_received} queries
                        </div>
                        <div className="text-gray-500">
                          {member.response_quality_score.toFixed(1)} quality score
                        </div>
                        <div className="text-gray-500">
                          {member.average_response_time_hours.toFixed(1)}h avg response
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-1">
                        {member.email_verified && <UserCheck className="h-4 w-4 text-green-500" />}
                        {member.slack_verified && <Slack className="h-4 w-4 text-blue-500" />}
                        {member.teams_verified && <MessageSquare className="h-4 w-4 text-purple-500" />}
                        {!member.email_verified && !member.slack_verified && !member.teams_verified && (
                          <UserX className="h-4 w-4 text-gray-400" />
                        )}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {getVerificationStatus(member)}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-2">
                        <button 
                          onClick={() => onEditMember?.(member)}
                          className="text-gray-400 hover:text-gray-600"
                        >
                          <Edit className="h-4 w-4" />
                        </button>
                        <button className="text-gray-400 hover:text-gray-600">
                          <MoreVertical className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        
        {!loading && members.length === 0 && (
          <div className="p-8 text-center">
            <Users className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No team members found</h3>
            <p className="text-gray-500 mb-4">Get started by adding your first team member.</p>
            <button 
              onClick={onAddMember}
              className="inline-flex items-center px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary-600"
            >
              <Plus className="h-4 w-4 mr-2" />
              Add Team Member
            </button>
          </div>
        )}
      </div>

      {/* Bulk Actions */}
      {selectedMembers.size > 0 && (
        <div className="fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-white border border-gray-200 rounded-lg shadow-lg px-6 py-3">
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-700">
              {selectedMembers.size} member{selectedMembers.size > 1 ? 's' : ''} selected
            </span>
            <div className="flex items-center space-x-2">
              <button className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-md">
                Export
              </button>
              <button className="px-3 py-1 text-sm bg-blue-100 hover:bg-blue-200 text-blue-700 rounded-md">
                Send Query
              </button>
              <button className="px-3 py-1 text-sm bg-red-100 hover:bg-red-200 text-red-700 rounded-md">
                Change Status
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}