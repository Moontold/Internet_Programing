export type Role = 'tutor' | 'parent' | 'student';
export type LessonFormat = 'offline' | 'online';

export interface Profile {
  id: number;
  role: Role;
  full_name: string;
  login: string;
}

export interface ParentShort {
  id: number;
  full_name: string;
  phone: string;
}
export interface ChildShort {
  id: number;
  full_name: string;
  grade: number | null;
  is_active: boolean;
}
export interface Parent extends ParentShort {
  login: string;
  contacts_note: string;
  is_active: boolean;
  children: ChildShort[];
}
export interface ParentCreate {
  full_name: string;
  login: string;
  password: string;
  phone: string;
  contacts_note: string;
}
export interface ParentUpdate {
  full_name?: string;
  phone?: string;
  contacts_note?: string;
  is_active?: boolean;
}

export interface StudentShort {
  id: number;
  full_name: string;
  grade: number | null;
  grade_note: string;
  format: LessonFormat;
  is_active: boolean;
}
export interface StudentListItem extends StudentShort {
  parent: ParentShort;
}
export interface Student extends StudentListItem {
  login: string;
  price_per_lesson: number;
}
export interface StudentCreate {
  full_name: string;
  login: string;
  password: string;
  parent_id: number;
  grade: number | null;
  grade_note: string;
  format: LessonFormat;
  price_per_lesson: number;
}
export interface StudentUpdate {
  full_name?: string;
  parent_id?: number;
  grade?: number | null;
  grade_note?: string;
  format?: LessonFormat;
  price_per_lesson?: number;
  is_active?: boolean;
}
