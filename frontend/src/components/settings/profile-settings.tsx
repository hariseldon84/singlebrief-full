/**
 * Profile Settings Component
 */

'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Camera, Save, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAppStore } from '@/lib/stores/app-store'
import { toast } from 'react-hot-toast'

const profileSchema = z.object({
  firstName: z.string().min(1, 'First name is required'),
  lastName: z.string().min(1, 'Last name is required'),
  email: z.string().email('Invalid email address'),
  title: z.string().optional(),
  department: z.string().optional(),
  location: z.string().optional(),
  timezone: z.string().optional(),
  bio: z.string().optional(),
})

type ProfileFormData = z.infer<typeof profileSchema>

export function ProfileSettings() {
  const { user, setUser } = useAppStore()
  const [isEditing, setIsEditing] = useState(false)
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    reset,
  } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      firstName: user?.name?.split(' ')[0] || '',
      lastName: user?.name?.split(' ')[1] || '',
      email: user?.email || '',
      title: user?.role || '',
      department: '',
      location: '',
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      bio: '',
    },
  })

  const handleAvatarChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        setAvatarPreview(e.target?.result as string)
      }
      reader.readAsDataURL(file)
    }
  }

  const onSubmit = async (data: ProfileFormData) => {
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      setUser({
        ...user!,
        name: `${data.firstName} ${data.lastName}`,
        email: data.email,
        role: data.title || '',
        avatar: avatarPreview || user?.avatar,
      })
      
      setIsEditing(false)
      toast.success('Profile updated successfully')
    } catch (error) {
      toast.error('Failed to update profile')
    }
  }

  const handleCancel = () => {
    reset()
    setAvatarPreview(null)
    setIsEditing(false)
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Profile Information</h2>
          <p className="text-sm text-gray-600 mt-1">
            Update your personal information and profile details
          </p>
        </div>
        {!isEditing && (
          <Button onClick={() => setIsEditing(true)}>
            Edit Profile
          </Button>
        )}
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Avatar Section */}
        <div className="flex items-center space-x-6">
          <div className="relative">
            <div className="h-20 w-20 rounded-full overflow-hidden bg-primary-100">
              {avatarPreview || user?.avatar ? (
                <img
                  src={avatarPreview || user?.avatar}
                  alt="Profile"
                  className="h-full w-full object-cover"
                />
              ) : (
                <div className="h-full w-full flex items-center justify-center">
                  <span className="text-2xl font-medium text-primary">
                    {user?.name?.split(' ').map(n => n[0]).join('') || 'U'}
                  </span>
                </div>
              )}
            </div>
            {isEditing && (
              <label className="absolute -bottom-2 -right-2 bg-white rounded-full p-2 shadow-md border border-gray-200 cursor-pointer hover:bg-gray-50">
                <Camera className="h-4 w-4 text-gray-600" />
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleAvatarChange}
                  className="hidden"
                />
              </label>
            )}
          </div>
          {isEditing && (
            <div>
              <p className="text-sm font-medium text-gray-900">Profile Photo</p>
              <p className="text-xs text-gray-500 mt-1">
                Upload a new profile photo. JPG, PNG up to 2MB.
              </p>
            </div>
          )}
        </div>

        {/* Form Fields */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              First Name
            </label>
            <input
              {...register('firstName')}
              disabled={!isEditing}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary disabled:bg-gray-50 disabled:text-gray-500"
            />
            {errors.firstName && (
              <p className="text-sm text-red-600 mt-1">{errors.firstName.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Last Name
            </label>
            <input
              {...register('lastName')}
              disabled={!isEditing}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary disabled:bg-gray-50 disabled:text-gray-500"
            />
            {errors.lastName && (
              <p className="text-sm text-red-600 mt-1">{errors.lastName.message}</p>
            )}
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email Address
            </label>
            <input
              {...register('email')}
              type="email"
              disabled={!isEditing}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary disabled:bg-gray-50 disabled:text-gray-500"
            />
            {errors.email && (
              <p className="text-sm text-red-600 mt-1">{errors.email.message}</p>
            )}
          </div>

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