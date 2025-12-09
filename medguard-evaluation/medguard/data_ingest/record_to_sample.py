from uuid import uuid4

from inspect_ai.dataset import Sample

from medguard.data_ingest.models.attributes import (
    AEVisit,
    Allergy,
    Event,
    GPEvent,
    InpatientEpisode,
    MedicationChange,
    OutpatientVisit,
    Prescription,
    SocialCareEvent,
)
from medguard.data_ingest.models.patient_profile import PatientProfile


def load_profile_json_to_pydantic(profile_json: dict) -> PatientProfile:
    profile_json = profile_json.copy()

    # Currently, we remove the medication entries from the profile.
    aggregation_handlers: dict[str, type[Event]] = {
        # 'medication': Medication,
        "gp_event": GPEvent,
        "inpatient_episode": InpatientEpisode,
        "ae_visit": AEVisit,
        "outpatient_visit": OutpatientVisit,
        "allergy": Allergy,
        "social_care_event": SocialCareEvent,
        "medication_change": MedicationChange,
        "prescription": Prescription,
    }

    events: list[dict] = profile_json["events"]

    profile_json["events"] = []

    profile = PatientProfile.model_validate(profile_json)

    for event in events:
        event_type = event["event_type"]
        if event_type in aggregation_handlers:
            event_model = aggregation_handlers[event_type]
            profile.events.append(event_model.model_validate(event))

    return profile


def record_to_sample(record: dict) -> Sample:
    patient = load_profile_json_to_pydantic(record)

    prompt, review_date = patient.get_prompt_and_date()

    return Sample(
        input=prompt,
        target=str(patient.matched_filters),
        id=str(uuid4()),
        metadata={
            "patient_id": patient.patient_link_id,
            "review_date": review_date,
            "matched_filters": [
                filter_match.model_dump()
                for filter_match in patient.get_active_filters(review_date)
            ],
        },
    )
