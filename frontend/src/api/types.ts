export type Role = 'tutor' | 'parent' | 'student';

export interface Profile {
  id: number;
  role: Role;
  full_name: string;
  login: string;
}
