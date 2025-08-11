/**
 * Profile Settings Component
 */

'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Save, X, ExternalLink } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useUser, useOrganization } from '@clerk/nextjs'
import { toast } from 'react-hot-toast'

const profileSchema = z.object({
  title: z.string().optional(),
  department: z.string().optional(),
  location: z.string().optional(),
  timezone: z.string().optional(),
  bio: z.string().optional(),
})

type ProfileFormData = z.infer<typeof profileSchema>

export function ProfileSettings() {
  const { user } = useUser()
  const { organization } = useOrganization()
  const [isEditing, setIsEditing] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    reset,
  } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      title: '',
      department: '',
      location: '',
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      bio: '',
    },
  })


  const onSubmit = async (data: ProfileFormData) => {
    try {
      // Simulate API call for non-Clerk fields
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Update only editable fields (Job Title, Department, etc.)
      // Clerk data (name, email, org) is managed by Clerk
      
      setIsEditing(false)
      toast.success('Profile updated successfully')
    } catch (error) {
      toast.error('Failed to update profile')
    }
  }

  const handleCancel = () => {
    reset()
    setIsEditing(false)
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-gray-900">Profile Information</h2>
        <p className="text-sm text-gray-600 mt-1">
          Update your personal information and profile details
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Avatar Section - Clerk Managed */}
        <div className="flex items-center space-x-6">
          <div className="relative">
            <div className="h-20 w-20 rounded-full overflow-hidden bg-primary-100">
              {user?.imageUrl ? (
                <img
                  src={user.imageUrl}
                  alt="Profile"
                  className="h-full w-full object-cover"
                />
              ) : (
                <div className="h-full w-full flex items-center justify-center">
                  <span className="text-2xl font-medium text-primary">
                    {user?.firstName?.[0]}{user?.lastName?.[0]}
                  </span>
                </div>
              )}
            </div>
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900">Profile Photo</p>
                <p className="text-xs text-gray-500 mt-1">
                  Managed by Clerk. Click to edit in Clerk profile.
                </p>
              </div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => window.open('/auth/user-profile', '_blank')}
              >
                <ExternalLink className="h-3 w-3 mr-1" />
                Edit in Clerk
              </Button>
            </div>
          </div>
        </div>

        {/* Clerk Managed Fields (Read-only) */}
        <div className="space-y-6">
          <div className="bg-gray-50 p-4 rounded-lg border">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-900">Account Information</h3>
              <p className="text-xs text-gray-500">Managed by Clerk</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  First Name
                </label>
                <div className="flex items-center space-x-2">
                  <input
                    value={user?.firstName || ''}
                    disabled
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => window.open('/auth/user-profile', '_blank')}
                  >
                    <ExternalLink className="h-3 w-3" />
                  </Button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Last Name
                </label>
                <div className="flex items-center space-x-2">
                  <input
                    value={user?.lastName || ''}
                    disabled
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => window.open('/auth/user-profile', '_blank')}
                  >
                    <ExternalLink className="h-3 w-3" />
                  </Button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address
                </label>
                <div className="flex items-center space-x-2">
                  <input
                    value={user?.primaryEmailAddress?.emailAddress || ''}
                    disabled
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => window.open('/auth/user-profile', '_blank')}
                  >
                    <ExternalLink className="h-3 w-3" />
                  </Button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Organization
                </label>
                <div className="flex items-center space-x-2">
                  <input
                    value={organization?.name || 'No organization'}
                    disabled
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => window.open('/auth/organization-profile', '_blank')}
                  >
                    <ExternalLink className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Editable Fields */}
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-gray-900">Additional Information</h3>
              <p className="text-xs text-gray-500 mt-1">These fields can be edited below</p>
            </div>
            {!isEditing && (
              <Button onClick={() => setIsEditing(true)} size="sm">
                Edit Details
              </Button>
            )}
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Job Title
            </label>
            <input
              {...register('title')}
              disabled={!isEditing}
              placeholder="e.g., Product Manager"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary disabled:bg-gray-50 disabled:text-gray-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Department
            </label>
            <input
              {...register('department')}
              disabled={!isEditing}
              placeholder="e.g., Engineering"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary disabled:bg-gray-50 disabled:text-gray-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Location
            </label>
            <input
              {...register('location')}
              disabled={!isEditing}
              placeholder="e.g., San Francisco, CA"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary disabled:bg-gray-50 disabled:text-gray-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Timezone
            </label>
            <select
              {...register('timezone')}
              disabled={!isEditing}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary disabled:bg-gray-50 disabled:text-gray-500"
            >
              <option value="America/New_York">Eastern Time</option>
              <option value="America/Chicago">Central Time</option>
              <option value="America/Denver">Mountain Time</option>
              <option value="America/Los_Angeles">Pacific Time</option>
              <option value="Europe/London">London</option>
              <option value="Europe/Paris">Paris</option>
              <option value="Asia/Tokyo">Tokyo</option>
              <option value="Asia/Shanghai">Shanghai</option>
            </select>
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Bio
            </label>
            <textarea
              {...register('bio')}
              disabled={!isEditing}
              rows={3}
              placeholder="Tell us about yourself..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary disabled:bg-gray-50 disabled:text-gray-500"
            />
          </div>
          </div>
        </div>

        {/* Action Buttons */}
        {isEditing && (
          <div className="flex items-center justify-end space-x-3 pt-6 border-t border-gray-200">
            <Button
              type="button"
              variant="outline"
              onClick={handleCancel}
              leftIcon={<X className="h-4 w-4" />}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!isDirty}
              leftIcon={<Save className="h-4 w-4" />}
            >
              Save Changes
            </Button>
          </div>
        )}
      </form>
    </div>
  )
}