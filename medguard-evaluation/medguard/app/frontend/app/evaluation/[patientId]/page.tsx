'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { PatientProfile, Event, MedGuardAnalysis, Stage1Response, Stage2Response } from '@/types/api';
import { fetchStageData, apiClient } from '@/lib/api';
import PatientHistoryTab from '@/components/information/PatientHistoryTab';
import Stage1Form from '@/components/evaluation/Stage1Form';
import Stage2Form from '@/components/evaluation/Stage2Form';

export default function EvaluationPage() {
  const params = useParams();
  const patientId = params.patientId as string;
  const router = useRouter();
  
  // Core state
  const [currentStage, setCurrentStage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Data state
  const [patient, setPatient] = useState<PatientProfile | null>(null);
  const [events, setEvents] = useState<Event[]>([]);
  const [analysisDate, setAnalysisDate] = useState<string | null>(null);
  // Analysis state
  const [medguardAnalysis, setMedguardAnalysis] = useState<MedGuardAnalysis | null>(null);
  
  // Tab state
  const [activeLeftTab, setActiveLeftTab] = useState('patient-history');
  
  // Load data based on current stage
  useEffect(() => {
    loadStageData();
  }, [patientId, currentStage]);
  
  const loadStageData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchStageData(patientId, currentStage);
      
      setPatient(data.patient);
      setAnalysisDate(data.analysisDate.analysis_date);
      setEvents(data.events);
      
      // Analysis data loading
      if ('medguardAnalysis' in data) {
        setMedguardAnalysis(data.medguardAnalysis);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };
  
  const handleStageComplete = () => {
    // Two-stage flow: 1 → 2 → Home
    if (currentStage === 1) {
      setCurrentStage(2);
    } else if (currentStage === 2) {
      router.push('/');
    }
  };

  // Auto-switch left tab based on stage
  useEffect(() => {
    switch (currentStage) {
      case 1:
        setActiveLeftTab('patient-history');
        break;
      case 2:
        setActiveLeftTab('medguard-analysis');
        break;
    }
  }, [currentStage]);

  const handleStage1Submit = async (data: Stage1Response) => {
    await apiClient.saveEvaluation({
      stage: 1,
      patient_id: patientId,
      data: data
    });
    
    handleStageComplete();
  };

  const handleStage2Submit = async (data: Stage2Response) => {
    try {
      await apiClient.saveEvaluation({
        stage: 2,
        patient_id: patientId,
        data
      });
      handleStageComplete();
    } catch (error) {
      console.error('Error saving Stage 2 evaluation:', error);
      setError('Failed to save Stage 2 evaluation');
    }
  };

  // Filter matched_filters to only those active at analysis_date
  // Matches backend logic: start_date < at_date AND end_date > at_date
  const getActiveFilters = () => {
    if (!patient?.matched_filters || !analysisDate) return [];

    const atDate = new Date(analysisDate);
    return patient.matched_filters.filter(filter => {
      const startDate = new Date(filter.start_date);
      const endDate = new Date(filter.end_date);
      return startDate < atDate && endDate > atDate;
    });
  };

  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-lg">Loading patient data...</div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-red-600">Error: {error}</div>
      </div>
    );
  }
  
  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Panel - Information Display (60%) */}
      <div className="w-3/5 border-r border-gray-200 bg-white flex flex-col">
        {/* Tab Navigation */}
        <div className="border-b border-gray-200">
          <nav className="flex space-x-4 px-4" aria-label="Tabs">
            <TabButton
              active={activeLeftTab === 'patient-history'}
              onClick={() => setActiveLeftTab('patient-history')}
              label="Patient History"
              available={true}
            />
            <TabButton
              active={activeLeftTab === 'medguard-analysis'}
              onClick={() => setActiveLeftTab('medguard-analysis')}
              label="MedGuard Analysis"
              available={currentStage >= 2}
            />
          </nav>
        </div>
        
        {/* Content Area */}
        <div className="flex-1 overflow-auto p-4">
          {activeLeftTab === 'patient-history' && patient && (
            <PatientHistoryTab
              patient={patient}
              events={events}
              smrDate={analysisDate}
              currentStage={currentStage}
            />
          )}
          
          {activeLeftTab === 'medguard-analysis' && medguardAnalysis && (
            <div>
              <h3 className="text-lg font-semibold mb-4">MedGuard Analysis</h3>

              {/* Intervention Required Summary */}
              <div className={`border-2 rounded-xl p-4 shadow-sm mb-6 ${
                medguardAnalysis.intervention_required
                  ? 'bg-red-50 border-red-200'
                  : 'bg-green-50 border-green-200'
              }`}>
                <div className="flex items-center justify-between">
                  <span className={`font-semibold ${
                    medguardAnalysis.intervention_required ? 'text-red-900' : 'text-green-900'
                  }`}>
                    Intervention Required:
                  </span>
                  <span className={`px-3 py-1.5 rounded-full text-sm font-bold ${
                    medguardAnalysis.intervention_required
                      ? 'bg-red-200 text-red-900'
                      : 'bg-green-200 text-green-900'
                  }`}>
                    {medguardAnalysis.intervention_required ? 'Yes' : 'No'}
                  </span>
                </div>
              </div>

              {/* Detailed Analysis Sections - in prompt order */}
              <div className="space-y-4">
                <AnalysisSection title="Patient Review" content={medguardAnalysis.patient_review} />

                {/* Clinical Issues */}
                {medguardAnalysis.clinical_issues.length > 0 && (
                  <div className="border rounded-lg p-4 bg-white shadow-sm">
                    <h4 className="font-medium mb-4">Clinical Issues</h4>
                    <div className="space-y-3">
                      {medguardAnalysis.clinical_issues.map((issue, idx) => (
                        <div key={idx} className="border-l-4 pl-3 py-2" style={{
                          borderLeftColor: issue.intervention_required ? '#dc2626' : '#2563eb'
                        }}>
                          <div className="flex items-start justify-between mb-2">
                            <h5 className="font-semibold text-gray-900">Issue {idx + 1}</h5>
                            <span className={`ml-3 px-2 py-1 rounded-full text-xs font-medium whitespace-nowrap ${
                              issue.intervention_required
                                ? 'bg-red-100 text-red-800'
                                : 'bg-blue-100 text-blue-800'
                            }`}>
                              {issue.intervention_required ? 'Intervention Required' : 'No Intervention'}
                            </span>
                          </div>
                          <p className="font-medium text-gray-800 mb-1">{issue.issue}</p>
                          <p className="text-sm text-gray-700 whitespace-pre-wrap">{issue.evidence}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <AnalysisSection title="Intervention" content={medguardAnalysis.intervention} />

                {/* Intervention Probability */}
                <div className="border rounded-lg p-4 bg-white shadow-sm">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium">Intervention Probability</h4>
                    <span className="text-2xl font-bold text-blue-600">
                      {Math.round(medguardAnalysis.intervention_probability * 100)}%
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    Probability that an intervention is required for this patient
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Right Panel - Evaluation Forms (40%) */}
      <div className="w-2/5 bg-white flex flex-col">
        {/* Patient ID Header with Home Button */}
        <div className="bg-gray-100 px-4 py-3 border-b border-gray-200 flex justify-between items-center">
          <div className="text-lg font-semibold">Patient ID: {patientId}</div>
          <button
            onClick={() => window.location.href = '/'}
            className="px-3 py-1.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors flex items-center"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            Home
          </button>
        </div>
        
        {/* Stage Tabs - Two stages */}
        <div className="border-b border-gray-200">
          <nav className="flex" aria-label="Stage tabs">
            <StageTab
              stage={1}
              active={currentStage === 1}
              completed={currentStage > 1}
              onClick={() => setCurrentStage(1)}
            />
            <StageTab
              stage={2}
              active={currentStage === 2}
              completed={false}
              onClick={() => currentStage >= 2 && setCurrentStage(2)}
            />
          </nav>
        </div>
        
        {/* Form Content - Two stages */}
        <div className="flex-1 overflow-auto p-4">
          {currentStage === 1 && (
            <Stage1Form onSubmit={handleStage1Submit} />
          )}
          
          {currentStage === 2 && (
            <Stage2Form
              onSubmit={handleStage2Submit}
              matchedFilters={getActiveFilters()}
              medguardAnalysis={medguardAnalysis}
            />
          )}
        </div>
      </div>
    </div>
  );
}

// Component helpers
function TabButton({ active, onClick, label, available }: {
  active: boolean;
  onClick: () => void;
  label: string;
  available: boolean;
}) {
  return (
    <button
      className={`
        py-2 px-1 border-b-2 font-medium text-sm transition-colors
        ${!available ? 'text-gray-400 cursor-not-allowed border-transparent' : 
          active ? 'border-blue-500 text-blue-600' : 
          'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
      `}
      onClick={available ? onClick : undefined}
      disabled={!available}
    >
      {label}
    </button>
  );
}

function StageTab({ stage, active, completed, onClick }: {
  stage: number;
  active: boolean;
  completed: boolean;
  onClick: () => void;
}) {
  return (
    <button
      className={`
        flex-1 py-3 px-4 text-sm font-medium transition-colors
        ${active ? 'bg-white text-blue-600 border-b-2 border-blue-600' :
          completed ? 'bg-gray-50 text-green-600 hover:bg-gray-100' :
          'bg-gray-50 text-gray-400 cursor-not-allowed'}
      `}
      onClick={onClick}
      disabled={!completed && !active}
    >
      <div className="flex items-center justify-center">
        {completed && <span className="mr-1">✓</span>}
        Stage {stage}
      </div>
    </button>
  );
}

function AnalysisSection({ title, content }: { title: string; content: string }) {
  return (
    <div className="border rounded-lg p-4">
      <h4 className="font-medium mb-2">{title}</h4>
      <div className="text-sm text-gray-700 whitespace-pre-wrap">{content}</div>
    </div>
  );
}