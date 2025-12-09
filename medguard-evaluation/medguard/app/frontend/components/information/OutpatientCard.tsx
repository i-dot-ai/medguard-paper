import { Event } from '@/types/api';

// Helper function to check if a date is valid (not null, undefined, or 1900-01-01)
function isValidDate(dateString: string): boolean {
  if (!dateString) return false;
  const date = new Date(dateString);
  return date.getFullYear() > 1900;
}

interface OutpatientEvent extends Event {
  attendance_date?: string;
  referral_date?: string;
  process_date?: string;
  discharge_date?: string;
  clinic_description?: string;
  referral_outcome?: string;
  specialty_description?: string;
  attendance_type_description?: string;
  discharge_method_description?: string;
}

interface OutpatientCardProps {
  event: Event;
  smrDate: string | null;
}

export default function OutpatientCard({ event, smrDate }: OutpatientCardProps) {
  const outpatient = event as OutpatientEvent;
  const isPreSMR = smrDate ? event.date < smrDate : true;

  return (
    <div className="border rounded-lg p-3 transition-colors hover:shadow-sm bg-white border-gray-200">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
              Outpatient Visit
            </span>
            {!isPreSMR && smrDate && (
              <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-amber-100 text-amber-800">
                Post-SMR
              </span>
            )}
          </div>
          
          {/* Key Info */}
          <div className="space-y-1">
            {outpatient.specialty_description && (
              <div className="font-medium text-gray-900">{outpatient.specialty_description}</div>
            )}
            {outpatient.clinic_description && (
              <div className="text-sm text-gray-700">{outpatient.clinic_description}</div>
            )}
            {outpatient.attendance_date && isValidDate(outpatient.attendance_date) && (
              <div className="text-sm text-gray-600">
                <span className="font-medium">Attendance:</span> {new Date(outpatient.attendance_date).toLocaleDateString('en-GB')}
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Details */}
      <div className="mt-3 space-y-2">
          {outpatient.referral_date && isValidDate(outpatient.referral_date) && (
            <div className="text-sm">
              <span className="font-medium">Referral Date:</span> {new Date(outpatient.referral_date).toLocaleDateString('en-GB')}
            </div>
          )}
          
          {outpatient.process_date && isValidDate(outpatient.process_date) && (
            <div className="text-sm">
              <span className="font-medium">Process Date:</span> {new Date(outpatient.process_date).toLocaleDateString('en-GB')}
            </div>
          )}
          
          {outpatient.discharge_date && isValidDate(outpatient.discharge_date) && (
            <div className="text-sm">
              <span className="font-medium">Discharge Date:</span> {new Date(outpatient.discharge_date).toLocaleDateString('en-GB')}
            </div>
          )}
          
          {outpatient.referral_outcome && (
            <div className="text-sm">
              <span className="font-medium">Referral Outcome:</span> {outpatient.referral_outcome}
            </div>
          )}
          
          {outpatient.attendance_type_description && (
            <div className="text-sm">
              <span className="font-medium">Attendance Type:</span> {outpatient.attendance_type_description}
            </div>
          )}
          
          {outpatient.discharge_method_description && (
            <div className="text-sm">
              <span className="font-medium">Discharge Method:</span> {outpatient.discharge_method_description}
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