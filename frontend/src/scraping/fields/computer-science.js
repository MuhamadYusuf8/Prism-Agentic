import {
  Code,
  Cloud,
  Cpu,
  Globe,
  Shield,
  Smartphone,
} from "lucide-react";

/**
 * Computer Science field scraping config.
 * Preset sub-sections power the "quick search" buttons and the modal.
 */
export const computerScience = {
  key: "computer_science",
  label: "Computer Science",
  shortLabel: "CS",
  degree: "S2 Informatics",
  description:
    "Scrape & discover Computer Science professionals from LinkedIn for S2 Informatics recruitment",
  icon: Code,
  accent: {
    text: "text-blue-600",
    icon: "text-blue-600",
    activeButton: "bg-blue-600 text-white border-blue-600",
    softActive: "bg-blue-100 border-blue-300 text-blue-700",
    hover: "hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700",
    softBg: "bg-blue-50 border-blue-200",
    dot: "bg-blue-500",
    spinner: "text-blue-600",
  },
  presets: [
    {
      label: "Software Engineer",
      icon: Code,
      queries: [
        'site:linkedin.com/in "software engineer" Indonesia',
        'site:linkedin.com/in "software developer" Indonesia',
      ],
    },
    {
      label: "Data & AI",
      icon: Cpu,
      queries: [
        'site:linkedin.com/in "data scientist" Indonesia',
        'site:linkedin.com/in "machine learning" Indonesia',
        'site:linkedin.com/in "data engineer" Indonesia',
      ],
    },
    {
      label: "Backend / DevOps",
      icon: Cloud,
      queries: [
        'site:linkedin.com/in "backend engineer" Indonesia',
        'site:linkedin.com/in "devops engineer" Indonesia',
        'site:linkedin.com/in "cloud engineer" Indonesia',
      ],
    },
    {
      label: "Frontend / Mobile",
      icon: Smartphone,
      queries: [
        'site:linkedin.com/in "frontend developer" Indonesia',
        'site:linkedin.com/in "full stack" Indonesia',
        'site:linkedin.com/in "mobile developer" Indonesia',
      ],
    },
    {
      label: "Cyber / Network",
      icon: Shield,
      queries: [
        'site:linkedin.com/in "cybersecurity" Indonesia',
        'site:linkedin.com/in "network engineer" Indonesia',
      ],
    },
    {
      label: "IT / Management",
      icon: Globe,
      queries: [
        'site:linkedin.com/in "IT manager" Indonesia',
        'site:linkedin.com/in "IT director" Indonesia',
        'site:linkedin.com/in "CTO" Indonesia',
      ],
    },
  ],
  skills: [
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "React",
    "Node.js",
    "Go",
    "Docker",
    "Kubernetes",
    "AWS",
    "SQL",
    "Machine Learning",
  ],
};
