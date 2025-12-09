import { useState } from 'react';
import { Event } from '@/types/api';

interface PrescriptionEvent extends Event {
  start_date?: string;
  end_date?: string;
  description?: string;
  snomed_code?: string;
  dosage?: string;
  units?: string;
  duration_days?: number;
  prescription_count?: number;
  average_course_length?: number;
  is_repeat_medication?: boolean;
}

interface PrescriptionCardProps {
  event: Event;
  smrDate: string | null;
  currentStage?: number;
}

export default function PrescriptionCard({ event, smrDate, currentStage }: PrescriptionCardProps) {
  const prescription = event as PrescriptionEvent;
  const isPreSMR = smrDate ? event.date < smrDate : true;
  
  // Check if prescription is active at SMR date
  const isActiveAtSMR = smrDate && prescription.start_date && prescription.end_date
    ? prescription.start_date < smrDate && prescription.end_date > smrDate
    : false;
  
  // For active prescriptions, don't show Post-SMR tag even if end date is after SMR
  const shouldShowPostSMR = !isActiveAtSMR && !isPreSMR && smrDate;
  
  // Hide duration and count for active prescriptions in stages 1-2
  const shouldHideDurationAndCount = isActiveAtSMR && (currentStage === 1 || currentStage === 2);

  return (
    <div className="border rounded-lg p-3 transition-colors hover:shadow-sm bg-white border-gray-200">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-800">
              Prescription
            </span>
            {isActiveAtSMR && (
              <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">
                Active at SMR
              </span>
            )}
            {shouldShowPostSMR && (
              <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-amber-100 text-amber-800">
                Post-SMR
              </span>
            )}
            {prescription.is_repeat_medication && (
              <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                Repeat
              </span>
            )}
          </div>
          
          {/* Medication Name */}
          <div className="font-medium text-gray-900 mb-1">
            {prescription.description || 'Unnamed medication'}
          </div>
          
          {/* Dosage Info */}
          {(prescription.dosage || prescription.units) && (
            <div className="text-sm text-gray-700 mb-1">
              {prescription.dosage && <span>{prescription.dosage}</span>}
              {prescription.units && <span className="ml-1">{prescription.units}</span>}
            </div>
          )}
          
          {/* Date Range */}
          <div className="text-sm text-gray-600">
            {prescription.start_date && (
              <div>
                <span className="font-medium">Start:</span> {new Date(prescription.start_date).toLocaleDateString('en-GB')}
              </div>
            )}
            {prescription.end_date && !isActiveAtSMR && (
              <div>
                <span className="font-medium">End:</span> {new Date(prescription.end_date).toLocaleDateString('en-GB')}
              </div>
            )}
            {isActiveAtSMR && (
              <div className="text-green-700 font-medium">
                Currently active
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Details */}
      <div className="mt-3 space-y-2">
          {prescription.duration_days && !shouldHideDurationAndCount && (
            <div className="text-sm">
              <span className="font-medium">Duration:</span> {prescription.duration_days} days
            </div>
          )}
          
          {prescription.prescription_count && !shouldHideDurationAndCount && (
            <div className="text-sm">
              <span className="font-medium">Prescription Count:</span> {prescription.prescription_count}
            </div>
          )}
          
          {prescription.average_course_length && !shouldHideDurationAndCount && (
            <div className="text-sm">
              <span className="font-medium">Average Course Length:</span> {prescription.average_course_length} days
            </div>
          )}
          
          {prescription.snomed_code && (
            <div className="text-sm">
              <span className="font-medium">SNOMED Code:</span> {prescription.snomed_code}
            </div>
          )}
          
          {prescription.is_repeat_medication !== undefined && (
            <div className="text-sm">
              <span className="font-medium">Repeat Medication:</span> {prescription.is_repeat_medication ? 'Yes' : 'No'}
            </div>
          )}
          
        {/* Other Details */}
        {event.details && Object.keys(event.details).length > 0 && (
          <div>
            <div className="text-xs font-medium text-gray-700 mb-1">Additional Details:</div>
            <div className="bg-gray-50 rounded p-2 text-xs font-mono">
              <pre className="whitespace-pre-wrap text-gray-700">
                {JSON.stringify(event.details, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}