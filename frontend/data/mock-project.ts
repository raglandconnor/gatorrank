import { mockProfileProjects } from './mock-profile';

export interface EditableProject {
  id: number;
  name: string;
  shortDescription: string;
  fullDescription: string;
  imageUrl?: string;
  tags: string[];
  teamMembers: string[];
  websiteUrl: string;
  githubUrl: string;
  demoVideoUrl: string;
}

export interface ProjectDetail extends EditableProject {
  votes: number;
  comments: number;
  category?: string;
}

export const mockProject: EditableProject = {
  id: 1,
  name: 'Campus Navigator',
  shortDescription:
    'Navigate campus with real-time indoor maps and directions.',
  fullDescription:
    'Campus Navigator is a mobile app that helps students and visitors find their way around campus. It features real-time indoor and outdoor maps, turn-by-turn directions, and points of interest. Built with React Native for cross-platform support.',
  imageUrl:
    'https://images.unsplash.com/photo-1526498460520-4c246339dccb?auto=format&fit=crop&w=400&q=80',
  tags: ['React Native', 'Maps', 'Mobile'],
  teamMembers: [],
  websiteUrl: '',
  githubUrl: '',
  demoVideoUrl: 'https://youtu.be/TOEawLBhxJU?si=jeWQWAf-y4Oysncm',
};

/** Resolves mock detail for `/projects/[id]` until the API exists. */
export function getProjectDetailById(
  id: string | number,
): ProjectDetail | null {
  const numericId =
    typeof id === 'string'
      ? (() => {
          // Only accept fully-numeric route params (e.g. "1abc" should not map to 1).
          if (!/^\d+$/.test(id)) return NaN;
          return Number(id);
        })()
      : id;

  if (!Number.isInteger(numericId)) return null;

  const profileMeta = mockProfileProjects.find((p) => p.id === numericId);

  if (numericId === mockProject.id) {
    return {
      ...mockProject,
      votes: profileMeta?.votes ?? 245,
      comments: profileMeta?.comments ?? 32,
      category: profileMeta?.category ?? 'Mobile App',
    };
  }

  if (profileMeta) {
    return {
      id: profileMeta.id,
      name: profileMeta.name,
      shortDescription: 'Listed on your profile.',
      fullDescription:
        'Full description for this project will appear here once it is connected to the backend.',
      tags: [],
      teamMembers: [],
      websiteUrl: '',
      githubUrl: '',
      demoVideoUrl: '',
      votes: profileMeta.votes,
      comments: profileMeta.comments,
      category: profileMeta.category,
    };
  }

  return null;
}
