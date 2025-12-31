import { Outlet, NavLink } from 'react-router-dom';
import { LayoutDashboard, Inbox, BarChart3, Users, BookOpen, LucideIcon } from 'lucide-react';

interface NavigationItem {
  name: string;
  to: string;
  icon: LucideIcon;
}

const Layout = (): JSX.Element => {
  const navigation: NavigationItem[] = [
    { name: 'Dashboard', to: '/', icon: LayoutDashboard },
    { name: 'Inbox', to: '/inbox', icon: Inbox },
    { name: 'Analytics', to: '/analytics', icon: BarChart3 },
    { name: 'Leads', to: '/leads', icon: Users },
    { name: 'Knowledge', to: '/knowledge', icon: BookOpen },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              {/* Logo */}
              <div className="flex-shrink-0 flex items-center">
                <h1 className="text-xl font-bold text-emerald-400">
                  Nutricraft Labs
                </h1>
              </div>
              {/* Navigation Links */}
              <div className="hidden sm:ml-8 sm:flex sm:space-x-8">
                {navigation.map((item) => (
                  <NavLink
                    key={item.name}
                    to={item.to}
                    end={item.to === '/'}
                    className={({ isActive }) =>
                      `inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                        isActive
                          ? 'border-primary-500 text-gray-900'
                          : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                      }`
                    }
                  >
                    <item.icon className="w-4 h-4 mr-2" />
                    {item.name}
                  </NavLink>
                ))}
              </div>
            </div>
            {/* Right side */}
            <div className="flex items-center">
              <span className="text-sm text-gray-500">
                Supplement Lead Intelligence
              </span>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
