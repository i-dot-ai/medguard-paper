from pathlib import Path

from medguard.data_ingest.models.patient_profile import PatientProfile
from medguard.evaluation.utils import load_patient_profiles_from_jsonl
from medguard.utils.parsing import save_pydantic_list_to_jsonl
from medguard.vignette.pipeline import get_active_and_repeat_prescriptions


def sanitise_patient_profile(profile: PatientProfile) -> PatientProfile:
    # We remove all patient events that aren't either active or repeat prescriptions. This is consistent with the patient vignettes

    profile.events = get_active_and_repeat_prescriptions(profile)

    return profile


def sanitise_patient_profiles(profiles: list[PatientProfile]) -> list[PatientProfile]:
    return [sanitise_patient_profile(x) for x in profiles]


def run_sanitise_patient_profiles(
    input_path: Path, output_path: Path, patient_ids: list[int] | None = None
):
    # Load the patient profiles
    profiles = load_patient_profiles_from_jsonl(input_path)

    if patient_ids:
        filtered_profiles = [x for x in profiles if x.patient_link_id in patient_ids]
    else:
        filtered_profiles = profiles

    print("PROFILE LENGTH", len(filtered_profiles))

    # Sanitise them
    sanitised_profiles = sanitise_patient_profiles(filtered_profiles)

    # Save it
    save_pydantic_list_to_jsonl(sanitised_profiles, output_path)
