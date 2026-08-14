import {
  Briefcase,
  Compass,
  LineChart,
  Megaphone,
  Package,
  Users,
} from "lucide-react";

/**
 * Master of Management (MM) field scraping config.
 */
export const management = {
  key: "management",
  label: "Master of Management",
  shortLabel: "MM",
  degree: "S2 Master of Management",
  description:
    "Scrape & discover Management professionals from LinkedIn for S2 Master of Management (MM) recruitment",
  icon: Briefcase,
  accent: {
    text: "text-emerald-600",
    icon: "text-emerald-600",
    activeButton: "bg-emerald-600 text-white border-emerald-600",
    softActive: "bg-emerald-100 border-emerald-300 text-emerald-700",
    hover: "hover:bg-emerald-50 hover:border-emerald-300 hover:text-emerald-700",
    softBg: "bg-emerald-50 border-emerald-200",
    dot: "bg-emerald-500",
    spinner: "text-emerald-600",
  },
  presets: [
    {
      label: "Business / Operations",
      icon: Briefcase,
      queries: [
        'site:linkedin.com/in "operations manager" Indonesia',
        'site:linkedin.com/in "business manager" Indonesia',
        'site:linkedin.com/in "general manager" Indonesia',
      ],
    },
    {
      label: "Finance & Accounting",
      icon: LineChart,
      queries: [
        'site:linkedin.com/in "finance manager" Indonesia',
        'site:linkedin.com/in "finance director" Indonesia',
        'site:linkedin.com/in "accounting manager" Indonesia',
      ],
    },
    {
      label: "Marketing & Sales",
      icon: Megaphone,
      queries: [
        'site:linkedin.com/in "marketing manager" Indonesia',
        'site:linkedin.com/in "sales manager" Indonesia',
        'site:linkedin.com/in "brand manager" Indonesia',
      ],
    },
    {
      label: "Human Resources",
      icon: Users,
      queries: [
        'site:linkedin.com/in "HR manager" Indonesia',
        'site:linkedin.com/in "human resources" Indonesia',
        'site:linkedin.com/in "people operations" Indonesia',
      ],
    },
    {
      label: "Supply Chain & Logistics",
      icon: Package,
      queries: [
        'site:linkedin.com/in "supply chain manager" Indonesia',
        'site:linkedin.com/in "logistics manager" Indonesia',
        'site:linkedin.com/in "procurement manager" Indonesia',
      ],
    },
    {
      label: "Strategy & Consulting",
      icon: Compass,
      queries: [
        'site:linkedin.com/in "management consultant" Indonesia',
        'site:linkedin.com/in "business consultant" Indonesia',
        'site:linkedin.com/in "strategy manager" Indonesia',
      ],
    },
  ],
  skills: [
    "Management",
    "Leadership",
    "Strategy",
    "Finance",
    "Marketing",
    "Supply Chain",
    "Operations",
    "Project Management",
    "Business Analysis",
    "Human Resources",
    "Sales",
    "Budgeting",
    "Negotiation",
  ],
};
