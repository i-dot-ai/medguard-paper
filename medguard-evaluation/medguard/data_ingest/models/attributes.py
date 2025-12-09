from datetime import datetime
from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, Field, computed_field

from medguard.data_ingest.utils import (
    format_datetime,
    get_first_non_null,
    update_datetime_prompt,
    update_prompt,
)


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


class Medication(BaseEvent):
    event_type: EventType = EventType.MEDICATION
    start_date: datetime = Field(alias="computed_start_date")
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
        res = update_prompt(res, self.repeat_medication_flag, "Is a repeat medication: ")

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
        res = update_prompt(res, self.episodity, descriptor=", Episodity ", newline=False)
        return res

    class Config:
        validate_by_name = True


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
        if self.date == at_date:
            res = "GP Event - this is the Structured Medication Review (SMR)"
        else:
            res = "GP Event"

        res = update_datetime_prompt(res, self.event_date, " on ", newline=False)
        res += " with the following observations:"

        for i, observation in enumerate(self.observations):
            res += f"\n{i + 1}. " + observation.prompt()

        return res


class InpatientEpisode(BaseEvent):
    event_type: EventType = EventType.INPATIENT_EPISODE
    admission_date: Optional[datetime] = Field(None, alias="AdmissionDate")
    admission_type_description: Optional[str] = Field(None, alias="AdmissionTypeDescription")
    admission_source_description: Optional[str] = Field(None, alias="AdmissionSourceDescription")
    admission_category_description: Optional[str] = Field(
        None, alias="AdmissionCategoryDescription"
    )
    expected_discharge_date: Optional[datetime] = Field(None, alias="ExpectedDischargeDate")
    transfer_date: Optional[datetime] = Field(None, alias="TransferDate")
    discharge_date: Optional[datetime] = Field(None, alias="DischargeDate")
    discharge_method_description: Optional[str] = Field(None, alias="DischargeMethodDescription")
    discharge_destination_description: Optional[str] = Field(
        None, alias="DischargeDestinationDescription"
    )
    ward_description: Optional[str] = Field(None, alias="WardDescription")
    specialty_description: Optional[str] = Field(None, alias="SpecialtyDescription")

    @computed_field
    @property
    def date(self) -> Optional[datetime]:
        return get_first_non_null("admission_date", "transfer_date", "discharge_date")(self)

    def prompt(self, at_date: datetime | None = None) -> str:
        res = "Inpatient Episode"
        res = update_datetime_prompt(res, self.admission_date, " on ", newline=False)
        res = update_prompt(res, self.admission_type_description, "Admission type: ")
        res = update_prompt(res, self.admission_source_description, "Admitted from: ")
        res = update_prompt(res, self.admission_category_description, "Admission category: ")
        res = update_prompt(res, self.discharge_method_description, "Discharge method: ")
        res = update_prompt(res, self.discharge_destination_description, "Discharged to: ")
        res = update_prompt(res, self.ward_description, "Ward: ")
        res = update_prompt(res, self.specialty_description, "Specialty: ")
        res = update_datetime_prompt(res, self.expected_discharge_date, "Expected discharge date: ")
        res = update_datetime_prompt(res, self.transfer_date, "Transfer date: ")
        res = update_datetime_prompt(res, self.discharge_date, "Discharge date: ")
        return res


class AEVisit(BaseEvent):
    event_type: EventType = EventType.AE_VISIT
    attendance_date: Optional[datetime] = Field(None, alias="AttendanceDate")
    expected_discharge_date: Optional[datetime] = Field(None, alias="ExpectedDischargeDate")
    discharge_date: Optional[datetime] = Field(None, alias="DischargeDate")
    discharge_method_description: Optional[str] = Field(None, alias="DischargeMethodDescription")
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

        res = update_datetime_prompt(res, self.expected_discharge_date, "Expected discharge date: ")
        res = update_datetime_prompt(res, self.discharge_date, "Discharge date: ")
        res = update_prompt(res, self.discharge_method_description, "Discharge Method: ")
        res = update_prompt(res, self.discharge_destination_description, "Discharge Destination: ")
        res = update_prompt(res, self.location_description, "Location: ")
        res = update_prompt(res, self.reason_for_attendance_description, "Reason for Attendance: ")
        return res


class OutpatientVisit(BaseEvent):
    event_type: EventType = EventType.OUTPATIENT_VISIT
    referral_date: Optional[datetime] = Field(None, alias="ReferralDate")
    attendance_date: Optional[datetime] = Field(None, alias="AttendanceDate")
    process_date: Optional[datetime] = Field(None, alias="ProcessDate")
    discharge_date: Optional[datetime] = Field(None, alias="DischargeDate")
    discharge_method_description: Optional[str] = Field(None, alias="DischargeMethodDescription")
    clinic_description: Optional[str] = Field(None, alias="ClinicDescription")
    referral_outcome: Optional[str] = Field(None, alias="ReferralOutcome")
    specialty_description: Optional[str] = Field(None, alias="SpecialtyDescription")
    attendance_type_description: Optional[str] = Field(None, alias="AttendanceTypeDescription")

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
        res = update_prompt(res, self.discharge_method_description, "Discharge Method: ")
        return res


class Allergy(BaseEvent):
    event_type: EventType = EventType.ALLERGY
    allergen_type_code: Optional[str] = Field(None, alias="AllergenTypeCode")
    allergen_description: Optional[str] = Field(None, alias="AllergenDescription")
    allergen_reference: Optional[str] = Field(None, alias="AllergenReference")
    allergen_code_system: Optional[str] = Field(None, alias="AllergenCodeSystem")
    allergen_severity: Optional[str] = Field(None, alias="AllergenSeverity")
    allergen_reaction_code: Optional[str] = Field(None, alias="AllergenReactionCode")
    allergen_recorded_date: Optional[datetime] = Field(None, alias="AllergenRecordedDate")

    @computed_field
    @property
    def date(self) -> Optional[datetime]:
        return get_first_non_null("allergen_recorded_date")(self)

    def prompt(self, at_date: datetime | None = None) -> str:
        res = "Allergy recorded"
        res = update_datetime_prompt(res, self.allergen_recorded_date, " on ", newline=False)
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
    NO_CHANGE = "no_change"


class MedicationChange(BaseEvent):
    event_type: EventType = EventType.MEDICATION_CHANGE
    date: Optional[datetime] = Field(None, alias="smr_date")
    description: Optional[str] = Field(None, alias="medication_name")
    change_type: ChangeType

    def prompt(self, at_date: datetime | None = None) -> str:
        res = f"Medication Change: {self.description} was {self.change_type.value} on {self.date}"

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
        return self.end_date

    def active_at_date(self, at_date: datetime) -> bool:
        if at_date is None:
            return False
        # start_date must be before at_date, and end_date must be after at_date
        return self.start_date < at_date and self.end_date > at_date

    def active_during_period(self, start_date: datetime, end_date: datetime) -> bool:
        # start_date must be before end_date, and start_date must be before at_date
        return self.start_date <= end_date and start_date <= self.end_date

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

        if at_date is None:
            # When at_date is None, just show start and end dates without status
            if self.end_date:
                res += f"\nCourse end date: {format_datetime(self.end_date)}"
            res = update_prompt(
                res, str(self.duration_days), "Total length of prescription (days): "
            )
        else:
            # Original logic when at_date is provided
            # Determine if the medication is currently being taken

            # Note, to be consistent with the definition of medication change having a 3 month window, we claim that a medication is being taken if it's end date is within 3 months of the SMR date
            is_currently_being_taken = self.active_at_date(at_date)

            if is_currently_being_taken:
                res += "\nMedication being taken at the time of the SMR"
            else:
                res += f"\nCourse end date: {format_datetime(self.end_date)}"
                res += "\nMedication not being taken at the time of the SMR"
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
