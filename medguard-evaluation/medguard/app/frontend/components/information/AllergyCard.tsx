import { useState } from 'react';
import { Event } from '@/types/api';

interface AllergyEvent extends Event {
  allergen_recorded_date?: string;
  allergen_description?: string;
  allergen_type_code?: string;
  allergen_reference?: string;
  allergen_code_system?: string;
  allergen_severity?: string;
  allergen_reaction_code?: string;
}

interface AllergyCardProps {
  event: Event;
  smrDate: string | null;
}

export default function AllergyCard({ event, smrDate }: AllergyCardProps) {
  const allergy = event as AllergyEvent;
  const isPreSMR = smrDate ? event.date < smrDate : true;

  const getSeverityColor = (severity?: string) => {
    if (!severity) return 'bg-gray-100 text-gray-800';
    const lowerSeverity = severity.toLowerCase();
    if (lowerSeverity.includes('severe') || lowerSeverity.includes('high')) {
      return 'bg-red-100 text-red-800';
    }
    if (lowerSeverity.includes('moderate') || lowerSeverity.includes('medium')) {
      return 'bg-yellow-100 text-yellow-800';
    }
    if (lowerSeverity.includes('mild') || lowerSeverity.includes('low')) {
      return 'bg-green-100 text-green-800';
    }
    return 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="border rounded-lg p-3 transition-colors hover:shadow-sm bg-white border-gray-200">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-800">
              Allergy
            </span>
            {allergy.allergen_severity && (
              <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getSeverityColor(allergy.allergen_severity)}`}>
                {allergy.allergen_severity}
              </span>
            )}
            {!isPreSMR && smrDate && (
              <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-amber-100 text-amber-800">
                Post-SMR
              </span>
            )}
          </div>
          
          {/* Allergen Description */}
          <div className="font-medium text-gray-900 mb-1">
            {allergy.allergen_description || 'Allergen recorded'}
          </div>
          
          {/* Date */}
          <div className="text-sm text-gray-600">
            {allergy.allergen_recorded_date && (
              <div>
                <span className="font-medium">Recorded:</span> {new Date(allergy.allergen_recorded_date).toLocaleDateString('en-GB')}
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Details */}
      <div className="mt-3 space-y-2">
          {allergy.allergen_type_code && (
            <div className="text-sm">
              <span className="font-medium">Type Code:</span> {allergy.allergen_type_code}
            </div>
          )}
          
          {allergy.allergen_reference && (
            <div className="text-sm">
              <span className="font-medium">Reference:</span> {allergy.allergen_reference}
            </div>
          )}
          
          {allergy.allergen_code_system && (
            <div className="text-sm">
              <span className="font-medium">Code System:</span> {allergy.allergen_code_system}
            </div>
          )}
          
          {allergy.allergen_reaction_code && (
            <div className="text-sm">
              <span className="font-medium">Reaction Code:</span> {allergy.allergen_reaction_code}
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