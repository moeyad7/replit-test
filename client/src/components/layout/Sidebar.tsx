import { Link, useLocation } from "wouter";
import { 
  DashboardIcon, 
  CustomersIcon, 
  PointsIcon, 
  ChallengesIcon,
  ReportsIcon 
} from "../ui/icons";

interface NavItemProps {
  icon: React.ReactNode;
  label: string;
  href: string;
  active?: boolean;
}

const NavItem: React.FC<NavItemProps> = ({ icon, label, href, active }) => {
  const className = `flex items-center px-2 py-2 text-sm font-medium rounded-md cursor-pointer ${
    active 
      ? "bg-primary-50 text-primary-700" 
      : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
  }`;
  
  return (
    <div className={className} onClick={() => window.location.href = href}>
      <span className="mr-3 text-lg">{icon}</span>
      {label}
    </div>
  );
};

export default function Sidebar() {
  const [location] = useLocation();

  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex-shrink-0 hidden md:block">
      <div className="h-full flex flex-col">
        <nav className="flex-1 px-2 py-4 space-y-1">
          <NavItem 
            icon={<DashboardIcon size={20} />} 
            label="Dashboard" 
            href="/" 
            active={location === '/'} 
          />
          <NavItem 
            icon={<CustomersIcon size={20} />} 
            label="Customers" 
            href="/customers" 
          />
          <NavItem 
            icon={<PointsIcon size={20} />} 
            label="Points & Rewards" 
            href="/points" 
          />
          <NavItem 
            icon={<ChallengesIcon size={20} />} 
            label="Challenges" 
            href="/challenges" 
          />
          <NavItem 
            icon={<ReportsIcon size={20} />} 
            label="Reports" 
            href="/reports" 
          />
        </nav>
        <div className="p-4 border-t border-gray-200">
          <div className="bg-primary-50 p-3 rounded-lg">
            <h3 className="text-sm font-medium text-primary-800">Need help?</h3>
            <p className="mt-1 text-xs text-primary-700">
              Try asking about your customers' points, behaviors, or rewards trends.
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}
