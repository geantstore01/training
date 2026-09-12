export type Role = "student" | "parent" | "teacher" | "school_admin" | "content_creator" | "sys_admin";
export interface Account { id: string; login: string; roles: Role[]; school_id: string; student_id: string | null; teacher_id: string | null }
export interface Student { id: string; pseudonym: string; level: "CM1" | "CM2"; accessibility_preferences: Preferences }
export interface Preferences { text_size: "normal" | "large"; dyslexic_font: boolean; voice_instructions: boolean }
export interface Mission { id: string; class_id: string; title: string; day: string; group_id: string | null; status: string; exercise_version_ids: string[] }
export interface AdaptiveCourse { title:string; focus:string; explanation:string; method:string[]; worked_example:string[]; exercise_version_id:string }
export interface CourseProgress { lesson_id:string; competency_id:string; title:string; subject:string; completed_exercises:number; total_exercises:number; progress_percent:number; status:"non_commencé"|"en_cours"|"passed"|"à_revoir"|"à_relire"; note:number|null; last_attempt_at:string|null; help_used:boolean; adapted_course:AdaptiveCourse|null }
export interface Part { visual?:{kind:"fraction";parts:number;selected:number}|{kind:"grid";rows:number;columns:number}|null; id: string; question: string; competency_id: string; response_type: "number" | "text" | "choice" | "ordering"; options: {id: string; label: string}[] }
export interface Exercise { id: string; kind: string; difficulty?: number; prompt: { instruction: string; parts: Part[] } }
export type Answers = Record<string, string | string[]>;
export interface Feedback { part_id: string; outcome: "réussi" | "à_revoir" | "à_relire"; message: string; error_code: string | null; categories?:string[] }
export interface Attempt { id: string; session_id: string; exercise_version_id: string; submitted_at: string | null; result: { feedback: Feedback[]; message: string } | null }
export interface TutorTurn { message_pedagogique: string; type: "questionnement" | "indice" | "methode_partielle" | "refus_socratique" | "indisponible" | "protection"; niveau_aide: number; aide_max?:number; question_suivante: string | null; erreur_detectee: "non_determinee" | "comprehension" | "organisation" | "verification"; action_recommandee: "reformuler" | "identifier" | "representer" | "relier" | "decomposer" | "verifier" | "amorcer" | "reessayer" | "demander_adulte"; safety_status: "safe" | "blocked" | "fallback" }
export interface Progress { student_id: string; competences_acquises: number; competences_a_retravailler: number; competences_en_apprentissage: number; minutes_session_estimees: number; tentatives_terminees: number; message: string }
export interface Notice { id: string; student_id: string; kind: string; period: string; body: Partial<Progress> & { message?: string }; read_at: string | null }
export interface SchoolClass { id: string; name: string; academic_year: number }
export interface Group { id: string; name: string; student_ids: string[] }
export interface Control { student_id: string; enabled: boolean; max_help: number; revision: number }
export interface ErrorPattern { competency_id: string; error_code: string; recurring: boolean; message: string }
export interface Policy { version: string; purposes: Record<string, string>; child_notice: string; withdrawal: string }
export interface Consent { id: string; purpose: string; granted: boolean; event_type: string; recorded_at: string }
export interface LessonSummary { id: string; version: number; title: string }
export interface CM2Lesson {subject?:"mathematiques"|"francais"|"sciences"|"histoire";history?:import("./history").HistoryChapter;science?:import("./science").ScienceChapter;objective:string;prerequisites:string[];discovery:string;explanation:string;method:string[];worked_example:string[];common_errors:string[];check_exercise_id:string;practice_exercise_ids:string[]}
export interface Lesson { title: string; body: { summary: string; objectives: string[]; blocks: {kind: string; text: string}[]; steps: {title: string; blocks: {kind: string; text: string}[]}[]; cm2?:CM2Lesson|null } }
export interface Subject { id: string; code: string; name: string }
export interface Competency { id: string; subject_id: string; domain_id: string | null; curriculum_level_id: string; code: string; label: string; description: string; objectives: string[]; common_errors: string[]; programme_version:string }
