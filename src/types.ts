export type KCSEGrade = 'A' | 'A-' | 'B+' | 'B' | 'B-' | 'C+' | 'C' | 'C-' | 'D+' | 'D' | 'D-' | 'E';

export type UserRole = 'student' | 'admin';

export interface SubjectGrade {
  subject: string;
  grade: KCSEGrade;
  points: number; // 1 to 12
}

export interface StudentProfile {
  uid: string;
  fullName: string;
  indexNumber: string;
  kcseMeanGrade: KCSEGrade;
  kcseMeanPoints: number; // e.g. 81 for A, down to 7 for E
  grades: Record<string, KCSEGrade>;
  interests: string[];
  skills: string[];
  strengths: string[];
  aspirations: string[];
  calculatedClusterScore?: number; // estimated KUCCPS cluster points
  updatedAt?: string;
}

export interface UniversityOffering {
  name: string;
  location: string;
  type: 'Public' | 'Private';
  lastCutoffPoints: number;
}

export interface ProgrammeInfo {
  id: string;
  code: string;
  name: string;
  faculty: string;
  durationYears: number;
  overview: string;
  admissionRequirements: {
    minimumMeanGrade: KCSEGrade;
    minimumMeanPoints: number;
    requiredSubjects: { subject: string; minGrade: KCSEGrade }[];
    clusterSubjectGroup: string;
  };
  universities: UniversityOffering[];
  careerPathways: string[];
  recommendedSkills: string[];
  certifications: string[];
  historicalCutoffs: {
    year: string;
    cutoffPoints: number;
  }[];
  category: 'Computing & IT' | 'Engineering' | 'Health Sciences' | 'Business & Economics' | 'Natural Sciences' | 'Humanities & Social Sciences';
}

export interface ShapExplanation {
  programmeId: string;
  featureImportances: Record<string, number>; // feature -> relative score e.g. 0.35
  explanationText: string;
  positiveDrivers: string[];
  potentialGaps: string[];
}

export interface RecommendationResult {
  programmeId: string;
  rank: number;
  confidence: number; // percentage, e.g. 94.5
  matchRationale: string;
  shapExplanation: ShapExplanation;
  programme: ProgrammeInfo;
  // Official KUCCPS Cluster Metrics
  calculatedClusterScore: number; // Candidate's Cluster Weighted Points (CWP) out of 48.0
  clusterGroupCode: string; // e.g. "Cluster 19: Computing & IT"
  clusterSubjectBreakdown: { subject: string; grade: KCSEGrade; points: number }[];
  rawClusterTotal: number; // sum of 4 cluster subjects (max 48)
  aggregatePoints: number; // candidate best 7 total (max 84)
  targetCutoff: number; // benchmark university cutoff points
  cutoffDifference: number; // CWP - benchmark cutoff (positive = qualified)
  qualifiedUniversitiesCount: number; // Count of universities where student exceeds cutoff
  totalUniversitiesOffering: number;
  // Prerequisite Subject Validation for KCSE
  prerequisitesMet: boolean;
  missingPrerequisites: { subject: string; requiredGrade: KCSEGrade; candidateGrade?: KCSEGrade }[];
  satisfiedPrerequisites: { subject: string; requiredGrade: KCSEGrade; candidateGrade: KCSEGrade }[];
}

export interface FeedbackEntry {
  id: string;
  uid: string;
  programmeId: string;
  programmeName: string;
  rating: number; // 1 - 5
  satisfactionScore: number; // 1 - 10
  plannedProgramme?: string;
  comments: string;
  timestamp: string;
}

export interface AdminAuditLog {
  id: string;
  timestamp: string;
  action: 'recommendation_run' | 'programme_update' | 'cutoff_adjusted';
  actorName: string;
  studentIndex?: string;
  details: string;
  metadata?: Record<string, string | number>;
}

