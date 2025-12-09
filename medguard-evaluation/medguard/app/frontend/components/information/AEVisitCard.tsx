import { useState } from 'react';
import { Event } from '@/types/api';

interface AEEvent extends Event {
  attendance_date?: string;
  expected_discharge_date?: string;
  discharge_date?: string;
  discharge_method_description?: string;
  discharge_destination_description?: string;
  location_description?: string;
  reason_for_attendance_description?: string;
}

interface AEVisitCardProps {
  event: Event;
  smrDate: string | null;
}

export default function AEVisitCard({ event, smrDate }: AEVisitCardProps) {
  const aeEvent = event as AEEvent;
  const isPreSMR = smrDate ? event.date < smrDate : true;

  return (
    <div className="border rounded-lg p-3 transition-colors hover:shadow-sm bg-white border-gray-200">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-800">
              A&E Visit
            </span>
            {!isPreSMR && smrDate && (
              <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-amber-100 text-amber-800">
                Post-SMR
              </span>
            )}
          </div>
          
          {/* Primary Date */}
          <div className="text-sm text-gray-600 mb-2">
            {aeEvent.attendance_date && (
              <div>
                <span className="font-medium">Attendance:</span> {new Date(aeEvent.attendance_date).toLocaleDateString('en-GB')}
              </div>
            )}
          </div>
          
          {/* Key Info - Always Visible */}
          {aeEvent.reason_for_attendance_description && (
            <div className="text-sm font-medium text-gray-900 mb-1">
              {aeEvent.reason_for_attendance_description}
            </div>
          )}
          
          {aeEvent.location_description && (
            <div className="text-sm text-gray-700">
              <span className="font-medium">Location:</span> {aeEvent.location_description}
            </div>
          )}
        </div>
      </div>
      
      {/* Details */}
      <div className="mt-3 space-y-2">
          {aeEvent.expected_discharge_date && (
            <div className="text-sm">
              <span className="font-medium">Expected Discharge:</span> {new Date(aeEvent.expected_discharge_date).toLocaleDateString('en-GB')}
            </div>
          )}
          
          {aeEvent.discharge_date && (
            <div className="text-sm">
              <span className="font-medium">Discharge Date:</span> {new Date(aeEvent.discharge_date).toLocaleDateString('en-GB')}
            </div>
          )}
          
          {aeEvent.discharge_method_description && (
            <div className="text-sm">
              <span className="font-medium">Discharge Method:</span> {aeEvent.discharge_method_description}
            </div>
          )}
          
          {aeEvent.discharge_destination_description && (
            <div className="text-sm">
              <span className="font-medium">Discharge Destination:</span> {aeEvent.discharge_destination_description}
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