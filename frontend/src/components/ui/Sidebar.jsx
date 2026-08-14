import { useLocation, Link, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Linkedin,
  Users,
  BarChart2,
  Mail,
  Bot,
  Settings,
  LogOut,
  MessageSquare,
} from "lucide-react";
import clsx from "clsx";
import { useAuth } from "../../lib/auth-context";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/linkedin", label: "LinkedIn Sourcing", icon: Linkedin },
  { href: "/leads", label: "All Leads", icon: Users },
  { href: "/analytics", label: "Analytics", icon: BarChart2 },
  { href: "/email", label: "Email", icon: Mail },
  { href: "/email-monitoring", label: "Email Monitoring", icon: MessageSquare },
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  const location = useLocation();
  const pathname = location.pathname;
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <aside className="w-56 bg-white border-r flex flex-col">
      <div className="p-5 border-b">
        <div className="flex items-center gap-2">
          <Bot size={20} className="text-blue-600" />
          <div>
            <div className="font-bold text-sm tracking-widest text-blue-600">
              PRISM
            </div>
            <div className="text-xs text-gray-400 leading-tight">
              President University
            </div>
          </div>
        </div>
      </div>
      <nav className="flex-1 p-3 space-y-0.5">
        {nav.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              to={href}
              className={clsx(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
                active
                  ? "bg-blue-50 text-blue-700 font-medium"
                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900",
              )}
            >
              <Icon size={16} className={active ? "text-blue-600" : ""} />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t p-3">
        {user && (
          <div className="flex items-center gap-2 px-1 pb-2 mb-2 border-b">
            <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-bold shrink-0">
              {(user.name || user.email || "A").charAt(0).toUpperCase()}
            </div>
            <div className="min-w-0">
              <div className="text-xs font-semibold truncate">{user.name || user.email}</div>
              <div className="text-[10px] text-gray-400 truncate">{user.email}</div>
            </div>
          </div>
        )}
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-red-50 hover:text-red-600 transition-colors"
        >
          <LogOut size={16} />
          Logout
        </button>
      </div>
      <div className="p-4 border-t text-xs text-gray-400 text-center">
        v2.0.0 · PRISM
      </div>
    </aside>
  );
}
