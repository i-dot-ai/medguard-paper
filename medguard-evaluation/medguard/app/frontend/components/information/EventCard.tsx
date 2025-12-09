import { useState } from 'react';
import { Event } from '@/types/api';

interface EventCardProps {
  event: Event;
  smrDate: string | null;
}

export default function EventCard({ event, smrDate }: EventCardProps) {
  // Determine if this event is before or after SMR
  const isPreSMR = smrDate ? event.date < smrDate : true;
  
  // Format the event type for display
  const formatEventType = (type: string) => {
    return type.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase());
  };

  return (
    <div className="border rounded-lg p-3 transition-colors hover:shadow-sm bg-white border-gray-200">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
              {formatEventType(event.event_type)}
            </span>
            {!isPreSMR && smrDate && (
              <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-amber-100 text-amber-800">
                Post-SMR
              </span>
            )}
          </div>
          
          <div className="mt-1 text-sm text-gray-600">
            {new Date(event.date).toLocaleDateString('en-GB', {
              day: 'numeric',
              month: 'short',
              year: 'numeric'
            })}
          </div>
        </div>
      </div>
      
      {/* Description */}
      {event.description && (
        <div className="mt-2 text-sm text-gray-700">
          {event.description}
        </div>
      )}
      
      {/* Details */}
      {event.details && Object.keys(event.details).length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-100">
        <div className="text-xs text-gray-500 mb-2">Additional Details:</div>
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