'use client'

import React, { useState, useEffect } from 'react'
import { X, Save, User, MapPin, Clock, Mail, Phone, Tag } from 'lucide-react'

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

interface PlatformAccount {
  platform_type: 'slack' | 'teams' | 'email'
  platform_user_id: string
  platform_username?: string
  platform_display_name?: string
  platform_email?: string
  workspace_id?: string
  workspace_name?: string
}

interface TeamMemberFormData {
  name: string
  email: string
  team_id: string
  role: string
  designation?: string
  
  // Profile information
  profile_photo_url?: string
  bio?: string
  location?: string
  timezone?: string
  
  // Contact information
  work_phone?: string
  mobile_phone?: string
  
  // Status and availability
  status: 'active' | 'inactive' | 'on_leave' | 'pending_invitation'
  current_workload: number
  
  // Contact preferences
  query_contact_preference: 'in_app' | 'email' | 'slack' | 'teams'
  urgent_contact_preference: 'in_app' | 'email' | 'slack' | 'teams'
  notification_preference: 'in_app' | 'email' | 'slack' | 'teams'
  
  // Communication settings
  working_hours_start?: string
  working_hours_end?: string
  working_days: string[]
  
  // Admin notes
  notes?: string
  
  // Expertise tags
  expertise_tags: Array<{
    tag_id: string
    proficiency_level: number
  }>
  
  // Platform accounts
  platform_accounts: PlatformAccount[]
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
    team_id: teamId,
    role: '',
    status: 'active',
    current_workload: 0.5,
    query_contact_preference: 'in_app',
    urgent_contact_preference: 'email',
    notification_preference: 'email',
    working_days: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
    expertise_tags: [],
    platform_accounts: [],
    ...member
  })

  const [userTags, setUserTags] = useState<string[]>([])
  const [tagInput, setTagInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [currentTab, setCurrentTab] = useState('basic')

  // Initialize with member's existing tags if editing
  useEffect(() => {
    if (isOpen && member?.expertise_tags) {
      const existingTags = member.expertise_tags.map((tag, index) => `tag-${index}`)
      setUserTags(existingTags)
    } else {
      setUserTags([])
    }
  }, [isOpen, member])

  const handleAddTag = () => {
    if (tagInput.trim() && !userTags.includes(tagInput.trim())) {
      setUserTags(prev => [...prev, tagInput.trim()])
      setTagInput('')
    }
  }

  const handleRemoveTag = (tagToRemove: string) => {
    setUserTags(prev => prev.filter(tag => tag !== tagToRemove))
  }

  const handleTagInputKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleAddTag()
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validate required fields
    if (!formData.name.trim()) {
      alert('Name is required')
      return
    }
    if (!formData.email.trim()) {
      alert('Email is required')
      return
    }
    if (!formData.role.trim()) {
      alert('Role is required')
      return
    }
    if (userTags.length === 0) {
      alert('At least one expertise tag is required')
      return
    }
    
    setLoading(true)
    
    try {
      // Convert user tags to expertise_tags format
      const expertiseTags = userTags.map((tag, index) => ({
        tag_id: `user-tag-${index}`,
        tag_name: tag,
        proficiency_level: 3 // Default proficiency
      }))
      
      const submissionData = {
        ...formData,
        expertise_tags: expertiseTags
      }
      
      onSave(submissionData)
    } catch (error) {
      console.error('Failed to save team member:', error)
    } finally {
      setLoading(false)
    }
  }


  const handleWorkingDayToggle = (day: string) => {
    const newDays = formData.working_days.includes(day)
      ? formData.working_days.filter(d => d !== day)
      : [...formData.working_days, day]
    
    setFormData(prev => ({ ...prev, working_days: newDays }))
  }

  const addPlatformAccount = (type: 'slack' | 'teams' | 'email') => {
    const newAccount: PlatformAccount = {
      platform_type: type,
      platform_user_id: '',
      platform_username: '',
      platform_email: type === 'email' ? '' : undefined
    }
    
    setFormData(prev => ({
      ...prev,
      platform_accounts: [...prev.platform_accounts, newAccount]
    }))
  }

  const updatePlatformAccount = (index: number, field: keyof PlatformAccount, value: string) => {
    setFormData(prev => ({
      ...prev,
      platform_accounts: prev.platform_accounts.map((account, i) =>
        i === index ? { ...account, [field]: value } : account
      )
    }))
  }

  const removePlatformAccount = (index: number) => {
    setFormData(prev => ({
      ...prev,
      platform_accounts: prev.platform_accounts.filter((_, i) => i !== index)
    }))
  }

  if (!isOpen) return null

  const tabs = [
    { id: 'basic', name: 'Basic Info', icon: User },
    { id: 'contact', name: 'Contact & Preferences', icon: Mail },
    { id: 'skills', name: 'Skills & Tags', icon: Tag },
    { id: 'platforms', name: 'Platform Accounts', icon: Phone }
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
            {/* Basic Info Tab */}
            {currentTab === 'basic' && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Name */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Name <span className="text-red-500">*</span>
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
                      Email <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="email"
                      required
                      value={formData.email}
                      onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary focus:border-transparent"
                      placeholder="Enter email address"
                    />
                  </div>

                  {/* Status */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Status
                    </label>
                    <select
                      value={formData.status}
                      onChange={(e) => setFormData(prev => ({ 
                        ...prev, 
                        status: e.target.value as any 
                      }))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary focus:border-transparent"
                    >
                      <option value="active">Active</option>
                      <option value="inactive">Inactive</option>
                      <option value="on_leave">On Leave</option>
                      <option value="pending_invitation">Pending Invitation</option>
                    </select>
                  </div>

                  {/* Role */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Role <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.role}
                      onChange={(e) => setFormData(prev => ({ ...prev, role: e.target.value }))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary focus:border-transparent"
                      placeholder="Enter role (e.g. Frontend Developer, Product Manager)"
                    />
                  </div>

                  {/* Designation */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Designation
                    </label>
                    <input
                      type="text"
                      value={formData.designation || ''}
                      onChange={(e) => setFormData(prev => ({ ...prev, designation: e.target.value }))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary focus:border-transparent"
                      placeholder="Enter designation (e.g. Senior, Lead, Manager)"
                    />
                  </div>
                </div>

                {/* Bio */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Bio
                  </label>
                  <textarea
                    value={formData.bio || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, bio: e.target.value }))}
                    rows={3}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary focus:border-transparent"
                    placeholder="Brief description of the team member"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Location */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Location
                    </label>
                    <div className="relative">
                      <MapPin className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                      <input
                        type="text"
                        value={formData.location || ''}
                        onChange={(e) => setFormData(prev => ({ ...prev, location: e.target.value }))}
                        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary focus:border-transparent"
                        placeholder="City, Country"
                      />
                    </div>
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

                {/* Current Workload - Used by AI Orchestrator */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Current Workload ({Math.round(formData.current_workload * 100)}%)
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={formData.current_workload}
                    onChange={(e) => setFormData(prev => ({ ...prev, current_workload: parseFloat(e.target.value) }))}
                    className="w-full"
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    Used by AI to determine availability (0% = Light, 100% = Maximum)
                  </p>
                </div>
              </div>
            )}

            {/* Contact & Preferences Tab */}
            {currentTab === 'contact' && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Work Phone */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Work Phone
                    </label>
                    <input
                      type="tel"
                      value={formData.work_phone || ''}
                      onChange={(e) => setFormData(prev => ({ ...prev, work_phone: e.target.value }))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary focus:border-transparent"
                      placeholder="+1 (555) 123-4567"
                    />
                  </div>

                  {/* Mobile Phone */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Mobile Phone
                    </label>
                    <input
                      type="tel"
                      value={formData.mobile_phone || ''}
                      onChange={(e) => setFormData(prev => ({ ...prev, mobile_phone: e.target.value }))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary focus:border-transparent"
                      placeholder="+1 (555) 123-4567"
                    />
                  </div>

                </div>

                {/* Contact Preferences */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Query Contact Preference
                    </label>
                    <select
                      value={formData.query_contact_preference}
                      onChange={(e) => setFormData(prev => ({ ...prev, query_contact_preference: e.target.value as any }))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary focus:border-transparent"
                    >
                      <option value="in_app">In App</option>
                      <option value="email">Email</option>
                      <option value="slack">Slack</option>
                      <option value="teams">Teams</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Urgent Contact Preference
                    </label>
                    <select
                      value={formData.urgent_contact_preference}
                      onChange={(e) => setFormData(prev => ({ ...prev, urgent_contact_preference: e.target.value as any }))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary focus:border-transparent"
                    >
                      <option value="in_app">In App</option>
                      <option value="email">Email</option>
                      <option value="slack">Slack</option>
                      <option value="teams">Teams</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Notification Preference
                    </label>
                    <select
                      value={formData.notification_preference}
                      onChange={(e) => setFormData(prev => ({ ...prev, notification_preference: e.target.value as any }))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary focus:border-transparent"
                    >
                      <option value="in_app">In App</option>
                      <option value="email">Email</option>
                      <option value="slack">Slack</option>
                      <option value="teams">Teams</option>
                    </select>
                  </div>
                </div>

                {/* Working Hours */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Working Hours Start
                    </label>
                    <input
                      type="time"
                      value={formData.working_hours_start || ''}
                      onChange={(e) => setFormData(prev => ({ ...prev, working_hours_start: e.target.value }))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Working Hours End
                    </label>
                    <input
                      type="time"
                      value={formData.working_hours_end || ''}
                      onChange={(e) => setFormData(prev => ({ ...prev, working_hours_end: e.target.value }))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary focus:border-transparent"
                    />
                  </div>
                </div>

                {/* Working Days */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Working Days
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].map((day) => (
                      <button
                        key={day}
                        type="button"
                        onClick={() => handleWorkingDayToggle(day)}
                        className={`px-3 py-1 rounded-md text-sm font-medium ${
                          formData.working_days.includes(day)
                            ? 'bg-primary text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        {day.charAt(0).toUpperCase() + day.slice(1, 3)}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Skills & Tags Tab */}
            {currentTab === 'skills' && (
              <div className="space-y-6">
                {/* Skills Summary */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Skills Summary
                  </label>
                  <textarea
                    value={formData.skills_summary || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, skills_summary: e.target.value }))}
                    rows={4}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary focus:border-transparent"
                    placeholder="Describe key skills, technologies, and expertise areas"
                  />
                </div>

                {/* Years of Experience */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Years of Experience
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="50"
                    value={formData.years_experience || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, years_experience: e.target.value ? parseInt(e.target.value) : undefined }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary focus:border-transparent"
                  />
                </div>

                {/* User-Defined Tags */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Expertise Tags <span className="text-red-500">*</span>
                  </label>
                  
                  {/* Tag Input */}
                  <div className="mb-3">
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={tagInput}
                        onChange={(e) => setTagInput(e.target.value)}
                        onKeyDown={handleTagInputKeyDown}
                        className="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary focus:border-transparent"
                        placeholder="Enter expertise tag (e.g., React, Python, Project Management)"
                      />
                      <button
                        type="button"
                        onClick={handleAddTag}
                        className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary-600 disabled:opacity-50"
                        disabled={!tagInput.trim()}
                      >
                        Add Tag
                      </button>
                    </div>
                    <p className="text-sm text-gray-500 mt-1">
                      Press Enter or click "Add Tag" to add expertise tags
                    </p>
                  </div>
                  
                  {/* Current Tags */}
                  <div className="border border-gray-300 rounded-md p-3 min-h-16">
                    {userTags.length === 0 ? (
                      <p className="text-gray-500 text-sm italic">No tags added yet</p>
                    ) : (
                      <div className="flex flex-wrap gap-2">
                        {userTags.map((tag, index) => (
                          <span
                            key={index}
                            className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-primary-100 text-primary-800 border border-primary-200"
                          >
                            {tag}
                            <button
                              type="button"
                              onClick={() => handleRemoveTag(tag)}
                              className="ml-2 text-primary-600 hover:text-primary-800 focus:outline-none"
                            >
                              <X className="h-4 w-4" />
                            </button>
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Platform Accounts Tab */}
            {currentTab === 'platforms' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium text-gray-900">Platform Accounts</h3>
                  <div className="flex space-x-2">
                    <button
                      type="button"
                      onClick={() => addPlatformAccount('email')}
                      className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded-md text-sm"
                    >
                      + Email
                    </button>
                    <button
                      type="button"
                      onClick={() => addPlatformAccount('slack')}
                      className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded-md text-sm"
                    >
                      + Slack
                    </button>
                    <button
                      type="button"
                      onClick={() => addPlatformAccount('teams')}
                      className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded-md text-sm"
                    >
                      + Teams
                    </button>
                  </div>
                </div>

                {formData.platform_accounts.map((account, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="text-sm font-medium text-gray-900 capitalize">
                        {account.platform_type} Account
                      </h4>
                      <button
                        type="button"
                        onClick={() => removePlatformAccount(index)}
                        className="text-red-600 hover:text-red-800 text-sm"
                      >
                        Remove
                      </button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          User ID *
                        </label>
                        <input
                          type="text"
                          required
                          value={account.platform_user_id}
                          onChange={(e) => updatePlatformAccount(index, 'platform_user_id', e.target.value)}
                          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-primary focus:border-transparent"
                          placeholder={`${account.platform_type} user ID`}
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Username
                        </label>
                        <input
                          type="text"
                          value={account.platform_username || ''}
                          onChange={(e) => updatePlatformAccount(index, 'platform_username', e.target.value)}
                          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-primary focus:border-transparent"
                          placeholder={`@username`}
                        />
                      </div>

                      {account.platform_type === 'email' && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Email Address
                          </label>
                          <input
                            type="email"
                            value={account.platform_email || ''}
                            onChange={(e) => updatePlatformAccount(index, 'platform_email', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-primary focus:border-transparent"
                            placeholder="email@example.com"
                          />
                        </div>
                      )}

                      {(account.platform_type === 'slack' || account.platform_type === 'teams') && (
                        <>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Workspace ID
                            </label>
                            <input
                              type="text"
                              value={account.workspace_id || ''}
                              onChange={(e) => updatePlatformAccount(index, 'workspace_id', e.target.value)}
                              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-primary focus:border-transparent"
                              placeholder="Workspace ID"
                            />
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Workspace Name
                            </label>
                            <input
                              type="text"
                              value={account.workspace_name || ''}
                              onChange={(e) => updatePlatformAccount(index, 'workspace_name', e.target.value)}
                              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-primary focus:border-transparent"
                              placeholder="Workspace name"
                            />
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                ))}

                {formData.platform_accounts.length === 0 && (
                  <div className="text-center py-8">
                    <Phone className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No platform accounts</h3>
                    <p className="text-gray-500 mb-4">Add platform accounts to enable multi-channel communication.</p>
                  </div>
                )}
              </div>
            )}

            {/* Admin Notes */}
            {currentTab === 'basic' && (
              <div className="border-t pt-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Admin Notes
                  </label>
                  <textarea
                    value={formData.notes || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                    rows={3}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary focus:border-transparent"
                    placeholder="Internal notes about this team member (not visible to the member)"
                  />
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