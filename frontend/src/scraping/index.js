import { computerScience } from "./fields/computer-science";
import { management } from "./fields/management";
import { law } from "./fields/law";

/**
 * All supported scraping fields. Order defines the default field and the
 * order of the field selector tabs in the LinkedIn Sourcing page.
 */
export const FIELDS = [computerScience, management, law];

/** Get a field by key, falling back to the first (default) field. */
export function getField(key) {
  return FIELDS.find((f) => f.key === key) || FIELDS[0];
}

/**
 * Compute a relevance level for a profile based on how many of its skills
 * match the active field's skill list.
 */
export function computeRelevance(skills = [], field = FIELDS[0]) {
  const fieldSkills = field.skills || [];
  if (!skills || skills.length === 0)
    return { level: "unknown", label: "—", color: "bg-gray-100 text-gray-500" };

  const matched = skills.filter((s) =>
    fieldSkills.some((fs) => s.toLowerCase().includes(fs.toLowerCase()))
  );

  if (matched.length >= 3)
    return { level: "high", label: "High", color: "bg-green-100 text-green-700" };
  if (matched.length >= 1)
    return { level: "medium", label: "Medium", color: "bg-yellow-100 text-yellow-700" };
  return { level: "low", label: "Low", color: "bg-red-100 text-red-700" };
}
