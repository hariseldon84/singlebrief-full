import { Shield, Lock, Eye, FileText, Users, CheckCircle, AlertTriangle, Download, Settings } from 'lucide-react'

export default function TrustPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Trust Center</h1>
          <p className="text-neutral">Security, compliance, and transparency</p>
        </div>
        <div className="flex items-center space-x-3">
          <button className="flex items-center space-x-2 px-4 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50">
            <Download className="h-4 w-4" />
            <span>Compliance Report</span>
          </button>
          <button className="flex items-center space-x-2 px-4 py-2 text-sm bg-primary text-white rounded-md hover:bg-primary-700">
            <Settings className="h-4 w-4" />
            <span>Security Settings</span>
          </button>
        </div>
      </div>

      {/* Security Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-neutral">Security Score</p>
              <p className="text-2xl font-semibold text-gray-900">98%</p>
            </div>
            <div className="h-12 w-12 bg-success-50 rounded-lg flex items-center justify-center">
              <Shield className="h-6 w-6 text-success" />
            </div>
          </div>
          <div className="mt-4">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-success h-2 rounded-full" style={{ width: '98%' }}></div>
            </div>
            <p className="text-sm text-success mt-1">Excellent security posture</p>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-neutral">Compliance Status</p>
              <p className="text-2xl font-semibold text-gray-900">100%</p>
            </div>
            <div className="h-12 w-12 bg-primary-50 rounded-lg flex items-center justify-center">
              <CheckCircle className="h-6 w-6 text-primary" />
            </div>
          </div>
          <p className="text-sm text-primary mt-2">All standards met</p>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-neutral">Data Sources</p>
              <p className="text-2xl font-semibold text-gray-900">12</p>
            </div>
            <div className="h-12 w-12 bg-highlight-50 rounded-lg flex items-center justify-center">
              <Eye className="h-6 w-6 text-highlight" />
            </div>
          </div>
          <p className="text-sm text-neutral mt-2">Monitored and secured</p>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-neutral">Audit Events</p>
              <p className="text-2xl font-semibold text-gray-900">2,847</p>
            </div>
            <div className="h-12 w-12 bg-soft-50 rounded-lg flex items-center justify-center">
              <FileText className="h-6 w-6 text-highlight" />
            </div>
          </div>
          <p className="text-sm text-neutral mt-2">Last 30 days</p>
        </div>
      </div>

      {/* Security Measures */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Data Protection */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Data Protection</h3>
          <div className="space-y-4">
            {[
              { feature: 'End-to-End Encryption', status: 'active', description: 'AES-256 encryption for all data' },
              { feature: 'Zero Trust Architecture', status: 'active', description: 'Every access request verified' },
              { feature: 'Data Anonymization', status: 'active', description: 'PII automatically protected' },
              { feature: 'Secure Data Storage', status: 'active', description: 'SOC 2 compliant infrastructure' },
            ].map((item, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="h-8 w-8 bg-success-50 rounded-full flex items-center justify-center">
                    <CheckCircle className="h-4 w-4 text-success" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{item.feature}</p>
                    <p className="text-xs text-neutral">{item.description}</p>
                  </div>
                </div>
                <span className="text-xs bg-success-100 text-success px-2 py-1 rounded-full">
                  Active
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Access Controls */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Access Controls</h3>
          <div className="space-y-4">
            {[
              { feature: 'Multi-Factor Authentication', status: 'required', description: 'MFA required for all users' },
              { feature: 'Role-Based Permissions', status: 'active', description: 'Granular access control' },
              { feature: 'Session Management', status: 'active', description: 'Automatic session timeout' },
              { feature: 'Audit Logging', status: 'active', description: 'Complete access history' },
            ].map((item, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="h-8 w-8 bg-primary-50 rounded-full flex items-center justify-center">
                    <Lock className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{item.feature}</p>
                    <p className="text-xs text-neutral">{item.description}</p>
                  </div>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full ${
                  item.status === 'required' ? 'bg-highlight-100 text-highlight' : 'bg-primary-100 text-primary'
                }`}>
                  {item.status === 'required' ? 'Required' : 'Active'}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Compliance Standards */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Compliance Standards</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { standard: 'SOC 2 Type II', status: 'compliant', lastAudit: 'Dec 2023', nextAudit: 'Dec 2024' },
            { standard: 'GDPR', status: 'compliant', lastAudit: 'Nov 2023', nextAudit: 'Nov 2024' },
            { standard: 'CCPA', status: 'compliant', lastAudit: 'Oct 2023', nextAudit: 'Oct 2024' },
          ].map((compliance, index) => (
            <div key={index} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-semibold text-gray-900">{compliance.standard}</h4>
                <span className="text-xs bg-success-100 text-success px-2 py-1 rounded-full">
                  Compliant
                </span>
              </div>
              <div className="space-y-2 text-sm text-neutral">
                <p>Last Audit: {compliance.lastAudit}</p>
                <p>Next Audit: {compliance.nextAudit}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Privacy Controls */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Privacy Controls</h3>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Data Retention */}
          <div>
            <h4 className="font-medium text-gray-900 mb-3">Data Retention Policies</h4>
            <div className="space-y-3">
              {[
                { type: 'Personal Data', retention: '2 years', purpose: 'Service delivery' },
                { type: 'Usage Analytics', retention: '1 year', purpose: 'Performance optimization' },
                { type: 'Audit Logs', retention: '7 years', purpose: 'Compliance requirements' },
                { type: 'Cached Data', retention: '30 days', purpose: 'Performance enhancement' },
              ].map((policy, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{policy.type}</p>
                    <p className="text-xs text-neutral">{policy.purpose}</p>
                  </div>
                  <span className="text-sm text-primary">{policy.retention}</span>
                </div>
              ))}
            </div>
          </div>

          {/* User Rights */}
          <div>
            <h4 className="font-medium text-gray-900 mb-3">User Rights</h4>
            <div className="space-y-3">
              {[
                { right: 'Data Access', description: 'Request copy of your data' },
                { right: 'Data Portability', description: 'Export data in standard format' },
                { right: 'Data Deletion', description: 'Request deletion of personal data' },
                { right: 'Opt-out Controls', description: 'Control data processing preferences' },
              ].map((right, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{right.right}</p>
                    <p className="text-xs text-neutral">{right.description}</p>
                  </div>
                  <button className="text-sm text-primary hover:text-primary-700">
                    Request
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Recent Security Events */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Recent Security Events</h3>
          <button className="text-sm text-primary hover:text-primary-700">View all events</button>
        </div>
        <div className="space-y-3">
          {[
            { event: 'Security scan completed', type: 'success', time: '2 hours ago', details: 'No vulnerabilities found' },
            { event: 'Access policy updated', type: 'info', time: '1 day ago', details: 'MFA requirement added' },
            { event: 'Data encryption verified', type: 'success', time: '2 days ago', details: 'All data properly encrypted' },
            { event: 'Compliance audit scheduled', type: 'warning', time: '3 days ago', details: 'SOC 2 audit in 30 days' },
          ].map((event, index) => (
            <div key={index} className="flex items-start space-x-3 p-3 hover:bg-gray-50 rounded-lg">
              <div className={`h-8 w-8 rounded-full flex items-center justify-center ${
                event.type === 'success' ? 'bg-success-50' :
                event.type === 'info' ? 'bg-primary-50' : 'bg-highlight-50'
              }`}>
                {event.type === 'success' ? (
                  <CheckCircle className="h-4 w-4 text-success" />
                ) : event.type === 'info' ? (
                  <Shield className="h-4 w-4 text-primary" />
                ) : (
                  <AlertTriangle className="h-4 w-4 text-highlight" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900">{event.event}</p>
                <p className="text-sm text-neutral">{event.details}</p>
                <p className="text-xs text-neutral mt-1">{event.time}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}