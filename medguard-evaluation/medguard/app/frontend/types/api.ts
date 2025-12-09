// API Types matching backend models

// Enums
export enum EventType {
  MEDICATION = "medication",
  GP_EVENT = "gp_event",
  GP_ENCOUNTER = "gp_encounter",
  INPATIENT_EPISODE = "inpatient_episode",
  AE_VISIT = "ae_visit",
  OUTPATIENT_VISIT = "outpatient_visit",
  ALLERGY = "allergy",
  SOCIAL_CARE_EVENT = "social_care_event",
  MEDICATION_CHANGE = "medication_change",
  PRESCRIPTION = "prescription"
}

export enum Gender {
  MALE = "Male",
  FEMALE = "Female",
  OTHER = "Other"
}

// Core Models
export interface FilterMatch {
  filter_id: number;
  start_date: string;
  end_date: string;
  description: string;
}

export interface PatientProfile {
  patient_link_id: number;
  patient_id?: number;
  date_of_birth?: string;
  sex?: string;
  ethnic_origin?: string;
  imd_score?: number;
  frailty_score?: number;
  mortality_risk_score?: number;
  deceased?: boolean;
  death_date?: string;
  restricted?: boolean;
  social_care_flag?: boolean;
  date_of_registration?: string;
  create_date?: string;
  qof_registers?: string;
  frailty_deficit_list?: string;
  matched_filters?: FilterMatch[];
  events?: Event[];
}

export interface Event {
  date: string;  // ISO date string
  event_type: EventType;
  description?: string;
  details?: Record<string, any>;
}

export interface Observation {
  description?: string;
  units?: string;
  value?: string;
  episodity?: string;
}

export interface GPEvent extends Event {
  event_type: EventType.GP_EVENT;
  observations?: Observation[];
  was_smr?: boolean;
  flag_smr?: boolean;  // Not displayed but present in data
}

export interface Medication {
  name: string;
  dosage?: string;
  frequency?: string;
  route?: string;
  start_date?: string;
  end_date?: string;
  indication?: string;
  prescriber?: string;
  status?: string;
}

// MedGuard Analysis Types
export interface ClinicalIssue {
  issue: string;
  evidence: string;
  intervention_required: boolean;
}

export interface MedGuardAnalysis {
  patient_review: string;
  clinical_issues: ClinicalIssue[];
  intervention: string;
  intervention_required: boolean;
  intervention_probability: number;
}

// Evaluation Analysis Types
export type AgreementType = "true-positive" | "false-positive" | "false-negative" | "true-negative";

export type FailureReason =
  | "hallucination"
  | "knowledge_gap"
  | "safety_critical_omission"
  | "non_critical_omission"
  | "input_processing_error"
  | "reasoning_error"
  | "quantitative_error"
  | "confidence_calibration_error"
  | "guideline_non_adherence";

export interface FailureAnalysis {
  reasoning: string;
  reason: FailureReason;
}

export interface InterventionAnalysis {
  reasoning: string;
  correct: boolean;
}

export interface EvaluationAnalysis {
  issue_correct: boolean;
  intervention_correct: boolean;
  agreement_type: AgreementType;
  intervention_analysis: InterventionAnalysis | null;
  failure_analysis: FailureAnalysis[];
}


// Stage Response Types for Clinician Forms
export interface Stage1Response {
  determination_possible: boolean | null;
  determination_possible_reasoning?: string;
}

export interface Stage2Response {
  // Data Error Flag
  data_error: boolean;
  data_error_explanation?: string;

  // Clinical Error Rules
  agrees_with_rules: 'yes' | 'no' | null;
  rules_assessment_reasoning?: string;

  // Clinical Error Rules follow-up (shown when agrees_with_rules === 'yes')
  medguard_identified_rule_issues?: 'yes' | 'no' | null;
  medguard_addressed_rule_issues?: 'yes' | 'no' | null;

  // MedGuard Issue Evaluation
  issue_assessments?: (boolean | null)[]; // Array of true/false/null for each issue
  issue_reasoning?: string[]; // Optional reasoning for each issue
  missed_issues: 'yes' | 'no' | null;
  missed_issues_detail?: string;

  // MedGuard Intervention Evaluation
  medguard_specific_intervention: 'yes' | 'no' | 'partial' | 'na' | null;
  medguard_specific_intervention_reasoning?: string;

  // Intervention follow-up fields
  intervention_should_be?: string; // "What intervention should be made?"

  // Failure mode analysis
  failure_modes?: string[]; // Array of selected failure mode categories
  failure_mode_explanations?: Record<string, string>; // Individual explanations for each failure mode
}

// Evaluation Submission
export interface EvaluationSubmission {
  stage: number;
  patient_id: string;
  data: Stage1Response | Stage2Response;
}

// Filter Types
export interface EventFilters {
  searchTerm: string;
  dateFrom?: string;
  dateTo?: string;
  eventTypes: EventType[];
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface SaveEvaluationResponse {
  success: boolean;
  message: string;
  filename: string;
}

// Helper type to check if an event is a GP Event
export function isGPEvent(event: Event): event is GPEvent {
  return event.event_type === EventType.GP_EVENT;
}