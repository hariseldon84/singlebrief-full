'use client'

import React, { useState } from 'react'
import { TeamMemberList } from '../../src/components/team-management/team-member-list'
import { TeamMemberForm } from '../../src/components/team-management/team-member-form'
import { useClerkOrganization } from '../../src/hooks/use-clerk-organization'
import { OrganizationSwitcher } from '@clerk/nextjs'
import { useAuth } from '@clerk/nextjs'

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
  const { organization, user, isLoaded } = useClerkOrganization()
  const { getToken } = useAuth()
  const [showMemberForm, setShowMemberForm] = useState(false)
  const [editingMember, setEditingMember] = useState<TeamMember | null>(null)
  const [currentTeamId] = useState(() => {
    // Use the organization ID from Clerk
    return organization?.id || 'default-team-id'
  })

  // Remove client-side redirect as AppLayoutWrapper handles this

  const handleCreateMember = () => {
    setEditingMember(null)
    setShowMemberForm(true)
  }

  const handleEditMember = (member: TeamMember) => {
    setEditingMember(member)
    setShowMemberForm(true)
  }

  // Convert TeamMember to simplified form data for Clerk invitations (Story 16.1)
  const convertToFormData = (member: TeamMember) => {
    return {
      name: member.user_id, // TODO: Get actual name from Clerk user data
      email: '', // TODO: Get email from Clerk user data  
      job_title: member.custom_role || '',
      department: '', // TODO: Get department from team member data
      location: member.location || '',
      timezone: '', // TODO: Get timezone from team member data
      bio: member.bio || '',
      send_invitation: false, // Don't send again for existing members
      invitation_message: ''
    }
  }

  const handleSaveMember = async (memberData: any) => {
    try {
      // Get authentication token from Clerk
      const accessToken = await getToken()

      if (!accessToken) {
        throw new Error('No authentication token found. Please log in again.')
      }

      const url = editingMember 
        ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1/team-management/members/${editingMember.id}`
        : `${process.env.NEXT_PUBLIC_API_URL}/api/v1/team-management/members`
      
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
        const savedMember = await response.json()
        
        // Send Clerk invitation if requested and this is a new member (Story 16.1)
        if (!editingMember && memberData.send_invitation) {
          try {
            const invitationResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/team-management/clerk-invitations`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${accessToken}`
              },
              body: JSON.stringify({
                email: memberData.email,
                first_name: memberData.name.split(' ')[0],
                last_name: memberData.name.split(' ').slice(1).join(' ') || memberData.name.split(' ')[0],
                role: 'basic_member',
                redirect_url: `${window.location.origin}/auth/callback`,
                message: memberData.invitation_message
              })
            })

            const inviteResult = await invitationResponse.json()
            
            if (inviteResult.success) {
              alert(`✅ Success!\n\nTeam member profile created and Clerk invitation sent to ${memberData.email}.\n\nThey will receive a secure signup link and automatically join your organization.`)
            } else {
              alert(`⚠️ Warning\n\nTeam member profile was created, but Clerk invitation failed:\n\n${inviteResult.error || 'Unknown error'}\n\nYou may need to send the invitation manually.`)
            }
          } catch (inviteError) {
            console.error('Failed to send Clerk invitation:', inviteError)
            alert(`⚠️ Warning\n\nTeam member profile was created, but Clerk invitation failed to send to ${memberData.email}.\n\nPlease check the backend logs and try again.`)
          }
        } else {
          alert(editingMember ? '✅ Team member updated successfully!' : '✅ Team member profile created successfully!')
        }
        
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
      const message = error instanceof Error ? error.message : 'Unknown error occurred'
      alert(`Failed to save team member: ${message}`)
    }
  }

  const handleCloseForm = () => {
    setShowMemberForm(false)
    setEditingMember(null)
  }

  // Show loading while organization data is being loaded
  if (!isLoaded) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading team data...</p>
        </div>
      </div>
    )
  }

  // If no organization, show organization switcher
  if (!organization) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center max-w-md">
          <h1 className="text-xl font-bold text-gray-900 mb-4">Create an Organization</h1>
          <p className="text-gray-600 mb-6">You need to create or join an organization to manage team members.</p>
          <OrganizationSwitcher 
            createOrganizationMode="navigation"
            createOrganizationUrl="/auth/create-organization"
            afterCreateOrganizationUrl="/team-management"
          />
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
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
  )
}