import { useState, useMemo } from 'react';
import { PatientProfile, Event, EventFilters, EventType } from '@/types/api';
import EventFiltersComponent from './EventFilters';
import EventCard from './EventCard';
import GPEventCard from './GPEventCard';
import PrescriptionCard from './PrescriptionCard';
import InpatientCard from './InpatientCard';
import AEVisitCard from './AEVisitCard';
import MedicationChangeCard from './MedicationChangeCard';
import OutpatientCard from './OutpatientCard';
import AllergyCard from './AllergyCard';

interface PatientHistoryTabProps {
  patient: PatientProfile;
  events: Event[];
  smrDate: string | null;
  currentStage: number;
}

// Helper functions matching backend model
const calculateAge = (dateOfBirth: string, referenceDate: string): string => {
  const birthDate = new Date(dateOfBirth);
  const refDate = new Date(referenceDate);
  
  const age = refDate.getFullYear() - birthDate.getFullYear() - 
    ((refDate.getMonth(), refDate.getDate()) < (birthDate.getMonth(), birthDate.getDate()) ? 1 : 0);
  
  return age.toString();
};

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  if (date.getFullYear() === 1900) return 'Unknown date';
  
  return date.toLocaleDateString('en-GB', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  });
};

// Lookup tables matching backend mappings
const qofRegisterLookup: Record<string, string> = {
  "AST_REG_V48": "Asthma Register: Patients aged at least 6 years old with an unresolved asthma diagnosis and have received asthma-related drug treatment in the preceding 12 months",
  "AFIB_REG_V48": "Atrial fibrillation register: Patients with an unresolved diagnosis of atrial fibrillation",
  "CAN_REG_V48": "Cancer register: patients diagnosed with cancer since 1st April 2003",
  "CS_REG_V48": "Cervical screening register: Females aged 25 to 64 years",
  "CHD_REG_V48": "CHD register: Register of patients with a coronary heart disease (CHD) diagnosis.",
  "CKD_REG_V45": "CKD register: Register of patients aged 18 years or over with CKD with classification of categories G3a to G5",
  "CKD_REG_V48": "CKD register: Register of patients aged 18 years or over with CKD with classification of categories G3a to G5",
  "COPD_REG_V48": "COPD register: Register of patients with a clinical diagnosis of COPD",
  "DEM_REG_V48": "Dementia register: Patients with a dementia diagnosis",
  "DEP1_REG_V48": "Depression register: Patients aged at least 18 years old whose latest unresolved episode of depression is since 1st April 2006",
  "DM_REG_V48": "Diabetes register: Patients aged at least 17 years old with an unresolved diabetes diagnosis",
  "EPIL_REG_V48": "Epilepsy register: Patients aged at least 18 years old with an unresolved diagnosis of epilepsy who have a record of being on drug treatment for epilepsy in the last 6 months",
  "HF1_REG_V48": "Heart failure register 1: Patients with an unresolved diagnosis of heart failure",
  "HF2_REG_V48": "Heart failure register 2: Patients with an unresolved diagnosis of heart failure due to left ventricular systolic dysfunction (LVSD) or reduced ejection fraction",
  "HTN_REG_V45": "Hypertension register: Patients with an unresolved diagnosis of hypertension",
  "HYP_REG_V48": "Hypertension register: Patients with an unresolved diagnosis of hypertension",
  "LD_REG_V48": "Learning disability register: Patients with a learning disability",
  "MH1_REG_V48": "Mental health register 1: Patients with a diagnosis of psychosis, schizophrenia or bipolar affective disease",
  "MH2_REG_V48": "Mental health register 2: Patients with a lithium prescription in the last 6 months whose lithium treatment has not been subsequently stopped",
  "OBES_30_REG_V48": "Obesity register: Patients aged 18 years or over with a body mass index (BMI) greater than or equal to 30 in the preceding 12 months",
  "OBES_27_BAME_REG_V48": "Obesity BAME register: Patients aged 18 years or over whose most recent ethnicity status was South Asian, Chinese, other Asian, Middle Eastern, Black African or African-Caribbean family background and have a BMI of 27.5 or over in the preceding 12 months",
  "OBES_REG_V48": "Obesity register: Patients aged 18 years or over with a body mass index (BMI) greater than or equal to 30 kg/m2 in the preceding 12 months or a BMI greater than or equal to 27.5 kg/m2 recorded in the preceding 12 months for patients with a South Asian, Chinese, other Asian, Middle Eastern, Black African or African-Caribbean family background.",
  "OSTEO1_REG_V48": "Osteoporosis register 1: Patients aged 50 or over who have not attained the age of 75 with a record of a fragility fracture on or after 1 April 2012 and a diagnosis of osteoporosis confirmed on a DXA scan",
  "OSTEO2_REG_V48": "Osteoporosis register 2: Patients aged 75 and over with a record of fragility fracture on or after 1 April 2014 and an osteoporosis diagnosis",
  "PAD_REG_V48": "PAD register: Register of patients with peripheral arterial disease",
  "PALCARE_REG_V48": "Palliative Care register: Patients who have been identified as requiring palliative care",
  "RA_REG_V45": "Rheumatoid arthritis register: Patients aged 16 years or over with a diagnosis of rheumatoid arthritis",
  "RA_REG_V48": "Rheumatoid arthritis register: Patients aged 16 years or over with a diagnosis of rheumatoid arthritis",
  "SMOK1_REG_V48": "Register of patients with a co-morbidity of CHD, PAD, stroke or TIA, hypertension, diabetes, COPD, asthma, CKD, schizophrenia, bipolar affective disorder or other psychoses",
  "SMOK2_REG_V48": "Register of patients who are aged 15 years and over",
  "STIA_REG_V48": "Stroke/TIA register: Register of patients with a Stroke or TIA diagnosis",
  "NDH_REG_V48": "Non-diabetic hyperglycaemia register: Patients aged 18 years or over with a diagnosis of non-diabetic hyperglycaemia"
};

const frailtyDeficitLookup: Record<string, string> = {
  "ACTLIM": "Activity limitation",
  "ANHAEM": "Anaemia & haematinic deficiency",
  "ARTH": "Arthritis",
  "ATFIB": "Atrial fibrillation",
  "CVBD": "Cerebrovascular disease",
  "CKD": "Chronic kidney disease",
  "DIAB": "Diabetes",
  "DIZ": "Dizziness",
  "DYSP": "Dyspnoea",
  "FALL": "Falls",
  "FOOT": "Foot problems",
  "FRAC": "Fragility fracture",
  "HIMP": "Hearing impairment",
  "HFAIL": "Heart failure",
  "HVD": "Heart valve disease",
  "HOUSEB": "Housebound",
  "HYPT": "Hypertension",
  "HYPOT": "Hypotension / syncope",
  "IHD": "Ischaemic heart disease",
  "MEMCOG": "Memory & cognitive problems",
  "MOB": "Mobility and transfer problems",
  "OSTEO": "Osteoporosis",
  "PARKS": "Parkinsonism & tremor",
  "PEPULC": "Peptic ulcer",
  "PVD": "Peripheral vascular disease",
  "POLYPH": "Polypharmacy",
  "REQCARE": "Requirement for care",
  "RESPD": "Respiratory disease",
  "SKULC": "Skin ulcer",
  "SLPDIS": "Sleep disturbance",
  "SOCVUL": "Social vulnerability",
  "THYDIS": "Thyroid disease",
  "URIINC": "Urinary incontinence",
  "IURID": "Urinary system disease",
  "VISIMP": "Visual impairment",
  "WLANX": "Weight loss & anorexia"
};

export default function PatientHistoryTab({
  patient,
  events,
  smrDate,
  currentStage
}: PatientHistoryTabProps) {
  const [filters, setFilters] = useState<EventFilters>({
    searchTerm: '',
    eventTypes: []
  });
  const [patientInfoExpanded, setPatientInfoExpanded] = useState(true);

  // Create comprehensive search text for each event type
  const getSearchableText = (event: Event): string => {
    const searchTexts: string[] = [
      event.description || '',
      event.event_type || '',
      JSON.stringify(event.details || {})
    ];

    // Add event-type specific searchable content
    switch (event.event_type) {
      case EventType.GP_EVENT:
        const gpEvent = event as any;
        if (gpEvent.observations) {
          gpEvent.observations.forEach((obs: any) => {
            searchTexts.push(obs.description || '');
            searchTexts.push(obs.value || '');
            searchTexts.push(obs.units || '');
            searchTexts.push(obs.episodity || '');
          });
        }
        break;
        
      case EventType.PRESCRIPTION:
        const prescription = event as any;
        searchTexts.push(prescription.dosage || '');
        searchTexts.push(prescription.units || '');
        searchTexts.push(prescription.snomed_code || '');
        searchTexts.push(prescription.is_repeat_medication ? 'repeat' : '');
        break;
        
      case EventType.INPATIENT_EPISODE:
        const inpatient = event as any;
        searchTexts.push(inpatient.admission_type_description || '');
        searchTexts.push(inpatient.admission_source_description || '');
        searchTexts.push(inpatient.specialty_description || '');
        searchTexts.push(inpatient.ward_description || '');
        searchTexts.push(inpatient.discharge_method_description || '');
        searchTexts.push(inpatient.discharge_destination_description || '');
        break;
        
      case EventType.AE_VISIT:
        const aeEvent = event as any;
        searchTexts.push(aeEvent.reason_for_attendance_description || '');
        searchTexts.push(aeEvent.location_description || '');
        searchTexts.push(aeEvent.discharge_method_description || '');
        searchTexts.push(aeEvent.discharge_destination_description || '');
        break;
        
      case EventType.OUTPATIENT_VISIT:
        const outpatient = event as any;
        searchTexts.push(outpatient.specialty_description || '');
        searchTexts.push(outpatient.clinic_description || '');
        searchTexts.push(outpatient.referral_outcome || '');
        searchTexts.push(outpatient.attendance_type_description || '');
        break;
        
      case EventType.ALLERGY:
        const allergy = event as any;
        searchTexts.push(allergy.allergen_description || '');
        searchTexts.push(allergy.allergen_severity || '');
        searchTexts.push(allergy.allergen_type_code || '');
        searchTexts.push(allergy.allergen_reaction_code || '');
        break;
        
      case EventType.MEDICATION_CHANGE:
        const medChange = event as any;
        searchTexts.push(medChange.change_type || '');
        break;
    }

    return searchTexts.join(' ').toLowerCase();
  };

  // Filter events based on search, date range, and event types
  const filteredEvents = useMemo(() => {
    return events.filter(event => {
      // Search filter
      if (filters.searchTerm) {
        const searchLower = filters.searchTerm.toLowerCase();
        const searchableText = getSearchableText(event);
        
        if (!searchableText.includes(searchLower)) return false;
      }

      // Date range filter
      if (filters.dateFrom) {
        if (event.date < filters.dateFrom) return false;
      }
      if (filters.dateTo) {
        if (event.date > filters.dateTo) return false;
      }

      // Event type filter
      if (filters.eventTypes.length > 0) {
        if (!filters.eventTypes.includes(event.event_type)) return false;
      }

      return true;
    });
  }, [events, filters]);

  // Sort events by date (most recent first)
  const sortedEvents = useMemo(() => {
    return [...filteredEvents].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  }, [filteredEvents]);

  return (
    <div className="space-y-4">
      {/* SMR Date Display */}
      {smrDate && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <span className="font-semibold text-blue-900">SMR Date: </span>
          <span className="text-blue-700">
            {new Date(smrDate).toLocaleDateString('en-GB', {
              day: 'numeric',
              month: 'long',
              year: 'numeric'
            })}
          </span>
          <div className="text-sm text-blue-600 mt-1">
            {currentStage <= 2 
              ? 'Showing events before SMR only' 
              : 'Showing all events (pre and post SMR)'}
          </div>
        </div>
      )}

      {/* Patient Information */}
      <div className="bg-white border border-gray-200 rounded-xl shadow-sm">
        <button
          onClick={() => setPatientInfoExpanded(!patientInfoExpanded)}
          className="w-full p-5 flex items-center justify-between hover:bg-gray-50 transition-colors rounded-xl"
        >
          <h3 className="text-lg font-bold text-gray-900 flex items-center">
            <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
            Patient Information
          </h3>
          <div className={`transform transition-transform duration-200 ${patientInfoExpanded ? 'rotate-90' : ''}`}>
            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </button>
        
        {patientInfoExpanded && (
          <div className="px-5 pb-5">
            {/* Demographics Section */}
            <div className="mb-5">
              <h4 className="text-sm font-semibold text-gray-700 mb-2 uppercase tracking-wide">Demographics</h4>
              <div className="bg-blue-50 rounded-lg p-3 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Patient ID:</span> 
                  <span className="font-medium text-gray-900">{patient.patient_link_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Sex:</span> 
                  <span className="font-medium text-gray-900">{patient.sex || 'Unknown'}</span>
                </div>
                {patient.date_of_birth && smrDate && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Age:</span> 
                    <span className="font-medium text-gray-900">{calculateAge(patient.date_of_birth, smrDate)} years</span>
                  </div>
                )}
                {patient.date_of_birth && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Date of birth:</span> 
                    <span className="font-medium text-gray-900">{formatDate(patient.date_of_birth)}</span>
                  </div>
                )}
                {patient.ethnic_origin && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Ethnicity:</span> 
                    <span className="font-medium text-gray-900">{patient.ethnic_origin}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Clinical Status */}
            {(patient.deceased || patient.imd_score !== undefined || patient.frailty_score !== undefined || 
              patient.mortality_risk_score !== undefined || patient.social_care_flag !== undefined) && (
              <div className="mb-5">
                <h4 className="text-sm font-semibold text-gray-700 mb-2 uppercase tracking-wide">Clinical Status</h4>
                <div className="bg-gray-50 rounded-lg p-3 space-y-2 text-sm">
                  {patient.deceased && (
                    <div className="flex justify-between bg-red-50 px-2 py-1 rounded border border-red-200">
                      <span className="text-red-700 font-medium">Deceased:</span> 
                      <span className="text-red-800 font-medium">
                        {patient.death_date ? formatDate(patient.death_date) : 'Unknown date'}
                      </span>
                    </div>
                  )}
                  
                  {patient.imd_score !== undefined && patient.imd_score !== null && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">IMD Deprivation:</span> 
                      <span className="font-medium text-gray-900">
                        {((patient.imd_score / 32844) * 100).toFixed(1)}%
                        <span className="text-xs text-gray-500 ml-1">(higher = less deprived)</span>
                      </span>
                    </div>
                  )}
                  
                  {patient.frailty_score !== undefined && patient.frailty_score !== null && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Frailty Score:</span> 
                      <span className="font-medium text-gray-900">
                        {patient.frailty_score.toFixed(2)}
                        <span className="text-xs text-gray-500 ml-1">(0.0-1.0 scale)</span>
                      </span>
                    </div>
                  )}
                  
                  {patient.mortality_risk_score !== undefined && patient.mortality_risk_score !== null && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Mortality Risk:</span> 
                      <span className="font-medium text-gray-900">{patient.mortality_risk_score}</span>
                    </div>
                  )}

                  {patient.social_care_flag !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Social Care:</span> 
                      <span className={`font-medium ${patient.social_care_flag ? 'text-amber-700' : 'text-gray-900'}`}>
                        {patient.social_care_flag ? 'Yes' : 'No'}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* QOF Registers */}
            {patient.qof_registers && (
              <div className="mb-5">
                <h4 className="text-sm font-semibold text-gray-700 mb-2 uppercase tracking-wide">QOF Registers</h4>
                <div className="bg-green-50 rounded-lg p-3">
                  <div className="space-y-1 text-xs">
                    {patient.qof_registers.split('|').map((register, idx) => (
                      <div key={idx} className="text-green-800 leading-relaxed">
                        <span className="font-medium">{register}:</span> {qofRegisterLookup[register] || register}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Frailty Deficits */}
            {patient.frailty_deficit_list && (
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-2 uppercase tracking-wide">Frailty Deficits</h4>
                <div className="bg-orange-50 rounded-lg p-3">
                  <div className="grid grid-cols-1 gap-1 text-xs">
                    {patient.frailty_deficit_list.split('|').map((deficit, idx) => (
                      <div key={idx} className="text-orange-800 flex items-start">
                        <span className="inline-block w-2 h-2 bg-orange-400 rounded-full mt-1.5 mr-2 flex-shrink-0"></span>
                        <span className="font-medium mr-1">{deficit}:</span>
                        <span>{frailtyDeficitLookup[deficit] || deficit}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Event Filters */}
      <EventFiltersComponent 
        filters={filters} 
        onFiltersChange={setFilters}
        smrDate={smrDate}
      />

      {/* Events List */}
      <div>
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-lg font-semibold">Clinical Events</h3>
          <div className="text-sm text-gray-500">
            {sortedEvents.length} of {events.length} events
          </div>
        </div>
        
        {sortedEvents.length === 0 ? (
          <div className="text-gray-500 text-center py-8">
            {events.length === 0 ? 'No events found' : 'No events match current filters'}
          </div>
        ) : (
          <div className="space-y-3">
            {sortedEvents.map((event, index) => {
              const key = `${event.date}-${index}`;
              const commonProps = { event, smrDate };
              
              switch (event.event_type) {
                case EventType.GP_EVENT:
                  return <GPEventCard key={key} {...commonProps} />;
                
                case EventType.PRESCRIPTION:
                  return <PrescriptionCard key={key} {...commonProps} currentStage={currentStage} />;
                
                case EventType.INPATIENT_EPISODE:
                  return <InpatientCard key={key} {...commonProps} />;
                
                case EventType.AE_VISIT:
                  return <AEVisitCard key={key} {...commonProps} />;
                
                case EventType.OUTPATIENT_VISIT:
                  return <OutpatientCard key={key} {...commonProps} />;
                
                case EventType.ALLERGY:
                  return <AllergyCard key={key} {...commonProps} />;
                
                case EventType.MEDICATION_CHANGE:
                  return <MedicationChangeCard key={key} {...commonProps} />;
                
                default:
                  return <EventCard key={key} {...commonProps} />;
              }
            })}
          </div>
        )}
      </div>
    </div>
  );
}