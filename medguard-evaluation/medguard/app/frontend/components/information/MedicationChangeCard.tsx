import { useState } from 'react';
import { Event } from '@/types/api';

interface MedicationChangeEvent extends Event {
  change_type?: 'started' | 'stopped' | 'changed';
}

interface MedicationChangeCardProps {
  event: Event;
  smrDate: string | null;
}

export default function MedicationChangeCard({ event, smrDate }: MedicationChangeCardProps) {
  const medicationChange = event as MedicationChangeEvent;
  const isPreSMR = smrDate ? event.date < smrDate : true;

  const getChangeTypeColor = (changeType?: string) => {
    switch (changeType) {
      case 'started':
        return 'bg-green-100 text-green-800';
      case 'stopped':
        return 'bg-red-100 text-red-800';
      case 'changed':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatChangeType = (changeType?: string) => {
    if (!changeType) return 'Changed';
    return changeType.charAt(0).toUpperCase() + changeType.slice(1);
  };

  return (
    <div className="border rounded-lg p-3 transition-colors hover:shadow-sm bg-white border-gray-200">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-orange-100 text-orange-800">
              Medication Change
            </span>
            {medicationChange.change_type && (
              <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getChangeTypeColor(medicationChange.change_type)}`}>
                {formatChangeType(medicationChange.change_type)}
              </span>
            )}
            {!isPreSMR && smrDate && (
              <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-amber-100 text-amber-800">
                Post-SMR
              </span>
            )}
          </div>
          
          {/* Medication Description */}
          <div className="font-medium text-gray-900 mb-1">
            {event.description || 'Medication change'}
          </div>
          
          {/* Date */}
          <div className="text-sm text-gray-600">
            {new Date(event.date).toLocaleDateString('en-GB', {
              day: 'numeric',
              month: 'short',
              year: 'numeric'
            })}
          </div>
        </div>
      </div>
      
      {/* Details */}
      {event.details && Object.keys(event.details).length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-100">
        <div className="text-xs font-medium text-gray-700 mb-1">Additional Details:</div>
        <div className="bg-gray-50 rounded p-2 text-xs font-mono">
          <pre className="whitespace-pre-wrap text-gray-700">
            {JSON.stringify(event.details, null, 2)}
          </pre>
        </div>
      </div>
      )}
    </div>
  );
}