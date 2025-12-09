'use client';

import { useState, useEffect } from 'react';
import { Stage2Response, MedGuardAnalysis } from '@/types/api';

interface Stage2FormProps {
  onSubmit: (data: Stage2Response) => Promise<void>;
  matchedFilters?: Array<{
    filter_id: number;
    start_date: string;
    end_date: string;
    description: string;
  }>;
  medguardAnalysis?: MedGuardAnalysis | null;
}

const FAILURE_MODES = [
  { value: 'hallucination', label: 'Hallucinations (fabricated facts, drugs, studies, or patient history)' },
  { value: 'knowledge_gap', label: 'Knowledge Gaps (outdated or missing specialized knowledge)' },
  { value: 'safety_critical_omission', label: 'Safety-Critical Omissions (missed contraindications, interactions, or red flags)' },
  { value: 'non_critical_omission', label: 'Non-Critical Omissions (incomplete assessment of minor details)' },
  { value: 'input_processing_error', label: 'Input Processing Errors (misreading or misinterpreting patient information)' },
  { value: 'reasoning_error', label: 'Reasoning Errors (illogical clinical conclusions despite correct information)' },
  { value: 'quantitative_error', label: 'Quantitative Errors (mathematical, dosing, or lab value calculation errors)' },
  { value: 'confidence_calibration_error', label: 'Confidence Calibration Errors (inappropriate certainty levels)' },
  { value: 'guideline_non_adherence', label: 'Guideline Non-Adherence (conflicts with established clinical guidelines)' },
  { value: 'other', label: 'Other (specify)' }
];

export default function Stage2Form({ onSubmit, matchedFilters = [], medguardAnalysis }: Stage2FormProps) {
  const [formData, setFormData] = useState<Stage2Response>({
    data_error: false,
    data_error_explanation: '',
    agrees_with_rules: null,
    rules_assessment_reasoning: '',
    medguard_identified_rule_issues: null,
    medguard_addressed_rule_issues: null,
    issue_assessments: [],
    issue_reasoning: [],
    missed_issues: null,
    missed_issues_detail: '',
    medguard_specific_intervention: null,
    medguard_specific_intervention_reasoning: '',
    intervention_should_be: '',
    failure_modes: [],
    failure_mode_explanations: {},
  });

  const [submitting, setSubmitting] = useState(false);

  // Initialize issue assessments array when medguardAnalysis changes
  useEffect(() => {
    if (medguardAnalysis && medguardAnalysis.clinical_issues.length > 0) {
      const issueCount = medguardAnalysis.clinical_issues.length;
      if (!formData.issue_assessments || formData.issue_assessments.length !== issueCount) {
        setFormData(prev => ({
          ...prev,
          issue_assessments: new Array(issueCount).fill(null),
          issue_reasoning: new Array(issueCount).fill(''),
        }));
      }
    }
  }, [medguardAnalysis]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      setSubmitting(true);
      await onSubmit(formData);
    } catch (error) {
      console.error('Failed to submit evaluation:', error);
      alert('Failed to save evaluation. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const isFormValid = () => {
    // If data error is checked, require explanation
    if (formData.data_error && (!formData.data_error_explanation || formData.data_error_explanation.trim() === '')) {
      return false;
    }

    // Require intervention assessment
    if (formData.medguard_specific_intervention === null) return false;

    // Only require Clinical Error Rules questions if rules were flagged
    if (matchedFilters.length > 0) {
      if (formData.agrees_with_rules === null) return false;

      // If user agrees with rules, require follow-up questions
      if (formData.agrees_with_rules === 'yes') {
        if (formData.medguard_identified_rule_issues === null) return false;
        if (formData.medguard_addressed_rule_issues === null) return false;
      }
    }

    // Require all issue assessments to be filled if there are issues
    if (medguardAnalysis && medguardAnalysis.clinical_issues.length > 0) {
      if (!formData.issue_assessments || formData.issue_assessments.some(assessment => assessment === null)) {
        return false;
      }
    }

    // Require missed issues question to be answered
    if (formData.missed_issues === null) return false;

    // If missed issues is yes, require detail
    if (formData.missed_issues === 'yes' && (!formData.missed_issues_detail || formData.missed_issues_detail.trim() === '')) {
      return false;
    }

    // Check if failure mode analysis is required
    const needsFailureAnalysis = formData.medguard_specific_intervention === 'no' ||
                                formData.medguard_specific_intervention === 'partial' ||
                                formData.missed_issues === 'yes';

    if (needsFailureAnalysis) {
      if (!formData.failure_modes || formData.failure_modes.length === 0) return false;

      // Check if "other" is selected but no explanation provided
      if (formData.failure_modes.includes('other')) {
        const otherExplanation = formData.failure_mode_explanations?.['other'];
        if (!otherExplanation || otherExplanation.trim() === '') return false;
      }
    }

    // Check if intervention follow-up field is required
    const needsInterventionField = medguardAnalysis?.intervention_required === true &&
                                   (formData.medguard_specific_intervention === 'no' ||
                                    formData.medguard_specific_intervention === 'partial');

    if (needsInterventionField && (!formData.intervention_should_be || formData.intervention_should_be.trim() === '')) {
      return false;
    }

    return true;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  // Derive agreement status and case information
  const getAgreementInfo = () => {
    const hasFilters = matchedFilters.length > 0;
    const medguardFlagged = medguardAnalysis?.intervention_required === true;
    const inAgreement = (hasFilters && medguardFlagged) || (!hasFilters && !medguardFlagged);

    if (hasFilters && medguardFlagged) {
      return {
        inAgreement: true,
        title: "Both Systems Identified Issues",
        description: "Both Clinical Error Rules and MedGuard flagged this case as requiring intervention."
      };
    } else if (hasFilters && !medguardFlagged) {
      return {
        inAgreement: false,
        title: "Disagreement: Rules Flagged, MedGuard Did Not",
        description: "Clinical Error Rules identified this case as requiring intervention, but MedGuard did not flag it. This represents a potential false negative from MedGuard."
      };
    } else if (!hasFilters && medguardFlagged) {
      return {
        inAgreement: false,
        title: "Disagreement: MedGuard Flagged, Rules Did Not",
        description: "MedGuard identified this case as requiring intervention, but no Clinical Error Rules were triggered. This could represent a true positive that rules missed, or a false positive from MedGuard."
      };
    } else {
      return {
        inAgreement: true,
        title: "Both Systems Found No Issues",
        description: "Neither Clinical Error Rules nor MedGuard flagged this case as requiring intervention. This represents agreement that no intervention is needed."
      };
    }
  };

  // Get dynamic explanatory text for MedGuard Question 1
  const getMedGuardQ1ExplanatoryText = () => {
    if (medguardAnalysis?.intervention_required === true) {
      return {
        yes: "MedGuard correctly identified that an intervention is required",
        no: "MedGuard incorrectly flagged this case - no intervention is actually required"
      };
    } else {
      return {
        yes: "MedGuard correctly determined that no intervention is required",
        no: "MedGuard incorrectly missed an issue - an intervention is actually required"
      };
    }
  };

  // Get dynamic explanatory text for MedGuard Question 2
  const getMedGuardQ2ExplanatoryText = () => {
    if (medguardAnalysis?.intervention_required === true) {
      return {
        yes: "MedGuard's proposed intervention is appropriate",
        no: "MedGuard's proposed intervention is inappropriate",
        partial: "MedGuard's proposed intervention is partially appropriate",
        na: "Not applicable - cannot assess a specific intervention when no intervention is required"
      };
    } else {
      return {
        yes: "MedGuard correctly determined no specific intervention is required",
        no: "MedGuard failed to specify an intervention when one is needed"
      };
    }
  };

  // Get available options for MedGuard Question 2
  const getMedGuardQ2Options = () => {
    if (medguardAnalysis?.intervention_required === true) {
      return [
        { value: 'yes', label: 'Yes' },
        { value: 'no', label: 'No' },
        { value: 'partial', label: 'Partial' },
        { value: 'na', label: 'N/A' }
      ];
    } else {
      return [
        { value: 'yes', label: 'Yes' },
        { value: 'no', label: 'No' }
      ];
    }
  };

  // Check if intervention follow-up field should be shown
  const shouldShowInterventionField = () => {
    if (medguardAnalysis?.intervention_required === true) {
      return formData.medguard_specific_intervention === 'no' || formData.medguard_specific_intervention === 'partial';
    } else {
      return formData.medguard_specific_intervention === 'no';
    }
  };

  // Get dynamic intervention field description
  const getInterventionFieldDescription = () => {
    if (medguardAnalysis?.intervention_required === true) {
      if (formData.medguard_specific_intervention === 'no') {
        return "Describe the appropriate intervention that should replace MedGuard's proposal.";
      } else if (formData.medguard_specific_intervention === 'partial') {
        return "Describe what additional intervention(s) are needed or how MedGuard's proposal should be modified.";
      }
      return "Please describe the correct intervention.";
    } else {
      return "Please describe the intervention that MedGuard should have identified and proposed for this case.";
    }
  };

  // Check if failure mode analysis should be shown
  const shouldShowFailureAnalysis = () => {
    return formData.medguard_specific_intervention === 'no' ||
           formData.medguard_specific_intervention === 'partial' ||
           formData.missed_issues === 'yes';
  };

  // Handle failure mode selection
  const handleFailureModeChange = (failureMode: string, checked: boolean) => {
    setFormData(prev => {
      const newFailureModes = checked 
        ? [...(prev.failure_modes || []), failureMode]
        : (prev.failure_modes || []).filter(mode => mode !== failureMode);
      
      const newExplanations = { ...prev.failure_mode_explanations };
      if (!checked) {
        delete newExplanations[failureMode];
      }
      
      return {
        ...prev,
        failure_modes: newFailureModes,
        failure_mode_explanations: newExplanations
      };
    });
  };

  // Handle failure mode explanation change
  const handleFailureModeExplanationChange = (failureMode: string, explanation: string) => {
    setFormData(prev => ({
      ...prev,
      failure_mode_explanations: {
        ...prev.failure_mode_explanations,
        [failureMode]: explanation
      }
    }));
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg mb-6">
        <h3 className="text-xl font-bold text-gray-900 mb-2">Stage 2</h3>
        <h4 className="text-lg font-semibold text-blue-900 mb-2">Ground Truth Validation & MedGuard Analysis</h4>
        <p className="text-sm text-gray-700">
          Evaluate the Clinical Error Rules assessment and MedGuard's analysis against your clinical judgment.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex-1 flex flex-col">
        <div className="flex-1 space-y-6 overflow-y-auto">
          {/* Data Error Flag */}
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
            <label className="flex items-start space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.data_error}
                onChange={(e) => setFormData({ ...formData, data_error: e.target.checked })}
                className="mt-1 rounded border-amber-300 text-amber-600 focus:ring-2 focus:ring-amber-500"
              />
              <div className="flex-1">
                <span className="font-medium text-amber-900">Data Error Suspected</span>
                <p className="text-sm text-amber-700 mt-1">
                  Check this box if you suspect the underlying data for this case is incorrect or incomplete
                </p>
              </div>
            </label>

            {formData.data_error && (
              <div className="mt-3">
                <textarea
                  value={formData.data_error_explanation || ''}
                  onChange={(e) => setFormData({ ...formData, data_error_explanation: e.target.value })}
                  rows={3}
                  placeholder="Please explain what data error you suspect..."
                  className="w-full px-3 py-2 border border-amber-300 rounded-lg text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500 resize-none bg-white"
                  required
                />
              </div>
            )}
          </div>

          {/* Clinical Error Rules Information with Agreement Status */}
          <div className={`border rounded-xl p-4 ${
            getAgreementInfo().inAgreement
              ? 'bg-green-50 border-green-300'
              : 'bg-red-50 border-red-200'
          }`}>
            <h5 className={`font-semibold mb-2 ${
              getAgreementInfo().inAgreement ? 'text-green-900' : 'text-red-700'
            }`}>
              {getAgreementInfo().title}
            </h5>
            <p className={`text-sm mb-4 ${
              getAgreementInfo().inAgreement ? 'text-green-700' : 'text-red-700'
            }`}>
              {getAgreementInfo().description}
            </p>
            {matchedFilters.length > 0 ? (
              <div className="space-y-3">
                <p className={`text-sm font-medium ${
                  getAgreementInfo().inAgreement ? 'text-green-800' : 'text-red-700'
                }`}>
                  This case triggered the following Clinical Error Rule(s):
                </p>
                {matchedFilters.map((filter, index) => (
                  <div key={index} className={`bg-white rounded-lg p-3 border ${
                    getAgreementInfo().inAgreement ? 'border-green-200' : 'border-red-200'
                  }`}>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                            getAgreementInfo().inAgreement
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-700'
                          }`}>
                            Clinical Error Rule {filter.filter_id}
                          </span>
                        </div>
                        <p className="text-sm text-gray-700 mb-2">{filter.description}</p>
                        <p className="text-xs text-gray-500">
                          Active period: {formatDate(filter.start_date)} - {formatDate(filter.end_date)}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className={`text-sm font-medium ${
                getAgreementInfo().inAgreement ? 'text-green-800' : 'text-red-700'
              }`}>
                No Clinical Error Rules were triggered for this case.
              </p>
            )}
          </div>

          {/* Ground Truth Evaluation - Only show if rules were flagged */}
          {matchedFilters.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
              <h5 className="font-semibold text-gray-900 mb-4">Ground Truth Evaluation</h5>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Do you agree that the clinical error rule has been correctly triggered for this case?
                  </label>
                  <div className="flex flex-wrap gap-4 mb-3">
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="radio"
                        checked={formData.agrees_with_rules === 'yes'}
                        onChange={() => setFormData({ ...formData, agrees_with_rules: 'yes' })}
                        className="rounded-full border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500"
                      />
                      <span className="font-medium text-gray-900">Yes</span>
                    </label>
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="radio"
                        checked={formData.agrees_with_rules === 'no'}
                        onChange={() => setFormData({ ...formData, agrees_with_rules: 'no' })}
                        className="rounded-full border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500"
                      />
                      <span className="font-medium text-gray-900">No</span>
                    </label>
                  </div>
                  <textarea
                    value={formData.rules_assessment_reasoning || ''}
                    onChange={(e) => setFormData({ ...formData, rules_assessment_reasoning: e.target.value })}
                    rows={2}
                    placeholder="Please explain your reasoning (optional)"
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                  />
                </div>
              </div>
            </div>
          )}

          {/* MedGuard Issue Evaluation */}
          {medguardAnalysis && medguardAnalysis.clinical_issues.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
              <h5 className="font-semibold text-gray-900 mb-4">MedGuard Issue Evaluation</h5>

              {/* Clinical Error Rules follow-up question */}
              {formData.agrees_with_rules === 'yes' && (
                <div className="mb-6 pb-4 border-b border-gray-200">
                  <label className="block text-sm font-medium text-gray-900 mb-2">
                    Did MedGuard correctly identify the issue(s) flagged by the clinical error rules?
                  </label>
                  <div className="flex gap-4">
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="radio"
                        checked={formData.medguard_identified_rule_issues === 'yes'}
                        onChange={() => setFormData({ ...formData, medguard_identified_rule_issues: 'yes' })}
                        className="rounded-full border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500"
                      />
                      <span className="text-sm font-medium text-gray-900">Yes</span>
                    </label>
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="radio"
                        checked={formData.medguard_identified_rule_issues === 'no'}
                        onChange={() => setFormData({ ...formData, medguard_identified_rule_issues: 'no' })}
                        className="rounded-full border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500"
                      />
                      <span className="text-sm font-medium text-gray-900">No</span>
                    </label>
                  </div>
                </div>
              )}

              <p className="text-sm text-gray-600 mb-4">
                For each issue identified by MedGuard (see left panel for details), indicate whether it is correct:
              </p>

              <div className="space-y-4">
                {medguardAnalysis.clinical_issues.map((issue, idx) => (
                  <div key={idx} className="border border-gray-200 rounded-lg p-3">
                    <label className="block text-sm font-medium text-gray-900 mb-2">
                      Issue {idx + 1}
                    </label>
                    <div className="flex gap-4 mb-2">
                      <label className="flex items-center space-x-2 cursor-pointer">
                        <input
                          type="radio"
                          checked={formData.issue_assessments?.[idx] === true}
                          onChange={() => {
                            const newAssessments = [...(formData.issue_assessments || [])];
                            newAssessments[idx] = true;
                            setFormData({ ...formData, issue_assessments: newAssessments });
                          }}
                          className="rounded-full border-gray-300 text-green-600 focus:ring-2 focus:ring-green-500"
                        />
                        <span className="text-sm font-medium text-gray-900">✓ Correct</span>
                      </label>
                      <label className="flex items-center space-x-2 cursor-pointer">
                        <input
                          type="radio"
                          checked={formData.issue_assessments?.[idx] === false}
                          onChange={() => {
                            const newAssessments = [...(formData.issue_assessments || [])];
                            newAssessments[idx] = false;
                            setFormData({ ...formData, issue_assessments: newAssessments });
                          }}
                          className="rounded-full border-gray-300 text-red-600 focus:ring-2 focus:ring-red-500"
                        />
                        <span className="text-sm font-medium text-gray-900">✗ Incorrect</span>
                      </label>
                    </div>
                    <textarea
                      value={formData.issue_reasoning?.[idx] || ''}
                      onChange={(e) => {
                        const newReasoning = [...(formData.issue_reasoning || [])];
                        newReasoning[idx] = e.target.value;
                        setFormData({ ...formData, issue_reasoning: newReasoning });
                      }}
                      rows={2}
                      placeholder="Reasoning (optional)"
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Missed Issues Question - Always shown */}
          <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
            <h5 className="font-semibold text-gray-900 mb-4">Missed Issues Assessment</h5>
            <label className="block text-sm font-medium text-gray-900 mb-2">
              Were there any issues that MedGuard missed that required an intervention?
            </label>
            <div className="flex gap-4 mb-3">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="radio"
                  checked={formData.missed_issues === 'yes'}
                  onChange={() => setFormData({ ...formData, missed_issues: 'yes' })}
                  className="rounded-full border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-gray-900">Yes</span>
              </label>
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="radio"
                  checked={formData.missed_issues === 'no'}
                  onChange={() => setFormData({ ...formData, missed_issues: 'no' })}
                  className="rounded-full border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-gray-900">No</span>
              </label>
            </div>
            {formData.missed_issues === 'yes' && (
              <textarea
                value={formData.missed_issues_detail || ''}
                onChange={(e) => setFormData({ ...formData, missed_issues_detail: e.target.value })}
                rows={3}
                placeholder="Please describe the missed issues..."
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                required
              />
            )}
          </div>

          {/* MedGuard Intervention Evaluation */}
          <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
            <h5 className="font-semibold text-gray-900 mb-4">MedGuard Intervention Evaluation</h5>

            {/* Clinical Error Rules follow-up question */}
            {formData.agrees_with_rules === 'yes' && (
              <div className="mb-6 pb-4 border-b border-gray-200">
                <label className="block text-sm font-medium text-gray-900 mb-2">
                  Did MedGuard's intervention correctly address the issue flagged by the clinical error rules?
                </label>
                <div className="flex gap-4">
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="radio"
                      checked={formData.medguard_addressed_rule_issues === 'yes'}
                      onChange={() => setFormData({ ...formData, medguard_addressed_rule_issues: 'yes' })}
                      className="rounded-full border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500"
                    />
                    <span className="text-sm font-medium text-gray-900">Yes</span>
                  </label>
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="radio"
                      checked={formData.medguard_addressed_rule_issues === 'no'}
                      onChange={() => setFormData({ ...formData, medguard_addressed_rule_issues: 'no' })}
                      className="rounded-full border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500"
                    />
                    <span className="text-sm font-medium text-gray-900">No</span>
                  </label>
                </div>
              </div>
            )}

            {/* Question: Specific Intervention */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Did MedGuard recommend an appropriate intervention for the patient?
              </label>
              <div className="flex flex-wrap gap-4 mb-3">
                {getMedGuardQ2Options().map((option) => (
                  <label key={option.value} className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="radio"
                      checked={formData.medguard_specific_intervention === option.value}
                      onChange={() => setFormData({ ...formData, medguard_specific_intervention: option.value as 'yes' | 'no' | 'partial' | 'na' })}
                      className="rounded-full border-gray-300 text-green-600 focus:ring-2 focus:ring-green-500"
                    />
                    <span className="font-medium text-gray-900">{option.label}</span>
                  </label>
                ))}
              </div>
              
              {/* Dynamic explanatory text */}
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 mb-3">
                {Object.entries(getMedGuardQ2ExplanatoryText()).map(([key, value]) => (
                  <p key={key} className="text-sm text-gray-700">
                    <strong>{key.charAt(0).toUpperCase() + key.slice(1)}</strong> - {value}
                  </p>
                ))}
              </div>
              
              <textarea
                value={formData.medguard_specific_intervention_reasoning || ''}
                onChange={(e) => setFormData({ ...formData, medguard_specific_intervention_reasoning: e.target.value })}
                rows={2}
                placeholder="Explain your reasoning (optional)"
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500 resize-none"
              />
            </div>
          </div>

          {/* Intervention Follow-up Field */}
          {shouldShowInterventionField() && (
            <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
              <h5 className="font-semibold text-gray-900 mb-4">Intervention Details</h5>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {medguardAnalysis?.intervention_required === true
                    ? "What intervention should be made (or should have been proposed by MedGuard)?"
                    : "What intervention should MedGuard have proposed?"
                  }
                </label>
                <p className="text-sm text-gray-600 mb-3">
                  {getInterventionFieldDescription()}
                </p>
                <textarea
                  value={formData.intervention_should_be || ''}
                  onChange={(e) => setFormData({ ...formData, intervention_should_be: e.target.value })}
                  rows={4}
                  placeholder="Describe the correct intervention..."
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                  required
                />
              </div>
            </div>
          )}

          {/* Failure Mode Analysis */}
          {shouldShowFailureAnalysis() && (
            <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
              <h5 className="font-semibold text-gray-900 mb-4">Failure Mode Analysis</h5>
              <p className="text-sm text-gray-600 mb-4">
                Please select all failure modes that apply to MedGuard's performance on this case:
              </p>
              
              <div className="space-y-4">
                {FAILURE_MODES.map((failureMode) => (
                  <div key={failureMode.value} className="border border-gray-200 rounded-lg p-3">
                    <label className="flex items-start space-x-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.failure_modes?.includes(failureMode.value) || false}
                        onChange={(e) => handleFailureModeChange(failureMode.value, e.target.checked)}
                        className="mt-1 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500"
                      />
                      <div className="flex-1">
                        <span className="font-medium text-gray-900">{failureMode.label}</span>
                        {formData.failure_modes?.includes(failureMode.value) && (
                          <div className="mt-2">
                            <textarea
                              value={formData.failure_mode_explanations?.[failureMode.value] || ''}
                              onChange={(e) => handleFailureModeExplanationChange(failureMode.value, e.target.value)}
                              rows={2}
                              placeholder={
                                failureMode.value === 'other'
                                  ? "Please describe the failure mode (required)"
                                  : "Please provide details about this failure mode (optional)"
                              }
                              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                              required={failureMode.value === 'other'}
                            />
                          </div>
                        )}
                      </div>
                    </label>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Submit Button */}
        <div className="mt-6 pt-4 border-t border-gray-200">
          <button
            type="submit"
            disabled={!isFormValid() || submitting}
            className="w-full px-6 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold rounded-xl hover:from-blue-700 hover:to-indigo-700 disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed transition-all duration-200 shadow-md hover:shadow-lg"
          >
            {submitting ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Saving...
              </div>
            ) : (
              'Complete Evaluation'
            )}
          </button>
        </div>
      </form>
    </div>
  );
}