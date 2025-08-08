import { HelpCircle, Search, MessageSquare, Book, FileText, ExternalLink, ChevronRight, Mail, Phone } from 'lucide-react'

export default function HelpPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Help & Support</h1>
          <p className="text-neutral">Get help and find answers to your questions</p>
        </div>
        <div className="flex items-center space-x-3">
          <button className="flex items-center space-x-2 px-4 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50">
            <MessageSquare className="h-4 w-4" />
            <span>Contact Support</span>
          </button>
        </div>
      </div>

      {/* Search Help */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="text-center">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">How can we help you?</h2>
          <p className="text-neutral mb-4">Search our knowledge base for quick answers</p>
          <div className="relative max-w-lg mx-auto">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search for help articles, guides, and FAQs..."
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>
        </div>
      </div>

      {/* Quick Help Categories */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow cursor-pointer">
          <div className="flex items-center space-x-3 mb-4">
            <div className="h-12 w-12 bg-primary-50 rounded-lg flex items-center justify-center">
              <Book className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Getting Started</h3>
              <p className="text-sm text-neutral">Setup and basic usage</p>
            </div>
          </div>
          <ul className="space-y-2">
            <li className="flex items-center justify-between text-sm text-gray-700 hover:text-primary cursor-pointer">
              <span>Quick setup guide</span>
              <ChevronRight className="h-4 w-4" />
            </li>
            <li className="flex items-center justify-between text-sm text-gray-700 hover:text-primary cursor-pointer">
              <span>Your first query</span>
              <ChevronRight className="h-4 w-4" />
            </li>
            <li className="flex items-center justify-between text-sm text-gray-700 hover:text-primary cursor-pointer">
              <span>Understanding briefs</span>
              <ChevronRight className="h-4 w-4" />
            </li>
            <li className="flex items-center justify-between text-sm text-gray-700 hover:text-primary cursor-pointer">
              <span>Team collaboration</span>
              <ChevronRight className="h-4 w-4" />
            </li>
          </ul>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow cursor-pointer">
          <div className="flex items-center space-x-3 mb-4">
            <div className="h-12 w-12 bg-highlight-50 rounded-lg flex items-center justify-center">
              <HelpCircle className="h-6 w-6 text-highlight" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Common Questions</h3>
              <p className="text-sm text-neutral">Frequently asked questions</p>
            </div>
          </div>
          <ul className="space-y-2">
            <li className="flex items-center justify-between text-sm text-gray-700 hover:text-primary cursor-pointer">
              <span>How does AI memory work?</span>
              <ChevronRight className="h-4 w-4" />
            </li>
            <li className="flex items-center justify-between text-sm text-gray-700 hover:text-primary cursor-pointer">
              <span>Data privacy and security</span>
              <ChevronRight className="h-4 w-4" />
            </li>
            <li className="flex items-center justify-between text-sm text-gray-700 hover:text-primary cursor-pointer">
              <span>Integration setup</span>
              <ChevronRight className="h-4 w-4" />
            </li>
            <li className="flex items-center justify-between text-sm text-gray-700 hover:text-primary cursor-pointer">
              <span>Troubleshooting</span>
              <ChevronRight className="h-4 w-4" />
            </li>
          </ul>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow cursor-pointer">
          <div className="flex items-center space-x-3 mb-4">
            <div className="h-12 w-12 bg-success-50 rounded-lg flex items-center justify-center">
              <FileText className="h-6 w-6 text-success" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Advanced Features</h3>
              <p className="text-sm text-neutral">Power user guides</p>
            </div>
          </div>
          <ul className="space-y-2">
            <li className="flex items-center justify-between text-sm text-gray-700 hover:text-primary cursor-pointer">
              <span>Custom integrations</span>
              <ChevronRight className="h-4 w-4" />
            </li>
            <li className="flex items-center justify-between text-sm text-gray-700 hover:text-primary cursor-pointer">
              <span>API documentation</span>
              <ChevronRight className="h-4 w-4" />
            </li>
            <li className="flex items-center justify-between text-sm text-gray-700 hover:text-primary cursor-pointer">
              <span>Analytics and reporting</span>
              <ChevronRight className="h-4 w-4" />
            </li>
            <li className="flex items-center justify-between text-sm text-gray-700 hover:text-primary cursor-pointer">
              <span>Admin configuration</span>
              <ChevronRight className="h-4 w-4" />
            </li>
          </ul>
        </div>
      </div>

      {/* Popular Articles */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Popular Help Articles</h3>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {[
            { title: 'Setting up your first integration', category: 'Getting Started', views: '2.3k views' },
            { title: 'Understanding AI confidence scores', category: 'Features', views: '1.8k views' },
            { title: 'Managing team permissions', category: 'Administration', views: '1.5k views' },
            { title: 'Customizing daily brief preferences', category: 'Personalization', views: '1.2k views' },
            { title: 'Troubleshooting common connection issues', category: 'Troubleshooting', views: '1.1k views' },
            { title: 'Privacy settings and data control', category: 'Privacy', views: '987 views' },
          ].map((article, index) => (
            <div key={index} className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg cursor-pointer">
              <div>
                <h4 className="text-sm font-medium text-gray-900">{article.title}</h4>
                <div className="flex items-center space-x-2 mt-1">
                  <span className="text-xs bg-primary-100 text-primary px-2 py-1 rounded-full">
                    {article.category}
                  </span>
                  <span className="text-xs text-neutral">{article.views}</span>
                </div>
              </div>
              <ChevronRight className="h-4 w-4 text-gray-400" />
            </div>
          ))}
        </div>
      </div>

      {/* Contact Support & Resources */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Contact Support */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Contact Support</h3>
          <div className="space-y-4">
            <div className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg">
              <div className="h-10 w-10 bg-primary-50 rounded-lg flex items-center justify-center">
                <MessageSquare className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h4 className="font-medium text-gray-900">Live Chat</h4>
                <p className="text-sm text-neutral">Get instant help from our support team</p>
              </div>
              <button className="ml-auto text-primary hover:text-primary-700">
                <span className="text-sm font-medium">Start Chat</span>
              </button>
            </div>

            <div className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg">
              <div className="h-10 w-10 bg-highlight-50 rounded-lg flex items-center justify-center">
                <Mail className="h-5 w-5 text-highlight" />
              </div>
              <div>
                <h4 className="font-medium text-gray-900">Email Support</h4>
                <p className="text-sm text-neutral">support@singlebrief.com</p>
              </div>
              <button className="ml-auto text-primary hover:text-primary-700">
                <span className="text-sm font-medium">Send Email</span>
              </button>
            </div>

            <div className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg">
              <div className="h-10 w-10 bg-success-50 rounded-lg flex items-center justify-center">
                <Phone className="h-5 w-5 text-success" />
              </div>
              <div>
                <h4 className="font-medium text-gray-900">Phone Support</h4>
                <p className="text-sm text-neutral">Available Mon-Fri, 9 AM - 6 PM EST</p>
              </div>
              <button className="ml-auto text-primary hover:text-primary-700">
                <span className="text-sm font-medium">Call Now</span>
              </button>
            </div>
          </div>
        </div>

        {/* Additional Resources */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Additional Resources</h3>
          <div className="space-y-3">
            {[
              { title: 'API Documentation', description: 'Complete developer reference', link: true },
              { title: 'Video Tutorials', description: 'Step-by-step video guides', link: true },
              { title: 'Community Forum', description: 'Connect with other users', link: true },
              { title: 'Release Notes', description: 'Latest updates and features', link: true },
              { title: 'Status Page', description: 'System status and uptime', link: true },
              { title: 'Security Whitepaper', description: 'Detailed security information', link: true },
            ].map((resource, index) => (
              <div key={index} className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg cursor-pointer">
                <div>
                  <h4 className="text-sm font-medium text-gray-900">{resource.title}</h4>
                  <p className="text-xs text-neutral">{resource.description}</p>
                </div>
                <ExternalLink className="h-4 w-4 text-gray-400" />
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* System Status */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">System Status</h3>
          <span className="inline-flex items-center space-x-1 text-sm text-success">
            <div className="h-2 w-2 bg-success rounded-full"></div>
            <span>All systems operational</span>
          </span>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { service: 'AI Intelligence Service', status: 'operational', uptime: '99.9%' },
            { service: 'Data Integration Hub', status: 'operational', uptime: '99.8%' },
            { service: 'Report Generation', status: 'operational', uptime: '99.7%' },
          ].map((service, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="text-sm font-medium text-gray-900">{service.service}</p>
                <p className="text-xs text-neutral">Uptime: {service.uptime}</p>
              </div>
              <div className="flex items-center space-x-2">
                <div className="h-2 w-2 bg-success rounded-full"></div>
                <span className="text-xs text-success">Operational</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}