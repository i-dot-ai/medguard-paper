import { useState } from 'react';
import { Event, GPEvent, isGPEvent, Observation } from '@/types/api';

interface GPEventCardProps {
  event: Event;
  smrDate: string | null;
}

export default function GPEventCard({ event, smrDate }: GPEventCardProps) {
  const [expanded, setExpanded] = useState(false);
  
  // Type guard to ensure this is a GP event
  if (!isGPEvent(event)) {
    return null;
  }
  
  const gpEvent = event as GPEvent;
  
  // Determine if this event is before or after SMR
  const isPreSMR = smrDate ? event.date < smrDate : true;

  return (
    <div className="border rounded-lg p-3 transition-colors hover:shadow-sm bg-white border-gray-200">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
              gpEvent.was_smr 
                ? 'bg-purple-100 text-purple-800' 
                : 'bg-green-100 text-green-800'
            }`}>
              {gpEvent.was_smr ? 'SMR Event' : 'GP Event'}
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
      
      {/* Observations (always visible for GP events as they're critical) */}
      {gpEvent.observations && gpEvent.observations.length > 0 && (
        <div className="mt-3">
          <div className="bg-yellow-50 border border-yellow-200 rounded p-2">
            <div className="text-sm space-y-2">
              {gpEvent.observations.map((obs, index) => (
                <div key={index} className="text-gray-700">
                  <div className="font-medium">{obs.description}</div>
                  {(obs.value || obs.units || obs.episodity) && (
                    <div className="text-xs text-gray-600 mt-1">
                      {obs.value && <span>Value: {obs.value}</span>}
                      {obs.units && <span className="ml-2">Units: {obs.units}</span>}
                      {obs.episodity && <span className="ml-2">Episodicity: {obs.episodity}</span>}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      
      {/* Additional Details */}
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