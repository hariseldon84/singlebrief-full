'use client'

import React, { useState, useEffect } from 'react'
import { X, Save, User, Tag, Send } from 'lucide-react'

interface ExpertiseTag {
  id: string
  name: string
  display_name: string
  category: string
  color?: string
}

interface Role {
  id: string
  name: string
  display_name: string
  category: string
  seniority_level?: string
}

interface Designation {
  id: string
  name: string
  display_name: string
  hierarchy_level: number
  department?: string
}


// Simplified team member form data - matches new user profile fields
interface TeamMemberFormData {
  name: string
  email: string
  job_title: string
  department?: string
  location?: string
  timezone?: string
  bio?: string
  
  // Clerk invitation settings
  send_invitation: boolean
  invitation_message?: string
}

interface TeamMemberFormProps {
  isOpen: boolean
  onClose: () => void
  onSave: (data: TeamMemberFormData) => void
  member?: Partial<TeamMemberFormData>
  teamId: string
  isEditing?: boolean
}

export function TeamMemberForm({ 
  isOpen, 
  onClose, 
  onSave, 
  member, 
  teamId, 
  isEditing = false 
}: TeamMemberFormProps) {
  const [formData, setFormData] = useState<TeamMemberFormData>({
    name: '',
    email: '',
    job_title: '',
    department: '',
    location: '',
    timezone: '',
    bio: '',
    send_invitation: true,
    invitation_message: '',
    ...member
  })

  const [loading, setLoading] = useState(false)
  const [currentTab, setCurrentTab] = useState('basic')


  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validate required fields for Clerk invitation
    if (!formData.name.trim()) {
      alert('Name is required')
      return
    }
    if (!formData.email.trim()) {
      alert('Email is required')
      return
    }
    if (!formData.job_title.trim()) {
      alert('Job Title is required')
      return
    }
    
    setLoading(true)
    
    try {
      // Simplified submission data for Clerk-native invitations
      const submissionData = {
        ...formData
      }
      
      onSave(submissionData)
    } catch (error) {
      console.error('Failed to save team member:', error)
    } finally {
      setLoading(false)
    }
  }



  if (!isOpen) return null

  const tabs = [
    { id: 'basic', name: 'Profile Info', icon: User },
    { id: 'invitation', name: 'Clerk Invitation', icon: Send }
  ]

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75" onClick={onClose} />
        
        <div className="inline-block w-full max-w-4xl p-6 my-8 overflow-hidden text-left align-middle transition-all transform bg-white shadow-xl rounded-lg">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900">
              {isEditing ? 'Edit Team Member' : 'Add Team Member'}
            </h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <X className="h-6 w-6" />
            </button>
          </div>

          {/* Tabs */}
          <div className="border-b border-gray-200 mb-6">
            <nav className="-mb-px flex space-x-8">
              {tabs.map((tab) => {
                const Icon = tab.icon
                return (
                  <button
                    key={tab.id}
                    onClick={() => setCurrentTab(tab.id)}
                    className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center ${
                      currentTab === tab.id
                        ? 'border-primary text-primary'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <Icon className="h-4 w-4 mr-2" />
                    {tab.name}
                  </button>
                )
              })}
            </nav>
          </div>

          <form onSubmit={handleSubmit}>
            {/* Profile Info Tab - Matches new user profile fields */}
            {currentTab === 'basic' && (
              <div className="space-y-6">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                  <h3 className="text-sm font-medium text-blue-900 mb-2">Story 16.1: Clerk-Native Team Invitations</h3>
                  <p className="text-sm text-blue-700">
                    Team members will be invited via Clerk's secure authentication system. These profile fields match what new users fill out when joining.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Name */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Full Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.name}
                      onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary focus:border-transparent"
                      placeholder="Enter full name"
                    />
                  </div>

                  {/* Email */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Email Address <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="email"
                      required
                      value={formData.email}
                      onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary focus:border-transparent"
                      placeholder="Enter email address for Clerk invitation"
                    />
                  </div>

                  {/* Job Title */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Job Title <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.job_title}
                      onChange={(e) => setFormData(prev => ({ ...prev, job_title: e.target.value }))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary focus:border-transparent"
                      placeholder="e.g., Senior Frontend Developer, Product Manager"
                    />
                  </div>

                  {/* Department */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Department
                    </label>
                    <input
                      type="text"
                      value={formData.department || ''}
                      onChange={(e) => setFormData(prev => ({ ...prev, department: e.target.value }))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary focus:border-transparent"
                      placeholder="e.g., Engineering, Marketing, Sales"
                    />
                  </div>

                  {/* Location */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Location
                    </label>
                    <input
                      type="text"
                      value={formData.location || ''}
                      onChange={(e) => setFormData(prev => ({ ...prev, location: e.target.value }))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary focus:border-transparent"
                      placeholder="City, Country"
                    />
                  </div>

                  {/* Timezone */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Timezone
                    </label>
                    <select
                      value={formData.timezone || ''}
                      onChange={(e) => setFormData(prev => ({ ...prev, timezone: e.target.value }))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary focus:border-transparent"
                    >
                      <option value="">Select timezone</option>
                      <option value="America/New_York">Eastern Time (ET)</option>
                      <option value="America/Chicago">Central Time (CT)</option>
                      <option value="America/Denver">Mountain Time (MT)</option>
                      <option value="America/Los_Angeles">Pacific Time (PT)</option>
                      <option value="Europe/London">London (GMT)</option>
                      <option value="Europe/Paris">Central European Time</option>
                      <option value="Asia/Tokyo">Japan Standard Time</option>
                      <option value="Asia/Shanghai">China Standard Time</option>
                      <option value="Asia/Kolkata">India Standard Time</option>
                    </select>
                  </div>
                </div>

                {/* Bio */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Bio (Optional)
                  </label>
                  <textarea
                    value={formData.bio || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, bio: e.target.value }))}
                    rows={3}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary focus:border-transparent"
                    placeholder="Brief background or additional context about this team member"
                  />
                </div>
              </div>
            )}




            {/* Clerk Invitation Tab */}
            {currentTab === 'invitation' && (
              <div className="space-y-6">
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <h3 className="text-sm font-medium text-green-900 mb-2">✅ Clerk-Native Team Invitation (Story 16.1)</h3>
                  <p className="text-sm text-green-700">
                    This team member will receive a secure Clerk invitation email and automatically join your organization. They'll access intelligence conversations through the SingleBrief platform only.
                  </p>
                </div>

                <div>
                  <div className="flex items-center space-x-3 mb-4">
                    <input
                      type="checkbox"
                      id="send_invitation"
                      checked={formData.send_invitation || false}
                      onChange={(e) => setFormData(prev => ({ ...prev, send_invitation: e.target.checked }))}
                      className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
                    />
                    <label htmlFor="send_invitation" className="text-sm font-medium text-gray-700">
                      ✉️ Send Clerk invitation immediately
                    </label>
                  </div>
                  
                  {formData.send_invitation && (
                    <div className="ml-7">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Welcome Message (Optional)
                      </label>
                      <textarea
                        value={formData.invitation_message || ''}
                        onChange={(e) => setFormData(prev => ({ ...prev, invitation_message: e.target.value }))}
                        rows={3}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary focus:border-transparent"
                        placeholder={`Hi [Name],\n\nWelcome to our team! You've been invited to join SingleBrief where you'll help provide intelligence insights as ${formData.job_title || '[your job title]'}.\n\nLooking forward to working with you!`}
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        This personal message will be included in the Clerk invitation email.
                      </p>
                    </div>
                  )}
                </div>

                <div className="border border-blue-200 rounded-lg p-4 bg-blue-50">
                  <h4 className="text-sm font-medium text-blue-900 mb-3">🔐 What happens next:</h4>
                  <div className="space-y-2">
                    <div className="flex items-start space-x-3">
                      <span className="text-blue-600 font-semibold text-sm">1.</span>
                      <div>
                        <p className="text-sm text-blue-800"><strong>Secure Invitation:</strong> They receive a Clerk-generated email with signup link</p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <span className="text-blue-600 font-semibold text-sm">2.</span>
                      <div>
                        <p className="text-sm text-blue-800"><strong>Organization Join:</strong> Automatic membership in your team's organization</p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <span className="text-blue-600 font-semibold text-sm">3.</span>
                      <div>
                        <p className="text-sm text-blue-800"><strong>Intelligence Access:</strong> Participate in in-app intelligence conversations only</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-red-900 mb-2">⚠️ Story 16.1 Changes</h4>
                  <p className="text-xs text-red-700">
                    <strong>Email-only responses are no longer supported.</strong> All team members must join the SingleBrief platform to participate in intelligence conversations via in-app chat. Platform accounts and external communication preferences have been removed.
                  </p>
                </div>
              </div>
            )}


            {/* Form Actions */}
            <div className="flex items-center justify-end space-x-3 pt-6 border-t">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex items-center px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary-600 disabled:opacity-50"
              >
                <Save className="h-4 w-4 mr-2" />
                {loading ? 'Saving...' : (isEditing ? 'Update Member' : 'Create Member')}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}