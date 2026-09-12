export type ChapterKey="matiere"|"digestion"|"circuits"|"terre";
export interface ScienceChapter {
  chapter:ChapterKey;code?:string;title?:string;objective?:string;
  vocabulary:{word:string;definition:string}[];
  source:{url:string;pdf_url:string;page:number;section:string;programme_version:string};
  success_criteria:string[];
  settings:{id:string;label:string}[];
  experiment:{title:string;objective:string;mode:"virtual";materials:string[];steps:string[];safety_rules:string[];hypothesis:string;analysis_question:string};
}
export interface ScienceRun {
  id:string;chapter:ChapterKey;setting:string;hypothesis:string;conclusion:string;completed_at:string|null;created_at:string;
  result:{label:string;before:string;after:string;observation:string;reference_conclusion:string;limitation:string;model_version:string};
  storage:"ephemeral_preview"|"encrypted_30_days";
}
