export interface HistorySource {title:string;url:string;page:number|null;section:string}
export interface HistoryEvent {id:string;year:number;date:string;title:string;explanation:string;source:HistorySource}
export interface HistoryChapter {
  chapter:string;theme:string;period:string;programme_version:string;sensitive:boolean;essential_question:string;
  timeline:HistoryEvent[];
  figures:{name:string;born:number;died:number;role:string;remember:string;confusion:string;event_ids:string[];source:HistorySource}[];
  places:{name:string;latitude:number;longitude:number;importance:string;source:HistorySource}[];
  causes:string[];consequences:string[];vocabulary:{word:string;definition:string}[];
  document:{type:string;title:string;date:string;origin:string;context:string;content:string;presentation:string;shows:string;limits:string;questions:string[];source:HistorySource};
  sources:HistorySource[];success_criteria:string[];remediation:string[];
}
export interface HistoryCatalogue {programme_version:string;themes:{id:string;title:string;subtitle:string}[];chapters:{chapter:string;code:string;title:string;theme:string;period:string}[]}
