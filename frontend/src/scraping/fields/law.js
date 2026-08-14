import {
  Gavel,
  Handshake,
  Lightbulb,
  Receipt,
  Scale,
  Shield,
} from "lucide-react";

/**
 * Master of Law (MH) field scraping config.
 */
export const law = {
  key: "law",
  label: "Master of Law",
  shortLabel: "MH",
  degree: "S2 Master of Law",
  description:
    "Scrape & discover Legal professionals from LinkedIn for S2 Master of Law (MH) recruitment",
  icon: Scale,
  accent: {
    text: "text-purple-600",
    icon: "text-purple-600",
    activeButton: "bg-purple-600 text-white border-purple-600",
    softActive: "bg-purple-100 border-purple-300 text-purple-700",
    hover: "hover:bg-purple-50 hover:border-purple-300 hover:text-purple-700",
    softBg: "bg-purple-50 border-purple-200",
    dot: "bg-purple-500",
    spinner: "text-purple-600",
  },
  presets: [
    {
      label: "Corporate & Commercial",
      icon: Scale,
      queries: [
        'site:linkedin.com/in "corporate lawyer" Indonesia',
        'site:linkedin.com/in "corporate counsel" Indonesia',
        'site:linkedin.com/in "company lawyer" Indonesia',
      ],
    },
    {
      label: "Litigation & Dispute",
      icon: Gavel,
      queries: [
        'site:linkedin.com/in "litigation lawyer" Indonesia',
        'site:linkedin.com/in "advocate" Indonesia',
        'site:linkedin.com/in "dispute resolution" Indonesia',
      ],
    },
    {
      label: "Criminal Law",
      icon: Shield,
      queries: [
        'site:linkedin.com/in "criminal lawyer" Indonesia',
        'site:linkedin.com/in "criminal defense" Indonesia',
      ],
    },
    {
      label: "Intellectual Property",
      icon: Lightbulb,
      queries: [
        'site:linkedin.com/in "intellectual property" Indonesia',
        'site:linkedin.com/in "IP lawyer" Indonesia',
      ],
    },
    {
      label: "Labor & Employment",
      icon: Handshake,
      queries: [
        'site:linkedin.com/in "labor lawyer" Indonesia',
        'site:linkedin.com/in "employment lawyer" Indonesia',
      ],
    },
    {
      label: "Tax Law",
      icon: Receipt,
      queries: [
        'site:linkedin.com/in "tax lawyer" Indonesia',
        'site:linkedin.com/in "tax consultant" Indonesia',
      ],
    },
  ],
  skills: [
    "Litigation",
    "Corporate Law",
    "Contract",
    "Legal",
    "Compliance",
    "Intellectual Property",
    "Labor Law",
    "Tax Law",
    "Arbitration",
    "Due Diligence",
    "Legal Research",
    "Negotiation",
  ],
};
