import {
  PatientProfile,
  Event,
  MedGuardAnalysis,
  EvaluationAnalysis,
  EvaluationSubmission,
  SaveEvaluationResponse
} from '@/types/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private async fetch<T>(path: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`API Error: ${response.status} - ${error}`);
    }

    return response.json();
  }

  // Patient endpoints
  async getPatients(): Promise<string[]> {
    return this.fetch<string[]>('/patients');
  }

  async getPatient(patientId: string): Promise<PatientProfile> {
    return this.fetch<PatientProfile>(`/patients/${patientId}`);
  }

  async getCompletedPatients(): Promise<string[]> {
    return this.fetch<string[]>('/patients/completed');
  }

  // Event endpoints
  async getPreSMREvents(patientId: string): Promise<Event[]> {
    return this.fetch<Event[]>(`/patients/${patientId}/events/pre-smr`);
  }


  // Analysis endpoints

  async getMedGuardAnalysis(patientId: string): Promise<MedGuardAnalysis | null> {
    return this.fetch<MedGuardAnalysis | null>(
      `/patients/${patientId}/analysis/medguard`
    );
  }

  async getEvaluationAnalysis(patientId: string): Promise<EvaluationAnalysis | null> {
    return this.fetch<EvaluationAnalysis | null>(
      `/patients/${patientId}/analysis/evaluation`
    );
  }

  // Analysis Date endpoint
  async getAnalysisDate(patientId: string): Promise<{ patient_id: string; analysis_date: string }> {
    return this.fetch<{ patient_id: string; analysis_date: string }>(
      `/patients/${patientId}/analysis-date`
    );
  }

  // Evaluation submission
  async saveEvaluation(evaluation: EvaluationSubmission): Promise<SaveEvaluationResponse> {
    return this.fetch<SaveEvaluationResponse>(
      `/patients/${evaluation.patient_id}/evaluation`,
      {
        method: 'POST',
        body: JSON.stringify(evaluation),
      }
    );
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Helper functions for stage-based data fetching
export async function fetchStageData(patientId: string, stage: number) {
  const baseData = {
    patient: await apiClient.getPatient(patientId),
    analysisDate: await apiClient.getAnalysisDate(patientId),
  };

  switch (stage) {
    case 1:
      // Stage 1: Only pre-SMR events
      return {
        ...baseData,
        events: await apiClient.getPreSMREvents(patientId),
      };

    case 2:
      // Stage 2: Pre-SMR events + MedGuard analysis
      return {
        ...baseData,
        events: await apiClient.getPreSMREvents(patientId),
        medguardAnalysis: await apiClient.getMedGuardAnalysis(patientId),
      };

    default:
      throw new Error(`Invalid stage: ${stage}`);
  }
}