export interface EditableProject {
  id: string;
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

export const mockProject: EditableProject = {
  id: '1',
  name: 'Campus Navigator',
  shortDescription:
    'Navigate campus with real-time indoor maps and directions.',
  fullDescription:
    'Campus Navigator is a mobile app that helps students and visitors find their way around campus. It features real-time indoor and outdoor maps, turn-by-turn directions, and points of interest. Built with React Native for cross-platform support.',
  imageUrl: undefined,
  tags: ['React Native', 'Maps', 'Mobile'],
  teamMembers: [],
  websiteUrl: '',
  githubUrl: '',
  demoVideoUrl: '',
};
