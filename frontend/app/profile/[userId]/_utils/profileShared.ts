export interface ExtendedProfile {
  bio: string;
  socials: { github?: string; linkedin?: string; website?: string };
  major: string;
  graduationYear: number;
  courses: string[];
  skills: string[];
}

export const EMPTY_EXTENDED: ExtendedProfile = {
  bio: '',
  socials: {},
  major: '',
  graduationYear: 0,
  courses: [],
  skills: [],
};

export function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0][0]?.toUpperCase() ?? '';
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

const extendedProfileKey = (userId: string) =>
  `gatorrank_profile_ext_${userId}`;

export function loadExtendedProfile(userId: string): ExtendedProfile {
  if (typeof window === 'undefined') return EMPTY_EXTENDED;
  try {
    const raw = localStorage.getItem(extendedProfileKey(userId));
    if (!raw) return EMPTY_EXTENDED;
    return {
      ...EMPTY_EXTENDED,
      ...(JSON.parse(raw) as Partial<ExtendedProfile>),
    };
  } catch {
    return EMPTY_EXTENDED;
  }
}

export function saveExtendedProfile(
  userId: string,
  ext: ExtendedProfile,
): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(extendedProfileKey(userId), JSON.stringify(ext));
}
