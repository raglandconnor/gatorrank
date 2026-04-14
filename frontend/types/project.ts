/** Project row shape for home/grid/profile-style cards (API-mapped or mock). */
export interface Project {
  id: string | number;
  name: string;
  slug: string;
  description: string;
  categories: string[];
  tags: string[];
  tech_stack: string[];
  votes: number;
  viewerHasVoted?: boolean;
  comments: number;
}
