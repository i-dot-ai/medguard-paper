'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api';
import { PatientProfile } from '@/types/api';

export default function Home() {
  const [patients, setPatients] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [completedPatients, setCompletedPatients] = useState<string[]>([]);
  const [patientProfiles, setPatientProfiles] = useState<Record<string, PatientProfile>>({});

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const patientIds = await apiClient.getPatients();
      setPatients(patientIds);

      const completedPatientIds = await apiClient.getCompletedPatients();
      setCompletedPatients(completedPatientIds);

      // Load patient profiles for all patients
      const profiles: Record<string, PatientProfile> = {};
      for (const patientId of patientIds) {
        try {
          const profile = await apiClient.getPatient(patientId);
          profiles[patientId] = profile;
        } catch (err) {
          console.error(`Failed to load profile for patient ${patientId}`, err);
        }
      }
      setPatientProfiles(profiles);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load patients');
    } finally {
      setLoading(false);
    }
  };

  const availablePatients = patients.filter(patientId =>
    !completedPatients.includes(patientId)
  );

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleDateString('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto py-12 px-4">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          MedGuard Clinical Evaluation
        </h1>
        
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Select a Patient for Evaluation</h2>
          
          {loading && (
            <div className="text-gray-500">Loading patients...</div>
          )}
          
          {error && (
            <div className="text-red-600">Error: {error}</div>
          )}
          
          {!loading && !error && availablePatients.length === 0 && (
            <div className="text-gray-500">
              {patients.length === 0 
              ? "No patients found. Please ensure the backend is running and data is loaded."
              : "All available patients have been evaluated. Great work!"
              }
            </div>
          )}
          
          {!loading && !error && (
            <>
              {/* Available Patients List */}
              {availablePatients.length > 0 ? (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold mb-3">Available Patients</h3>
                  <ul className="space-y-2">
                    {availablePatients.map((patientId) => {
                      const profile = patientProfiles[patientId];
                      return (
                        <li key={patientId}>
                          <Link
                            href={`/evaluation/${patientId}`}
                            className="block px-4 py-3 border border-gray-200 rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors"
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-medium">Patient ID: {patientId}</span>
                              {profile && (
                                <div className="flex gap-4 text-sm text-gray-600">
                                  <span>{profile.sex || 'Unknown'}</span>
                                  <span>DOB: {formatDate(profile.date_of_birth)}</span>
                                </div>
                              )}
                            </div>
                          </Link>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              ) : (
                <div className="text-gray-500 mb-6">
                  {patients.length === 0
                    ? "No patients found. Please ensure the backend is running and data is loaded."
                    : "All available patients have been evaluated. Great work!"
                  }
                </div>
              )}

              {/* Completed Patients List */}
              {completedPatients.length > 0 && (
                <div className="pt-6 border-t border-gray-300">
                  <h3 className="text-lg font-semibold mb-3">Completed Patients</h3>
                  <div className="text-sm text-gray-600 mb-3">
                    {completedPatients.length} of {patients.length} patients completed
                    ({Math.round((completedPatients.length / patients.length) * 100)}%)
                  </div>
                  <ul className="space-y-2">
                    {completedPatients.map((patientId) => {
                      const profile = patientProfiles[patientId];
                      return (
                        <li key={patientId}>
                          <div className="px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <span className="font-medium text-gray-600">Patient ID: {patientId}</span>
                                <span className="text-sm text-green-600">✓ Completed</span>
                              </div>
                              {profile && (
                                <div className="flex gap-4 text-sm text-gray-600">
                                  <span>{profile.sex || 'Unknown'}</span>
                                  <span>DOB: {formatDate(profile.date_of_birth)}</span>
                                </div>
                              )}
                            </div>
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              )}
            </>
          )}

        </div>
        
        <div className="mt-8 p-4 bg-blue-50 rounded-lg">
          <h3 className="font-semibold text-blue-900 mb-2">Evaluation Instructions</h3>
          <div className="text-sm text-blue-800 space-y-2">
            <p><strong>Stage 1 - Information Sufficiency Check:</strong></p>
            <ul className="ml-4 space-y-1 list-disc list-inside">
              <li>Review the patient's clinical history and events in the left panel</li>
              <li>Confirm you have sufficient information to conduct a meaningful medication review</li>
              <li>If insufficient information, you'll be returned to the homepage</li>
            </ul>
            
            <p><strong>Stage 2 - Ground Truth Validation & MedGuard Analysis:</strong></p>
            <ul className="ml-4 space-y-1 list-disc list-inside">
              <li>Review the MedGuard Analysis Summary and detailed analysis in the left panel</li>
              <li>Evaluate Clinical Error Rules information (if any rules were triggered)</li>
              <li>Answer questions about whether Clinical Error Rules correctly identified clinical issues</li>
              <li>Assess MedGuard's analysis of intervention requirements and specific interventions</li>
              <li>If MedGuard made errors, provide details about what intervention should be made</li>
              <li>Select failure modes that explain any MedGuard performance issues</li>
              <li>Provide detailed explanations for selected failure modes</li>
            </ul>
            
            <p className="mt-2"><strong>Important:</strong> Your responses are NOT saved automatically. You must click &quot;Complete Evaluation&quot; to save your assessment.</p>
          </div>
        </div>
      </div>
    </div>
  );
}