export interface UserProfile {
  name: string;
  avatarUrl?: string;
  role: 'student' | 'faculty';
  bio: string;
  socials: {
    github?: string;
    linkedin?: string;
    website?: string;
  };
  major: string;
  graduationYear: number;
  courses: string[];
  skills: string[];
}

export interface ProfileProject {
  id: number;
  name: string;
  imageUrl?: string;
  category: string;
  votes: number;
  comments: number;
}

export const mockProfile: UserProfile = {
  name: 'Luis Cabrera',
  role: 'student',
  bio: 'Passionate software engineer and innovator, dedicated to building impactful solutions that address real-world challenges. Experienced in full-stack development and AI applications.',
  socials: {
    github: 'https://github.com',
    linkedin: 'https://linkedin.com',
    website: 'https://example.com',
  },
  major: 'Computer Engineering',
  graduationYear: 2026,
  courses: ['COP4331', 'CEN3031', 'CAP4104', 'COP3530', 'CIS4301', 'CNT4007'],
  skills: [
    'Next.js',
    'React',
    'FastAPI',
    'Supabase',
    'Tailwind CSS',
    'PostgreSQL',
    'Python',
    'TypeScript',
  ],
};

export const mockProfileProjects: ProfileProject[] = [
  {
    id: 1,
    name: 'Campus Navigator',
    category: 'Mobile App',
    votes: 245,
    comments: 32,
  },
  {
    id: 2,
    name: 'Study Group Finder',
    category: 'Web Application',
    votes: 189,
    comments: 18,
  },
  {
    id: 3,
    name: 'AI Study Assistant',
    category: 'Artificial Intelligence',
    votes: 312,
    comments: 47,
  },
];
