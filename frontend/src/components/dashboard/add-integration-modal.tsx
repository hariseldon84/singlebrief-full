'use client'

import { useState } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { Fragment } from 'react'
import { X, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface AddIntegrationModalProps {
  open: boolean
  onClose: () => void
}

export function AddIntegrationModal({ open, onClose }: AddIntegrationModalProps) {
  const [selectedIntegration, setSelectedIntegration] = useState<string | null>(null)

  const availableIntegrations = [
    { id: 'slack', name: 'Slack', description: 'Team communication and channels' },
    { id: 'email', name: 'Gmail', description: 'Email integration and calendar' },
    { id: 'teams', name: 'Microsoft Teams', description: 'Team collaboration platform' },
    { id: 'notion', name: 'Notion', description: 'Documentation and notes' },
    { id: 'github', name: 'GitHub', description: 'Code repository and issues' },
    { id: 'jira', name: 'Jira', description: 'Project management and tickets' },
  ]

  const handleConnect = () => {
    if (selectedIntegration) {
      // Handle integration connection logic here
      console.log('Connecting to:', selectedIntegration)
      onClose()
    }
  }

  return (
    <Transition.Root show={open} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
        </Transition.Child>

        <div className="fixed inset-0 z-10 overflow-y-auto">
          <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
              enterTo="opacity-100 translate-y-0 sm:scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 translate-y-0 sm:scale-100"
              leaveTo="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            >
              <Dialog.Panel className="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6">
                <div className="absolute right-0 top-0 hidden pr-4 pt-4 sm:block">
                  <button
                    type="button"
                    className="rounded-md bg-white text-gray-400 hover:text-gray-500"
                    onClick={onClose}
                  >
                    <X className="h-6 w-6" />
                  </button>
                </div>
                <div className="sm:flex sm:items-start">
                  <div className="mt-3 text-center sm:ml-0 sm:mt-0 sm:text-left w-full">
                    <Dialog.Title as="h3" className="text-lg font-semibold leading-6 text-gray-900">
                      Add New Integration
                    </Dialog.Title>
                    <div className="mt-2">
                      <p className="text-sm text-gray-500">
                        Connect a new service to gather intelligence from your team
                      </p>
                    </div>
                    
                    <div className="mt-6 space-y-3">
                      {availableIntegrations.map((integration) => (
                        <div
                          key={integration.id}
                          className={`relative flex cursor-pointer rounded-lg border p-4 hover:bg-gray-50 ${
                            selectedIntegration === integration.id
                              ? 'border-primary bg-primary-50'
                              : 'border-gray-300'
                          }`}
                          onClick={() => setSelectedIntegration(integration.id)}
                        >
                          <div className="flex-1">
                            <div className="flex items-center">
                              <span className="text-sm font-medium text-gray-900">
                                {integration.name}
                              </span>
                            </div>
                            <div className="mt-1">
                              <span className="text-sm text-gray-500">
                                {integration.description}
                              </span>
                            </div>
                          </div>
                          {selectedIntegration === integration.id && (
                            <div className="flex items-center">
                              <div className="h-4 w-4 rounded-full bg-primary flex items-center justify-center">
                                <div className="h-2 w-2 rounded-full bg-white" />
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
                  <Button
                    onClick={handleConnect}
                    disabled={!selectedIntegration}
                    leftIcon={<Plus className="h-4 w-4" />}
                    className="w-full sm:ml-3 sm:w-auto"
                  >
                    Connect Integration
                  </Button>
                  <Button
                    variant="outline"
                    onClick={onClose}
                    className="mt-3 w-full sm:mt-0 sm:w-auto"
                  >
                    Cancel
                  </Button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition.Root>
  )
}