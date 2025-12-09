"""Business logic for processing patient data."""

from datetime import timedelta
from typing import Any, Dict, List

from medguard.data_ingest.models.attributes import EventType
from medguard.scorer.models import AnalysedPatientRecord


def get_pre_smr_events(record: AnalysedPatientRecord) -> List[Dict[str, Any]]:
    """
    Get events available before the SMR, following the logic from prompt builder.

    Returns events as JSON-serializable dicts with event_type field.
    """
    patient = record.patient.model_copy(deep=True)
    smr_date = record.analysis_date

    # Filter to events before SMR (using similar logic to get_prompt_and_outcome)
    event_span_years = 5

    # Get active prescriptions at SMR date
    active_prescriptions = [
        x for x in patient.get_events_by_type(EventType.PRESCRIPTION) if x.active_at_date(smr_date)
    ]

    # Filter and sort events
    filtered_patient = (
        patient.filter_events_more_recent_than(smr_date - timedelta(days=event_span_years * 365))
        .filter_events_older_than(smr_date - timedelta(days=1))
        .filter_events_not_null_date()
        .add_prescription_events(active_prescriptions)
        .sort_active_prescriptions_to_front_and_by_end_date(smr_date)
        .sort_events_by_date(reverse=False)
    )

    # Convert events to dict format
    return [event.model_dump() for event in filtered_patient.events]


def get_post_smr_events(
    record: AnalysedPatientRecord, event_span_months: int = 12
) -> List[Dict[str, Any]]:
    """
    Get events that occurred after the SMR within the specified window.

    Returns events as JSON-serializable dicts with event_type field.
    """
    patient = record.patient.model_copy(deep=True)
    smr_date = record.analysis_date
    end_date = smr_date + timedelta(days=event_span_months * 30)

    # Get active prescriptions during the post-SMR period
    # Note: Using 3-month window for medication consistency
    active_prescriptions = [
        x
        for x in patient.get_events_by_type(EventType.PRESCRIPTION)
        if x.active_during_period(smr_date - timedelta(days=91), end_date)
    ]

    # Filter to post-SMR events
    filtered_patient = (
        patient.filter_events_more_recent_than(smr_date - timedelta(days=1))
        .filter_events_older_than(end_date)
        .filter_events_not_null_date()
        .add_prescription_events(active_prescriptions)
        .sort_events_by_date(reverse=False)
        .sort_active_prescriptions_to_front_and_by_end_date(smr_date)
    )

    # Convert events to dict format
    return [event.model_dump() for event in filtered_patient.events]


def get_all_events(record: AnalysedPatientRecord) -> List[Dict[str, Any]]:
    """
    Get all events for a patient.

    Returns events as JSON-serializable dicts with event_type field.
    """
    return [event.model_dump() for event in record.patient.events]
