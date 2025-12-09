from datetime import date, datetime, timedelta
from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, Field, computed_field, field_validator

frailty_deficit_lookup = {
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
    "WLANX": "Weight loss & anorexia",
}

qof_register_lookup = {
    "AST_REG_V48": "Asthma Register: Patients aged at least 6 years old with an unresolved asthma diagnosis and have received asthma-related drug treatment in the preceding 12 months",
    "AFIB_REG_V48": "Atrial fibrillation register: Patients with an unresolved diagnosis of atrial fibrillation",
    "CAN_REG_V48": "Cancer register: patients diagnosed with cancer since 1st April 2003",
    "CS_REG_V48": "Cervical screening register: Females aged 25 to 64 years",
    "CHD_REG_V48": "CHD register: Register of patients with a coronary heart disease (CHD) diagnosis.",
    "CKD_REG_V48": "CKD register: Register of patients aged 18 years or over with CKD with classification of categories G3a to G5",
    "COPD_REG_V48": "COPD register:  Register of patients with a clinical diagnosis of COPD before 1 April 2020; and Patients with a clinical diagnosis of COPD on or after 1 April 2020 whose diagnosis has been confirmed by a quality assured post-bronchodilator spirometry FEV1/FVC ratio below 0.7 between 3 months before or 6 months after diagnosis and Patients with a clinical diagnosis of COPD on or after 1 April 2020 who are unable to undertake spirometry.",
    "DEM_REG_V48": "Dementia register:  Patients with a dementia diagnosis",
    "DEP1_REG_V48": "Depression register:  Patients aged at least 18 years old whose latest unresolved episode of depression is since 1st April 2006",
    "DM_REG_V48": "Diabetes register:  Patients aged at least 17 years old with an unresolved diabetes diagnosis",
    "EPIL_REG_V48": "Epilepsy register:  Patients aged at least 18 years old with an unresolved diagnosis of epilepsy who have a record of being on drug treatment for epilepsy in the last 6 months",
    "HF1_REG_V48": "Heart failure register 1:  Patients with an unresolved diagnosis of heart failure",
    "HF2_REG_V48": "Heart failure register 2:  Patients with an unresolved diagnosis of heart failure due to left ventricular systolic dysfunction (LVSD) or reduced ejection fraction",
    "HYP_REG_V48": "Hypertension register:  Patients with an unresolved diagnosis of hypertension",
    "LD_REG_V48": "Learning disability register:  Patients with a learning disability",
    "MH1_REG_V48": "Mental health register 1:  Patients with a diagnosis of psychosis, schizophrenia or bipolar affective disease",
    "MH2_REG_V48": "Mental health register 2:  Patients with a lithium prescription in the last 6 months whose lithium treatment has not been subsequently stopped",
    "OBES_30_REG_V48": "Obesity register:  Patients aged 18 years or over with a body mass index (BMI) greater than or equal to 30 in the preceding 12 months",
    "OBES_27_BAME_REG_V48": "Obesity BAME register: Patients aged 18 years or over whose most recent ethnicity status was South Asian, Chinese, other Asian, Middle Eastern, Black African or African-Caribbean family background and have a BMI of 27.5 or over in the preceding 12 months",
    "OBES_REG_V48": "Obesity register: Patients aged 18 years or over with a body mass index (BMI) greater than or equal to 30 kg/m2 in the preceding 12 months or a BMI greater than or equal to 27.5 kg/m2 recorded in the preceding 12 months for patients with a South Asian, Chinese, other Asian, Middle Eastern, Black African or African-Caribbean family background.",
    "OSTEO1_REG_V48": "Osteoporosis register 1:  Patients aged 50 or over who have not attained the age of 75 with a record of a fragility fracture on or after 1 April 2012 and a diagnosis of osteoporosis confirmed on a DXA scan",
    "OSTEO2_REG_V48": "Osteoporosis register 2:  Patients aged 75 and over with a record of fragility fracture on or after 1 April 2014 and an osteoporosis diagnosis",
    "PAD_REG_V48": "PAD register:  Register of patients with peripheral arterial disease",
    "PALCARE_REG_V48": "Palliative Care register:  Patients who have been identified as requiring palliative care",
    "RA_REG_V48": "Rheumatoid arthritis register:  Patients aged 16 years or over with a diagnosis of rheumatoid arthritis",
    "SMOK1_REG_V48": "Register of patients with a co-morbidity of CHD, PAD, stroke or TIA, hypertension, diabetes, COPD, asthma, CKD, schizophrenia, bipolar affective disorder or other psychoses",
    "SMOK2_REG_V48": "Register of patients who are aged 15 years and over",
    "STIA_REG_V48": "Stroke/TIA register:  Register of patients with a Stroke or TIA diagnosis",
    "NDH_REG_V48": "Non-diabetic hyperglycaemia register:  Patients aged 18 years or over with a diagnosis of non-diabetic hyperglycaemia",
}


def get_first_non_null(*attributes):
    """Helper function to get the first non-null attribute from an object"""

    def getter(self):
        for attr in attributes:
            value = getattr(self, attr, None)
            if value is not None:
                return value
        return None

    return getter


def format_datetime(dt: datetime, include_time: bool = False) -> str:
    if include_time:
        return dt.strftime("%A %d %B %Y %H.%M%p")
    else:
        return dt.strftime("%A %d %B %Y")


def format_date(d: date | None) -> str:
    """Format a date as a human-friendly string; returns "Unknown date" if None."""
    if not d:
        return "Unknown date"
    return d.strftime("%A %d %B %Y")


class EventType(str, Enum):
    MEDICATION = "medication"
    GP_EVENT = "gp_event"
    GP_ENCOUNTER = "gp_encounter"
    INPATIENT_EPISODE = "inpatient_episode"
    AE_VISIT = "ae_visit"
    OUTPATIENT_VISIT = "outpatient_visit"
    ALLERGY = "allergy"
    SOCIAL_CARE_EVENT = "social_care_event"
    MEDICATION_CHANGE = "medication_change"
    PRESCRIPTION = "prescription"


class FilterType(int, Enum):
    """Filter types for identifying patients with specific clinical scenarios"""

    NO_MATCH = 0
    DILTIAZEM_VERAPAMIL_HEART_FAILURE = 5
    ASTHMA_BETA_BLOCKER_NO_CARDIAC = 6
    ANTIPSYCHOTIC_ELDERLY_DEMENTIA_NOT_PSYCHOSIS = 10
    METFORMIN_RENAL_IMPAIRMENT_EGFR_30 = 16
    CHC_BMI_40_OR_GREATER = 23
    METHOTREXATE_NO_FOLIC_ACID = 26
    NSAID_PEPTIC_ULCER_NO_GASTROPROTECTION = 28
    WARFARIN_ANTIBIOTIC_NO_INR = 33
    ELDERLY_LOOP_DIURETIC_NO_RENAL_CHECK = 43
    METHOTREXATE_NO_LFT_MONITORING = 55


filter_descriptions = {
    FilterType.DILTIAZEM_VERAPAMIL_HEART_FAILURE: "Prescription of diltiazem or verapamil in a patient with heart failure",
    FilterType.ASTHMA_BETA_BLOCKER_NO_CARDIAC: "Prescription of a beta-blocker to a patient with asthma (excluding patients who also have a cardiac condition, where the benefits of beta-blockers may outweigh the risks)",
    FilterType.ANTIPSYCHOTIC_ELDERLY_DEMENTIA_NOT_PSYCHOSIS: "Prescription of an antipsychotic drug to a patient aged >65 years with dementia, who does not have a diagnosis of psychosis",
    FilterType.METFORMIN_RENAL_IMPAIRMENT_EGFR_30: "Metformin prescribed to a patient with renal impairment where the eGFR is ≤30 ml/min",
    FilterType.CHC_BMI_40_OR_GREATER: "Combined hormonal contraceptive prescribed to woman with body mass index of ≥40",
    FilterType.METHOTREXATE_NO_FOLIC_ACID: "Methotrexate prescribed without folic acid",
    FilterType.NSAID_PEPTIC_ULCER_NO_GASTROPROTECTION: "Prescription of an NSAID, without co-prescription of an ulcer-healing drug, to a patient with a history of peptic ulceration",
    FilterType.WARFARIN_ANTIBIOTIC_NO_INR: "Concurrent use of warfarin and any antibiotic without monitoring the INR within 5 days",
    FilterType.ELDERLY_LOOP_DIURETIC_NO_RENAL_CHECK: "Patients aged >75 years on loop diuretics who have not had a U+E in the previous 15 months",
    FilterType.METHOTREXATE_NO_LFT_MONITORING: "Prescription of methotrexate without a record of liver function having been measured within the previous 3 months",
}


filter_factors = {
    FilterType.DILTIAZEM_VERAPAMIL_HEART_FAILURE: [
        "Have a recorded diagnosis of heart failure (any type)",
        "Have been prescribed diltiazem or verapamil (non-dihydropyridine calcium channel blockers)",
    ],
    FilterType.ASTHMA_BETA_BLOCKER_NO_CARDIAC: [
        "Have a recorded diagnosis of asthma (any type)",
        "Do NOT have any recorded cardiac condition (heart failure, CHD, arrhythmia, etc.)",
        "Have been prescribed a beta blocker after their asthma diagnosis",
    ],
    FilterType.ANTIPSYCHOTIC_ELDERLY_DEMENTIA_NOT_PSYCHOSIS: [
        "Are aged >65 years at time of prescription",
        "Have a recorded diagnosis of dementia (any type)",
        "Have been prescribed an antipsychotic for >6 weeks (>42 days)",
        "Do NOT have a diagnosis of psychosis (exclusion criterion)",
        "Prescription must occur AFTER dementia diagnosis",
    ],
    FilterType.METFORMIN_RENAL_IMPAIRMENT_EGFR_30: [
        "Have a recorded eGFR measurement ≤30 ml/min OR a diagnosis of severe renal impairment (CKD stage 4-5)",
        "Have been prescribed metformin after renal impairment was documented",
        "Renal impairment must be documented within 12 months before prescription",
    ],
    FilterType.CHC_BMI_40_OR_GREATER: [
        "Are female",
        "Have documented BMI ≥40 within 12 months before prescription",
        "Are prescribed combined hormonal contraceptives (oral, patch, or ring)",
    ],
    FilterType.METHOTREXATE_NO_FOLIC_ACID: [
        "Have been prescribed oral methotrexate",
        "Do NOT have a co-prescribed folic acid supplement during the methotrexate treatment period",
    ],
    FilterType.NSAID_PEPTIC_ULCER_NO_GASTROPROTECTION: [
        "Have a recorded diagnosis of peptic ulcer (including gastric ulcer, duodenal ulcer, etc.)",
        "Have been prescribed an NSAID after their peptic ulcer diagnosis",
        "Do NOT have a co-prescribed ulcer-healing drug during the NSAID prescription period",
    ],
    FilterType.WARFARIN_ANTIBIOTIC_NO_INR: [
        "Have concurrent prescriptions for warfarin and an antibiotic (overlapping prescription periods)",
        "Do NOT have an INR check recorded within 5 days of the antibiotic prescription start date",
    ],
    FilterType.ELDERLY_LOOP_DIURETIC_NO_RENAL_CHECK: [
        "Are aged >75 years (strictly greater than 75)",
        "Have been prescribed a loop diuretic",
        "Have NOT had a computer-recorded check of their renal function and electrolytes in the previous 15 months (450 days)",
    ],
    FilterType.METHOTREXATE_NO_LFT_MONITORING: [
        "Have been prescribed oral methotrexate",
        "Do NOT have a recorded liver function test (LFT) within the previous 3 months (90 days) before prescription start",
    ],
}


class FilterMatch(BaseModel):
    """Represents a period when a patient matched a specific clinical filter"""

    filter_id: int
    start_date: datetime
    end_date: datetime

    @computed_field
    @property
    def description(self) -> str:
        """Automatically populate description from filter_descriptions lookup"""
        return filter_descriptions.get(
            FilterType(self.filter_id), f"Filter {self.filter_id}"
        )

    def prompt(self) -> str:
        """Generate a prompt-friendly description of this filter match"""
        return f"Filter {self.filter_id}: {self.description} (Period: {format_datetime(self.start_date)} to {format_datetime(self.end_date)})"


class Sex(str, Enum):
    MALE = "M"
    FEMALE = "F"
    OTHER = "O"
    UNKNOWN = "U"


class BaseEvent(BaseModel):
    event_type: EventType
    description: Optional[str] = Field(None, alias="description")

    class Config:
        extra = "allow"  # Allow additional fields
        validate_by_name = True  # Allow both field names and aliases


def update_prompt(res: str, field: str | None, descriptor: str = "", newline=True):
    if field:
        newline_token = "\n" if newline else ""
        res += newline_token + descriptor + field
    return res


def update_datetime_prompt(
    res: str,
    dt: datetime | None,
    descriptor: str = "",
    include_time: bool = False,
    newline: bool = True,
) -> str:
    """Append a formatted datetime to the prompt only if non-null.

    - descriptor: prefix to include before the formatted datetime (e.g., "Discharge date: ")
    - include_time: whether to include time in the formatting
    - newline: whether to prepend a newline before appending
    """
    if dt is None:
        return res
    newline_token = "\n" if newline else ""
    return res + newline_token + descriptor + format_datetime(dt, include_time)


class Medication(BaseEvent):
    event_type: EventType = EventType.MEDICATION
    start_date: Optional[datetime] = Field(alias="computed_start_date")
    end_date: Optional[datetime] = Field(None, alias="computed_end_date")
    description: Optional[str] = Field(None, alias="description")
    dosage: Optional[str] = Field(None, alias="Dosage")
    units: Optional[str] = Field(None, alias="Units")
    quantity: Optional[str] = Field(None, alias="Quantity")
    course_length_per_issue: Optional[str] = Field(None, alias="CourseLengthPerIssue")
    repeat_medication_flag: Optional[str] = Field(None, alias="RepeatMedicationFlag")

    @computed_field
    @property
    def date(self) -> Optional[datetime]:
        return get_first_non_null("start_date")(self)

    def prompt(self, at_date: datetime | None = None) -> str:
        res = f"Medication: {self.description}"
        res += f"\nFirst date medication was taken: {format_datetime(self.start_date)}"

        if self.end_date:
            if self.end_date > at_date:
                res += "\nMedication currently in course."
            else:
                res += f"\nFinal date medication was taken: {format_datetime(self.end_date)}"
        else:
            res += "\nMedication end date not provided, a typical course length is around 28 days."

        res = update_prompt(
            res,
            self.dosage,
            "Dosage: ",
        )
        res = update_prompt(res, self.units, "Units: ")
        res = update_prompt(res, self.quantity, "Quantity: ")
        res = update_prompt(res, self.course_length_per_issue, "Course Length: ")
        res = update_prompt(
            res, self.repeat_medication_flag, "Is a repeat medication: "
        )

        return res


class Observation(BaseModel):
    description: Optional[str] = Field(None, alias="description")
    units: Optional[str] = Field(None, alias="Units")
    value: Optional[str] = Field(None, alias="Value")
    episodity: Optional[str] = Field(None, alias="Episodicity")

    def prompt(self) -> str:
        res = f"{self.description}"
        res = update_prompt(res, self.value, descriptor=" | ", newline=False)
        res = update_prompt(res, self.units, descriptor=" ", newline=False)
        res = update_prompt(
            res, self.episodity, descriptor=", Episodity ", newline=False
        )
        return res


class GPEvent(BaseEvent):
    event_type: EventType = EventType.GP_EVENT
    event_date: Optional[datetime] = Field(None, alias="Date")
    was_smr: bool = Field(alias="was_smr")
    flag_smr: Optional[bool] = Field(False, alias="flag_smr")
    observations: list[Observation] = Field(default_factory=list, alias="observations")

    @computed_field
    @property
    def date(self) -> Optional[datetime]:
        return get_first_non_null("event_date")(self)

    def prompt(self, at_date: datetime | None = None) -> str:
        res = "GP Event"
        res = update_datetime_prompt(res, self.event_date, " on ", newline=False)
        res += " with the following observations:"

        for i, observation in enumerate(self.observations):
            res += f"\n{i + 1}. " + observation.prompt()

        return res


class InpatientEpisode(BaseEvent):
    event_type: EventType = EventType.INPATIENT_EPISODE
    admission_date: Optional[datetime] = Field(None, alias="AdmissionDate")
    admission_type_description: Optional[str] = Field(
        None, alias="AdmissionTypeDescription"
    )
    admission_source_description: Optional[str] = Field(
        None, alias="AdmissionSourceDescription"
    )
    admission_category_description: Optional[str] = Field(
        None, alias="AdmissionCategoryDescription"
    )
    expected_discharge_date: Optional[datetime] = Field(
        None, alias="ExpectedDischargeDate"
    )
    transfer_date: Optional[datetime] = Field(None, alias="TransferDate")
    discharge_date: Optional[datetime] = Field(None, alias="DischargeDate")
    discharge_method_description: Optional[str] = Field(
        None, alias="DischargeMethodDescription"
    )
    discharge_destination_description: Optional[str] = Field(
        None, alias="DischargeDestinationDescription"
    )
    ward_description: Optional[str] = Field(None, alias="WardDescription")
    specialty_description: Optional[str] = Field(None, alias="SpecialtyDescription")

    @computed_field
    @property
    def date(self) -> Optional[datetime]:
        return get_first_non_null("admission_date", "transfer_date", "discharge_date")(
            self
        )

    def prompt(self, at_date: datetime | None = None) -> str:
        res = "Inpatient Episode"
        res = update_datetime_prompt(res, self.admission_date, " on ", newline=False)
        res = update_datetime_prompt(
            res, self.expected_discharge_date, "Expected discharge date: "
        )
        res = update_datetime_prompt(res, self.transfer_date, "Transfer date: ")
        res = update_datetime_prompt(res, self.discharge_date, "Discharge date: ")
        return res


class AEVisit(BaseEvent):
    event_type: EventType = EventType.AE_VISIT
    attendance_date: Optional[datetime] = Field(None, alias="AttendanceDate")
    expected_discharge_date: Optional[datetime] = Field(
        None, alias="ExpectedDischargeDate"
    )
    discharge_date: Optional[datetime] = Field(None, alias="DischargeDate")
    discharge_method_description: Optional[str] = Field(
        None, alias="DischargeMethodDescription"
    )
    discharge_destination_description: Optional[str] = Field(
        None, alias="DischargeDestinationDescription"
    )
    location_description: Optional[str] = Field(None, alias="LocationDescription")
    reason_for_attendance_description: Optional[str] = Field(
        None, alias="ReasonForAttendanceDescription"
    )

    @computed_field
    @property
    def date(self) -> Optional[datetime]:
        return get_first_non_null("attendance_date", "discharge_date")(self)

    def prompt(self, at_date: datetime | None = None) -> str:
        res = "A&E Visit"
        res = update_datetime_prompt(res, self.attendance_date, " on ", newline=False)

        res = update_datetime_prompt(
            res, self.expected_discharge_date, "Expected discharge date: "
        )
        res = update_datetime_prompt(res, self.discharge_date, "Discharge date: ")
        res = update_prompt(
            res, self.discharge_method_description, "Discharge Method: "
        )
        res = update_prompt(
            res, self.discharge_destination_description, "Discharge Destination: "
        )
        res = update_prompt(res, self.location_description, "Location: ")
        res = update_prompt(
            res, self.reason_for_attendance_description, "Reason for Attendance: "
        )
        return res


class OutpatientVisit(BaseEvent):
    event_type: EventType = EventType.OUTPATIENT_VISIT
    referral_date: Optional[datetime] = Field(None, alias="ReferralDate")
    attendance_date: Optional[datetime] = Field(None, alias="AttendanceDate")
    process_date: Optional[datetime] = Field(None, alias="ProcessDate")
    discharge_date: Optional[datetime] = Field(None, alias="DischargeDate")
    discharge_method_description: Optional[str] = Field(
        None, alias="DischargeMethodDescription"
    )
    clinic_description: Optional[str] = Field(None, alias="ClinicDescription")
    referral_outcome: Optional[str] = Field(None, alias="ReferralOutcome")
    specialty_description: Optional[str] = Field(None, alias="SpecialtyDescription")
    attendance_type_description: Optional[str] = Field(
        None, alias="AttendanceTypeDescription"
    )

    @computed_field
    @property
    def date(self) -> Optional[datetime]:
        return get_first_non_null(
            "attendance_date", "referral_date", "process_date", "discharge_date"
        )(self)

    def prompt(self, at_date: datetime | None = None) -> str:
        res = "Outpatient Visit"
        res = update_datetime_prompt(res, self.attendance_date, " on ", newline=False)
        res = update_datetime_prompt(res, self.referral_date, "Referral date: ")
        res = update_datetime_prompt(res, self.process_date, "Process date: ")
        res = update_datetime_prompt(res, self.discharge_date, "Discharge date: ")
        res = update_prompt(res, self.clinic_description, "Clinic: ")
        res = update_prompt(res, self.referral_outcome, "Referral Outcome: ")
        res = update_prompt(res, self.specialty_description, "Specialty: ")
        res = update_prompt(res, self.attendance_type_description, "Attendance Type: ")
        res = update_prompt(
            res, self.discharge_method_description, "Discharge Method: "
        )
        return res


class Allergy(BaseEvent):
    event_type: EventType = EventType.ALLERGY
    allergen_type_code: Optional[str] = Field(None, alias="AllergenTypeCode")
    allergen_description: Optional[str] = Field(None, alias="AllergenDescription")
    allergen_reference: Optional[str] = Field(None, alias="AllergenReference")
    allergen_code_system: Optional[str] = Field(None, alias="AllergenCodeSystem")
    allergen_severity: Optional[str] = Field(None, alias="AllergenSeverity")
    allergen_reaction_code: Optional[str] = Field(None, alias="AllergenReactionCode")
    allergen_recorded_date: Optional[datetime] = Field(
        None, alias="AllergenRecordedDate"
    )

    @computed_field
    @property
    def date(self) -> Optional[datetime]:
        return get_first_non_null("allergen_recorded_date")(self)

    def prompt(self, at_date: datetime | None = None) -> str:
        res = "Allergy recorded"
        res = update_datetime_prompt(
            res, self.allergen_recorded_date, " on ", newline=False
        )
        res = update_prompt(res, self.allergen_description, "Allergen: ")
        res = update_prompt(res, self.allergen_type_code, "Type Code: ")
        res = update_prompt(res, self.allergen_reference, "Reference: ")
        res = update_prompt(res, self.allergen_code_system, "Code System: ")
        res = update_prompt(res, self.allergen_severity, "Severity: ")
        res = update_prompt(res, self.allergen_reaction_code, "Reaction Code: ")
        return res


class SocialCareEvent(BaseEvent):
    event_type: EventType = EventType.SOCIAL_CARE_EVENT
    status: Optional[str] = Field(None, alias="Status")
    type_description: Optional[str] = Field(None, alias="TypeDescription")
    start_date: Optional[datetime] = Field(None, alias="StartDate")
    end_date: Optional[datetime] = Field(None, alias="EndDate")

    @computed_field
    @property
    def date(self) -> Optional[datetime]:
        return get_first_non_null("start_date", "end_date")(self)

    def prompt(self, at_date: datetime | None = None) -> str:
        res = "Social Care Event"
        res = update_datetime_prompt(res, self.start_date, "Start date: ")
        res = update_datetime_prompt(res, self.end_date, "End date: ")
        res = update_prompt(res, self.status, "Status: ")
        res = update_prompt(res, self.type_description, "Type: ")
        return res


class ChangeType(Enum):
    STARTED = "started"
    STOPPED = "stopped"


class MedicationChange(BaseEvent):
    event_type: EventType = EventType.MEDICATION_CHANGE
    date: Optional[datetime] = Field(None, alias="smr_date")
    description: Optional[str] = Field(None, alias="medication_name")
    change_type: ChangeType

    def prompt(self, at_date: datetime | None = None) -> str:
        res = f"Medication Change: {self.description} was {self.change_type.value} as a result of the SMR on {self.date}"

        return res


class Prescription(BaseEvent):
    event_type: EventType = EventType.PRESCRIPTION
    start_date: datetime = Field(alias="medication_start_date")
    end_date: datetime = Field(alias="medication_end_date")
    description: Optional[str] = Field(None, alias="medication_name")
    snomed_code: Optional[str] = Field(None, alias="medication_code")
    dosage: Optional[str] = Field(None, alias="dosage")
    units: Optional[str] = Field(None, alias="units")
    duration_days: Optional[int] = Field(alias="total_duration_days")
    prescription_count: Optional[int]
    average_course_length: Optional[int]
    is_repeat_medication: Optional[bool]

    @computed_field
    @property
    def date(self) -> Optional[datetime]:
        return get_first_non_null("start_date", "end_date")(self)

    def prompt(self, at_date: datetime | None = None) -> str:
        res = f"Medication: {self.description}"
        res = update_prompt(
            res,
            self.dosage,
            "Dosage: ",
        )
        res = update_prompt(res, self.units, "Units: ")
        res = update_prompt(
            res, "Yes" if self.is_repeat_medication else "No", "Is Repeat Medication: "
        )
        res += f"\nCourse start date: {format_datetime(self.start_date)}"

        # Determine if the medication is currently being taken
        is_currently_being_taken = self.end_date and self.end_date > at_date

        if is_currently_being_taken:
            res += "\nMedication currently being taken"
        else:
            res += "\nMedication not currently being taken"
            res += f"\nCourse end date: {format_datetime(self.end_date)}"

        if self.end_date and self.end_date < at_date:
            res = update_prompt(
                res, str(self.duration_days), "Total length of prescription (days): "
            )

        res = update_prompt(
            res, str(self.prescription_count), "Total number of prescriptions: "
        )
        res = update_prompt(
            res, str(self.average_course_length), "Average individual course length: "
        )

        return res


# Union type for all events
Event = Union[
    Medication,
    GPEvent,
    InpatientEpisode,
    AEVisit,
    OutpatientVisit,
    Allergy,
    SocialCareEvent,
    MedicationChange,
    Prescription,
]


class PatientProfile(BaseModel):
    # Identifiers
    patient_link_id: int = Field(alias="PK_Patient_Link_ID")
    patient_id: Optional[int] = Field(None, alias="PK_Patient_ID")

    # Demographics
    date_of_birth: Optional[date] = Field(None, alias="Dob")
    sex: Optional[Sex] = Field(None, alias="Sex")
    ethnic_origin: Optional[str] = Field(None, alias="EthnicOrigin")

    # Clinical scores
    imd_score: Optional[float] = Field(None, alias="IMD_Score")
    frailty_score: Optional[float] = Field(None, alias="FrailtyScore")
    mortality_risk_score: Optional[float] = Field(None, alias="MortalityRiskScore")

    # Status flags
    deceased: Optional[bool] = Field(None, alias="Deceased")
    death_date: Optional[date] = Field(None, alias="DeathDate")
    restricted: Optional[bool] = Field(None, alias="Restricted")
    social_care_flag: Optional[bool] = Field(None, alias="SocialCareFlag")

    # Registration
    date_of_registration: Optional[date] = Field(None, alias="DateOfRegistration")
    create_date: Optional[datetime] = Field(None, alias="CreateDate")

    # Clinical registers and lists
    qof_registers: Optional[str] = Field(None, alias="QOFRegisters")
    frailty_deficit_list: Optional[str] = Field(None, alias="FrailtyDeficitList")

    # Filter matches - which clinical filters this patient matched
    matched_filters: List[FilterMatch] = Field(default_factory=list)

    # Sample date - reference date for the patient profile
    sample_date: Optional[date] = Field(None)

    # Events - will be populated from the aggregations
    events: List[Event] = Field(default_factory=list)

    class Config:
        validate_by_name = True

    @field_validator("deceased", "restricted", "social_care_flag", mode="before")
    @classmethod
    def convert_y_n_to_bool(cls, v):
        if v == "Y":
            return True
        elif v == "N":
            return False
        return None

    @field_validator("sex", mode="before")
    @classmethod
    def normalize_sex(cls, v):
        if v:
            v = v.upper()
            if v in Sex._value2member_map_:
                return v
        return Sex.UNKNOWN

    def add_events_from_aggregations(self, aggregations: dict) -> "PatientProfile":
        """Add all events from aggregation data"""

        # Simple mapping of aggregation names to their event classes
        aggregation_handlers = {
            "medications": Medication,
            "gp_events": GPEvent,
            "inpatient_episodes": InpatientEpisode,
            "ae_visits": AEVisit,
            "outpatient_visits": OutpatientVisit,
            "allergies": Allergy,
            "social_care_events": SocialCareEvent,
            "smr_medication_changes": MedicationChange,
            "gp_prescriptions": Prescription,
        }

        # Process each aggregation
        for agg_name, event_class in aggregation_handlers.items():
            if agg_name in aggregations and aggregations[agg_name]:
                for event_data in aggregations[agg_name]:
                    try:
                        # Pydantic will handle the field mapping using aliases
                        event = event_class(**event_data)
                        self.events.append(event)
                    except Exception as e:
                        print(f"Error adding {agg_name} event: {e}")

        return self

    def sort_events_by_date(self) -> "PatientProfile":
        """Sort all events by date (most recent first), with None dates at the end."""
        self.events.sort(key=lambda x: x.date or datetime.min, reverse=True)
        return self

    def filter_events_more_recent_than(self, date: datetime) -> "PatientProfile":
        self.events = [x for x in self.events if x.date is not None and x.date > date]
        return self

    def filter_events_older_than(self, date: datetime) -> "PatientProfile":
        self.events = [x for x in self.events if x.date is not None and x.date < date]
        return self

    def filter_events_not_null_date(self) -> "PatientProfile":
        self.events = [x for x in self.events if x.date is not None]
        return self

    def get_events_by_type(self, event_type: EventType):
        return [x for x in self.events if x.event_type == event_type]

    def prompt(self, at_date: datetime | None = None) -> str:
        """Default patient summary prompt with recent events timeline."""
        return self.build_prompt(at_date=at_date)

    def build_prompt(
        self,
        max_events: int | None = 5,
        events: Optional[List[Event]] = None,
        at_date: datetime | None = None,
    ) -> str:
        """
        Build a patient summary prompt.

        Parameters
        - max_events: number of most recent events to list across all types
        - events: if provided, use this list of events; if None, include all events on the profile
        """

        # Prepare events: choose source (order is preserved as provided)
        source_events: List[Event] = (
            list(events) if events is not None else list(self.events)
        )

        # Determine reference date for age: date of the most recent event if available
        reference_date_for_age: Optional[date] = at_date.date()

        # Header: identity, demographics
        sex_display = (
            self.sex.value
            if isinstance(self.sex, Sex)
            else (self.sex or Sex.UNKNOWN.value)
        )

        # Compute age using reference date if possible
        age_display = None
        if self.date_of_birth and reference_date_for_age:
            try:
                age = (
                    reference_date_for_age.year
                    - self.date_of_birth.year
                    - (
                        (reference_date_for_age.month, reference_date_for_age.day)
                        < (self.date_of_birth.month, self.date_of_birth.day)
                    )
                )
                age_display = str(age)
            except Exception:
                age_display = None

        lines: List[str] = []

        lines.append(
            f"You are conducting a review of the patient on the following date: {format_datetime(at_date)}"
        )
        lines.append(f"Patient ID: {self.patient_link_id}")
        lines.append(f"Sex: {sex_display}")
        if age_display is not None:
            lines.append(f"Age: {age_display}")
        lines.append(f"Date of birth: {format_date(self.date_of_birth)}")

        # Death status
        if self.deceased:
            lines.append(f"Deceased on: {format_date(self.death_date)}")

        # Scores and flags
        if self.imd_score is not None:
            lines.append(
                f"IMD {self.imd_score / 32844 * 100:.1f}% (1% is most deprived, 100% is least deprived)"
            )
        if self.frailty_score is not None:
            lines.append(
                f"Frailty {self.frailty_score:.2f} (0 is the least frail, 1 is the most frail)"
            )
        if self.mortality_risk_score is not None:
            lines.append(f"Mortality Risk {self.mortality_risk_score}")

        if self.social_care_flag:
            lines.append("Patient is in social care")
        if not self.social_care_flag:
            lines.append("Patient is not in social care")

        if self.qof_registers:
            lines.append("QOF registers:")
            lines.append(format_qof_registers(self.qof_registers))
        if self.frailty_deficit_list:
            lines.append("Frailty deficits:")
            lines.append(format_frailty_deficit_list(self.frailty_deficit_list))

        # Most recent events section

        if max_events is None:
            max_events = len(source_events)

        if max_events > 0 and source_events:
            lines.append(
                f"\nMost recent events ({min(max_events, len(source_events))}):"
            )
            for idx, e in enumerate(source_events[:max_events], start=1):
                lines.append(f"Event {idx} - {e.prompt(at_date=at_date)}\n")

        return "\n".join(lines)

    def get_patient_smrs(self, flagged: bool | None = None) -> list[GPEvent]:
        smr_events = [
            e for e in self.events if e.event_type == EventType.GP_EVENT and e.was_smr
        ]

        if flagged is not None:
            smr_events = [e for e in smr_events if e.flag_smr == flagged]

        return smr_events

    def get_patient_smr_date_and_flag(
        self, flagged_if_possible: bool = True, use_changed: bool = True
    ) -> tuple[datetime, bool]:
        if use_changed:
            smr_events = self.get_patient_smrs()
            medication_changes = self.get_medication_changes(smr_events[0])
            if len(medication_changes) > 0:
                return smr_events[0].date, True
            else:
                return smr_events[0].date, False

        if flagged_if_possible:
            smr_events = self.get_patient_smrs(flagged=True)

        if len(smr_events) > 0:
            return smr_events[0].date, smr_events[0].flag_smr

        smr_events = self.get_patient_smrs()
        return smr_events[0].date, smr_events[0].flag_smr

    def get_prompt_and_outcome(self, event_span_years: int = 5) -> tuple[str, bool]:
        # Get the SMR date and flag

        patient = self.sort_events_by_date()
        smr_date, smr_flag = patient.get_patient_smr_date_and_flag()

        # Filter events to the event span
        prompt = (
            patient.filter_events_more_recent_than(
                smr_date - timedelta(days=event_span_years * 365)
            )
            .filter_events_older_than(smr_date - timedelta(days=1))
            .filter_events_not_null_date()
            .sort_active_prescriptions_to_front_and_by_end_date(smr_date)
            .build_prompt(max_events=None, at_date=smr_date)
        )

        return prompt, smr_flag

    def get_medication_changes(self, event: GPEvent) -> list[MedicationChange]:
        # Get all the medication changes for the patient

        medication_changes = self.get_events_by_type(EventType.MEDICATION_CHANGE)

        # Get only those that happened with the same datetime as the provided event

        medication_changes = [
            medication_change
            for medication_change in medication_changes
            if medication_change.date == event.date
        ]

        return medication_changes

    def sort_active_prescriptions_to_front_and_by_end_date(
        self, at_date: datetime
    ) -> "PatientProfile":
        # Moves the prescriptions to the front of the event list, and sorts them so the prescriptions with the most recent end date are first

        active_prescriptions = [
            x
            for x in self.events
            if x.event_type == EventType.PRESCRIPTION
            and x.end_date
            and x.end_date > at_date
        ]
        active_prescriptions.sort(key=lambda x: x.end_date, reverse=True)

        self.events = active_prescriptions + [
            x
            for x in self.events
            if x.event_type != EventType.PRESCRIPTION
            or (
                x.event_type == EventType.PRESCRIPTION
                and x.end_date
                and x.end_date <= at_date
            )
        ]

        return self


def format_qof_registers(qof_registers: str) -> str:
    return "\n".join(
        [f"- {qof_register_lookup.get(r, r)}" for r in qof_registers.split("|")]
    )


def format_frailty_deficit_list(frailty_deficit_list: str) -> str:
    return "\n".join(
        [
            f"- {frailty_deficit_lookup.get(r, r)}"
            for r in frailty_deficit_list.split("|")
        ]
    )
