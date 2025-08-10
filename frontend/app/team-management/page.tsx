'use client'

import React, { useState } from 'react'
import { TeamMemberList } from '../../src/components/team-management/team-member-list'
import { TeamMemberForm } from '../../src/components/team-management/team-member-form'

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

export default function TeamManagementPage() {
  const [showMemberForm, setShowMemberForm] = useState(false)
  const [editingMember, setEditingMember] = useState<TeamMember | null>(null)
  const [currentTeamId] = useState(() => {
    // For now, get the organization ID and use a default team structure
    const userStr = localStorage.getItem('sb_user')
    const user = userStr ? JSON.parse(userStr) : null
    return user?.organization_id || 'default-team-id'
  })

  const handleCreateMember = () => {
    setEditingMember(null)
    setShowMemberForm(true)
  }

  const handleEditMember = (member: TeamMember) => {
    setEditingMember(member)
    setShowMemberForm(true)
  }

  // Convert TeamMember to TeamMemberFormData for the form
  const convertToFormData = (member: TeamMember) => {
    return {
      user_id: member.user_id,
      team_id: currentTeamId,
      custom_role: member.custom_role,
      custom_designation: member.custom_designation,
      bio: member.bio,
      location: member.location,
      status: member.status,
      current_workload: member.current_workload,
      capacity_percentage: member.capacity_percentage,
      query_contact_preference: member.query_contact_preference,
      urgent_contact_preference: member.urgent_contact_preference,
      notification_preference: member.query_contact_preference, // Default fallback
      response_time_expectation_hours: member.response_time_expectation_hours,
      working_days: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'], // Default
      expertise_tags: member.expertise_tags?.map(tag => ({
        tag_id: tag.id,
        proficiency_level: 3 // Default proficiency level
      })) || [],
      platform_accounts: [] // Would need to fetch this data separately
    }
  }

  const handleSaveMember = async (memberData: any) => {
    try {
      // Get authentication token
      const tokensStr = localStorage.getItem('sb_tokens')
      const tokens = tokensStr ? JSON.parse(tokensStr) : null
      const accessToken = tokens?.access_token

      if (!accessToken) {
        throw new Error('No authentication token found. Please log in again.')
      }

      const url = editingMember 
        ? `/api/v1/team-management/members/${editingMember.id}`
        : '/api/v1/team-management/members'
      
      const method = editingMember ? 'PUT' : 'POST'
      
      console.log('Sending request to:', url)
      console.log('Method:', method)
      console.log('Data:', memberData)
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify(memberData)
      })

      if (response.ok) {
        setShowMemberForm(false)
        setEditingMember(null)
        // Refresh the list - you would typically use a state management solution
        window.location.reload()
      } else {
        const errorData = await response.text()
        console.error('API Error Response:', {
          status: response.status,
          statusText: response.statusText,
          body: errorData
        })
        throw new Error(`API Error: ${response.status} ${response.statusText} - ${errorData}`)
      }
    } catch (error) {
      console.error('Error saving team member:', error)
      alert(`Failed to save team member: ${error.message}`)
    }
  }

  const handleCloseForm = () => {
    setShowMemberForm(false)
    setEditingMember(null)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <TeamMemberList 
          onAddMember={handleCreateMember}
          onEditMember={handleEditMember}
        />
        
        <TeamMemberForm
          isOpen={showMemberForm}
          onClose={handleCloseForm}
          onSave={handleSaveMember}
          member={editingMember ? convertToFormData(editingMember) : undefined}
          teamId={currentTeamId}
          isEditing={!!editingMember}
        />
      </div>
    </div>
  )
}