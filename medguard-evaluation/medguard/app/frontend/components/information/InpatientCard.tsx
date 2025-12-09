import { useState } from 'react';
import { Event } from '@/types/api';

interface InpatientEvent extends Event {
  admission_date?: string;
  admission_type_description?: string;
  admission_source_description?: string;
  admission_category_description?: string;
  expected_discharge_date?: string;
  transfer_date?: string;
  discharge_date?: string;
  discharge_method_description?: string;
  discharge_destination_description?: string;
  ward_description?: string;
  specialty_description?: string;
}

interface InpatientCardProps {
  event: Event;
  smrDate: string | null;
}

export default function InpatientCard({ event, smrDate }: InpatientCardProps) {
  const inpatient = event as InpatientEvent;
  const isPreSMR = smrDate ? event.date < smrDate : true;

  return (
    <div className="border rounded-lg p-3 transition-colors hover:shadow-sm bg-white border-gray-200">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-800">
              Inpatient Episode
            </span>
            {!isPreSMR && smrDate && (
              <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-amber-100 text-amber-800">
                Post-SMR
              </span>
            )}
          </div>
          
          {/* Primary Date */}
          <div className="text-sm text-gray-600 mb-2">
            {inpatient.admission_date && (
              <div>
                <span className="font-medium">Admission:</span> {new Date(inpatient.admission_date).toLocaleDateString('en-GB')}
              </div>
            )}
            {inpatient.discharge_date && (
              <div>
                <span className="font-medium">Discharge:</span> {new Date(inpatient.discharge_date).toLocaleDateString('en-GB')}
              </div>
            )}
          </div>
          
          {/* Key Info - Always Visible */}
          <div className="space-y-1">
            {inpatient.specialty_description && (
              <div className="text-sm">
                <span className="font-medium">Specialty:</span> {inpatient.specialty_description}
              </div>
            )}
            {inpatient.ward_description && (
              <div className="text-sm">
                <span className="font-medium">Ward:</span> {inpatient.ward_description}
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Details */}
      <div className="mt-3 space-y-2">
          {inpatient.admission_type_description && (
            <div className="text-sm">
              <span className="font-medium">Admission Type:</span> {inpatient.admission_type_description}
            </div>
          )}
          
          {inpatient.admission_source_description && (
            <div className="text-sm">
              <span className="font-medium">Admitted From:</span> {inpatient.admission_source_description}
            </div>
          )}
          
          {inpatient.admission_category_description && (
            <div className="text-sm">
              <span className="font-medium">Admission Category:</span> {inpatient.admission_category_description}
            </div>
          )}
          
          {inpatient.expected_discharge_date && (
            <div className="text-sm">
              <span className="font-medium">Expected Discharge:</span> {new Date(inpatient.expected_discharge_date).toLocaleDateString('en-GB')}
            </div>
          )}
          
          {inpatient.transfer_date && (
            <div className="text-sm">
              <span className="font-medium">Transfer Date:</span> {new Date(inpatient.transfer_date).toLocaleDateString('en-GB')}
            </div>
          )}
          
          {inpatient.discharge_method_description && (
            <div className="text-sm">
              <span className="font-medium">Discharge Method:</span> {inpatient.discharge_method_description}
            </div>
          )}
          
          {inpatient.discharge_destination_description && (
            <div className="text-sm">
              <span className="font-medium">Discharged To:</span> {inpatient.discharge_destination_description}
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