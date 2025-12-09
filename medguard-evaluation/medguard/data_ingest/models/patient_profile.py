from datetime import date, datetime, timedelta
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from medguard.data_ingest.models.attributes import (
    AEVisit,
    Allergy,
    Event,
    EventType,
    GPEvent,
    InpatientEpisode,
    Medication,
    MedicationChange,
    Observation,
    OutpatientVisit,
    Prescription,
    Sex,
    SocialCareEvent,
)
from medguard.data_ingest.models.filters import FilterMatch
from medguard.data_ingest.utils import (
    calculate_age,
    datetime_midpoint,
    format_date,
    format_datetime,
    format_frailty_deficit_list,
    format_qof_registers,
    get_random_date_between,
)


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

    sample_date: Optional[datetime] = Field(None)

    # Events - will be populated from the aggregations
    events: List[Event] = Field(default_factory=list)

    class Config:
        validate_by_name = True

    @classmethod
    def model_json_schema(cls, **kwargs):
        """Always generate JSON schema with field names, not aliases"""
        return super().model_json_schema(by_alias=False, **kwargs)

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

    def sort_events_by_date(self, reverse: bool = True) -> "PatientProfile":
        """Sort all events by date (most recent first), with None dates at the end."""
        self.events.sort(key=lambda x: x.date or datetime.min, reverse=reverse)
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

    def _build_prompt_patient(self, at_date: datetime | None = None) -> str:
        """Build a patient summary prompt."""
        # Determine reference date for age: date of the most recent event if available
        reference_date_for_age: Optional[date] = at_date.date()

        # Header: identity, demographics
        sex_display = (
            self.sex.value if isinstance(self.sex, Sex) else (self.sex or Sex.UNKNOWN.value)
        )

        # Compute age using reference date if possible
        age_display = None
        if self.date_of_birth and reference_date_for_age:
            age = calculate_age(self.date_of_birth, reference_date_for_age)
            age_display = str(age) if age is not None else None

        lines: List[str] = []

        lines.append(f"Date of the Structured Medical Review (SMR): {format_datetime(at_date)}")
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

        return "\n".join(lines)

    def _build_prompt_events(
        self,
        at_date: datetime | None = None,
        max_events: int | None = 5,
        exclude_medication_changes: bool = True,
    ) -> str:
        lines: List[str] = []

        if max_events is None:
            max_events = len(self.events)

        if max_events > 0 and self.events:
            lines.append(f"\nPatient Events ({min(max_events, len(self.events))}):\n")
            for idx, e in enumerate(self.events[:max_events], start=1):
                if exclude_medication_changes and e.event_type == EventType.MEDICATION_CHANGE:
                    continue

                lines.append(f"Event {idx} - {e.prompt(at_date=at_date)}\n")

        return "\n".join(lines)

    def build_prompt(
        self,
        max_events: int | None = 5,
        at_date: datetime | None = None,
    ) -> str:
        """
        Build a patient summary prompt.

        Parameters
        - max_events: number of most recent events to list across all types
        - events: if provided, use this list of events; if None, include all events on the profile
        """
        patient_prompt = self._build_prompt_patient(at_date=at_date)
        events_prompt = self._build_prompt_events(at_date=at_date, max_events=max_events)

        return f"{patient_prompt}\n\n{events_prompt}"

    def get_patient_smrs(self, flagged: bool | None = None) -> list[GPEvent]:
        smr_events = [e for e in self.events if e.event_type == EventType.GP_EVENT and e.was_smr]

        if flagged is not None:
            smr_events = [e for e in smr_events if e.flag_smr == flagged]

        return smr_events

    def get_patient_smr_date_and_flag(
        self, flagged_if_possible: bool = True, use_changed: bool = True
    ) -> tuple[datetime, bool]:
        if use_changed:
            smr_events = self.get_patient_smrs()
            medication_changes = self.get_medication_changes(smr_events[0].date)
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

    def get_patient_smr_findings(self, date: datetime) -> list[Observation]:
        smr_event = [
            x for x in self.get_events_by_type(EventType.GP_EVENT) if x.was_smr and x.date == date
        ][0]

        observations = [x for x in smr_event.observations if "(finding)" in x.description]
        return observations

    def add_prescription_events(self, events: list[Prescription]) -> "PatientProfile":
        # Check that we're only adding Prescription events
        if not all(isinstance(x, Prescription) for x in events):
            raise ValueError("Only Prescription events can be added to the patient profile")

        # Get a list of the existing prescription events
        existing_events = [
            (x.start_date, x.end_date, x.snomed_code)
            for x in self.events
            if x.event_type == EventType.PRESCRIPTION
        ]

        # For each of the new events, check if it overlaps with any of the existing events
        for event in events:
            if (event.start_date, event.end_date, event.snomed_code) in existing_events:
                continue
            else:
                self.events.append(event)

        return self

    def get_prompt_and_date(
        self, event_span_years: int = 5, character_limit: int = 30_000 * 3
    ) -> tuple[str, bool]:
        # Get the patient and
        patient = self.sort_events_by_date()
        review_date = patient.get_active_filter_date()

        active_prescriptions: list[Prescription] = [
            x
            for x in patient.get_events_by_type(EventType.PRESCRIPTION)
            if x.active_at_date(review_date)
        ]

        # Filter events to the event span
        prompt = (
            patient.filter_events_more_recent_than(
                review_date - timedelta(days=event_span_years * 365)
            )
            .filter_events_older_than(review_date - timedelta(days=1))
            .filter_events_not_null_date()
            .add_prescription_events(active_prescriptions)
            .sort_active_prescriptions_to_front_and_by_end_date(review_date)
            .build_prompt(max_events=None, at_date=review_date)
        )

        return prompt[:character_limit], review_date

    def get_medication_changes(self, date: datetime) -> list[MedicationChange]:
        # Get all the medication changes for the patient

        medication_changes = self.get_events_by_type(EventType.MEDICATION_CHANGE)

        # Get only those that happened with the same datetime as the provided event

        medication_changes = [
            medication_change
            for medication_change in medication_changes
            if medication_change.date == date
        ]

        return medication_changes

    def sort_active_prescriptions_to_front_and_by_end_date(
        self, at_date: datetime
    ) -> "PatientProfile":
        # Moves the prescriptions to the front of the event list, and sorts them so the prescriptions with the most recent end date are first

        # Note, to be consistent with the definition of medication change having a 3 month window, we claim that a medication is being taken if it's end date is within 3 months of the SMR date
        active_prescriptions = [
            x
            for x in self.events
            if x.event_type == EventType.PRESCRIPTION and x.active_at_date(at_date)
        ]

        active_prescriptions.sort(key=lambda x: x.end_date, reverse=True)

        self.events = active_prescriptions + [
            x
            for x in self.events
            if x.event_type != EventType.PRESCRIPTION
            or (
                x.event_type == EventType.PRESCRIPTION
                and not x.active_during_period(at_date - timedelta(days=91), at_date)
            )
        ]

        return self

    def get_active_filter_date(self, get_date_for_no_filters: bool = True) -> datetime | None:
        # If there are active filters, return the date halfway between the start and end dates of the filters
        if len(self.matched_filters) == 0 and get_date_for_no_filters:
            # otherwise a random date from 2023-01-01 to 2025-01-01
            return self.sample_date or get_random_date_between(
                datetime(2023, 1, 1), datetime(2025, 1, 1)
            )

        if len(self.matched_filters) == 0 and not get_date_for_no_filters:
            return None

        return datetime_midpoint(
            self.matched_filters[0].start_date, self.matched_filters[0].end_date
        )

    def get_active_filters(self, at_date: datetime) -> list[FilterMatch]:
        return [filter for filter in self.matched_filters if filter.active_at_date(at_date)]

    def count_number_active_medications(self, at_date: datetime) -> int:
        return len(
            [
                x
                for x in self.events
                if x.event_type == EventType.PRESCRIPTION and x.active_at_date(at_date)
            ]
        )

    def get_active_filter(self) -> FilterMatch | None:
        return self.matched_filters[0] if len(self.matched_filters) > 0 else None

    def get_age(self, at_date: datetime) -> int | None:
        return calculate_age(self.date_of_birth, at_date.date())

    def get_number_qof_registers(self) -> int:
        return len(self.qof_registers.split("|")) if self.qof_registers else 0
