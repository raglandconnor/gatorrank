export interface Project {
  id: number;
  name: string;
  description: string;
  tags: string[];
  votes: number;
  comments: number;
}

export const topOverallProjects: Project[] = [
  {
    id: 1,
    name: 'Minara',
    description:
      'A mobile app that helps UF students find study groups and tutors on campus.',
    tags: ['iOS', 'Education', 'Social'],
    votes: 342,
    comments: 27,
  },
  {
    id: 2,
    name: 'GatorMap',
    description:
      'An interactive campus navigation tool with real-time crowd density overlays.',
    tags: ['Web', 'Maps', 'Productivity'],
    votes: 289,
    comments: 14,
  },
  {
    id: 3,
    name: 'SwampByte',
    description:
      'A competitive coding platform specifically designed for UF CS students.',
    tags: ['Web', 'Education', 'Open Source'],
    votes: 251,
    comments: 19,
  },
  {
    id: 4,
    name: 'HealthGator',
    description:
      'Tracks personal health metrics and syncs with UF Student Health Center records.',
    tags: ['iOS', 'Health & Fitness', 'AI'],
    votes: 198,
    comments: 11,
  },
  {
    id: 5,
    name: 'ChompAI',
    description:
      'An AI-powered course selection assistant that recommends schedules based on your major.',
    tags: ['Web', 'AI', 'Education'],
    votes: 175,
    comments: 22,
  },
];

export const trendingThisMonthProjects: Project[] = [
  {
    id: 6,
    name: 'GatorEats',
    description:
      'Discover the best food spots near UF with ratings from fellow students.',
    tags: ['iOS', 'Food & Drink', 'Social'],
    votes: 143,
    comments: 31,
  },
  {
    id: 7,
    name: 'RentGator',
    description:
      'Find and compare off-campus housing options near the University of Florida.',
    tags: ['Web', 'Real Estate', 'Productivity'],
    votes: 128,
    comments: 18,
  },
  {
    id: 8,
    name: 'Swampfolio',
    description:
      'A portfolio builder and showcase platform tailored for UF engineering students.',
    tags: ['Web', 'Career', 'Open Source'],
    votes: 112,
    comments: 9,
  },
  {
    id: 9,
    name: 'GatorBudget',
    description:
      'Personal finance tracker built for college students living on a tight budget.',
    tags: ['iOS', 'Finance', 'Productivity'],
    votes: 97,
    comments: 7,
  },
  {
    id: 10,
    name: 'ClubHub',
    description:
      'A centralized directory and event calendar for all UF student organizations.',
    tags: ['Web', 'Social', 'Events'],
    votes: 84,
    comments: 15,
  },
];

export const trendingLastMonthProjects: Project[] = [
  {
    id: 11,
    name: 'PawPrint',
    description:
      'Help reunite lost UF campus pets with their owners using photo recognition.',
    tags: ['iOS', 'AI', 'Social'],
    votes: 201,
    comments: 33,
  },
  {
    id: 12,
    name: 'SchedSync',
    description:
      'Syncs your UF class schedule with friends to find shared free time instantly.',
    tags: ['Web', 'Productivity', 'Social'],
    votes: 178,
    comments: 24,
  },
  {
    id: 13,
    name: 'Noteswap',
    description:
      'A peer-to-peer note sharing platform for UF courses with quality ratings.',
    tags: ['Web', 'Education', 'Open Source'],
    votes: 154,
    comments: 17,
  },
  {
    id: 14,
    name: 'GatorRide',
    description:
      'Carpool and rideshare matching for UF students commuting from Gainesville suburbs.',
    tags: ['iOS', 'Transportation', 'Social'],
    votes: 132,
    comments: 12,
  },
  {
    id: 15,
    name: 'ResearchLink',
    description:
      'Connects undergraduate students with UF faculty research opportunities.',
    tags: ['Web', 'Education', 'Career'],
    votes: 119,
    comments: 20,
  },
];
