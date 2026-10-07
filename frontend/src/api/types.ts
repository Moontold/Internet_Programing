export type Role = 'tutor' | 'parent' | 'student';
export type LessonFormat = 'offline' | 'online';
export type LessonStatus = 'planned' | 'held' | 'cancelled';
export type HomeworkStatus = 'not_checked' | 'done' | 'not_done';
export type Scope = 'this' | 'following' | 'all';

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
  series: Series[];
  stats: StudentStats;
}
export interface StudentStats {
  homework_done_percent: number | null;
  homework_avg_grade: number | null;
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

export interface SeriesStudent {
  id: number;
  full_name: string;
}
export interface Series {
  id: number;
  first_start: string;
  duration_minutes: number;
  interval_weeks: number;
  until: string | null;
  title: string;
  students: SeriesStudent[];
}
export interface SeriesCreate {
  first_start: string;
  duration_minutes: number;
  interval_weeks: number;
  until: string | null;
  title: string;
  student_ids: number[];
}

export interface FileInfo {
  id: number;
  original_name: string;
  size: number;
  mime: string;
  created_at: string;
}

export interface LessonParticipant {
  student_id: number;
  full_name: string;
  homework_status: HomeworkStatus | null;
  homework_grade: number | null;
}
export interface LessonShort {
  id: number;
  series_id: number | null;
  scheduled_start: string;
  duration_minutes: number;
  status: LessonStatus;
  detached: boolean;
  topic: string;
  title: string;
  format: LessonFormat | null;
  participants: LessonParticipant[];
  has_homework: boolean;
}
export interface Lesson extends LessonShort {
  original_start: string;
  homework_text: string;
  homework_saved_at: string | null;
  files: FileInfo[];
  previous_grade: number | null;
}
export interface LessonCreate {
  scheduled_start: string;
  duration_minutes: number;
  title: string;
  student_ids: number[];
}
export interface LessonUpdate {
  scope?: Scope;
  scheduled_start?: string;
  duration_minutes?: number;
  student_ids?: number[];
  topic?: string;
}
export interface ParticipantUpdate {
  homework_status?: HomeworkStatus;
  homework_grade?: number;
  clear_grade?: boolean;
}

export interface ChildCard {
  student: StudentShort;
  series: Series[];
  stats: StudentStats;
}
export interface ChildrenList {
  children: ChildCard[];
}
