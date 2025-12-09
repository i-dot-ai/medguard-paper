from medguard.data_ingest.models.patient_profile import PatientProfile
from medguard.scorer.models import MedGuardAnalysis
from medguard.vignette.models import (
    ClinicalIssue,
    PatientVignette,
    PatientVignetteWithFeedback,
    Prescription,
)
from medguard.data_ingest.models.attributes import EventType, Prescription as DataIngestPrescription
from medguard.evaluation.clinician.models import Stage2Data

from medguard.data_ingest.utils import qof_registers_to_list, frailty_deficit_list_to_list
from medguard.vignette.parser.parser import replace_absolute_dates_with_relative

from datetime import date

from hashlib import sha256


def get_active_and_repeat_prescriptions(
    patient_profile: PatientProfile,
) -> list[DataIngestPrescription]:
    prescriptions: list[DataIngestPrescription] = patient_profile.get_events_by_type(
        EventType.PRESCRIPTION
    )

    return [
        prescription
        for prescription in prescriptions
        if prescription.active_at_date(patient_profile.sample_date)
        or prescription.is_repeat_medication
    ]


def convert_prescriptions_to_vignette_prescriptions(
    prescriptions: list[DataIngestPrescription], sample_date: date
) -> list[Prescription]:
    return [
        Prescription(
            active_at_review=prescription.active_at_date(sample_date),
            days_since_start=(sample_date - prescription.start_date).days,
            days_since_end=(sample_date - prescription.end_date).days,
            description=prescription.description,
            dosage=prescription.dosage,
            units=prescription.units,
            is_repeat_medication=prescription.is_repeat_medication,
        )
        for prescription in prescriptions
    ]


def get_prescriptions(patient_profile: PatientProfile) -> list[Prescription]:
    return convert_prescriptions_to_vignette_prescriptions(
        get_active_and_repeat_prescriptions(patient_profile), patient_profile.sample_date
    )


def clean_clinical_issues(
    clinical_issues: list[ClinicalIssue], sample_date: date
) -> list[ClinicalIssue]:
    return [
        ClinicalIssue(
            issue=replace_absolute_dates_with_relative(clinical_issue.issue, sample_date),
            evidence=replace_absolute_dates_with_relative(clinical_issue.evidence, sample_date),
            intervention_required=clinical_issue.intervention_required,
        )
        for clinical_issue in clinical_issues
    ]


def generate_vignette(
    patient_profile: PatientProfile, medguard_analysis: MedGuardAnalysis
) -> PatientVignette:
    return PatientVignette(
        patient_id_hash=sha256(str(patient_profile.patient_link_id).encode()).hexdigest(),
        age=patient_profile.get_age(patient_profile.sample_date),
        sex=patient_profile.sex,
        imd_percentile=patient_profile.imd_score / 32844 * 100,
        frailty_score=patient_profile.frailty_score,
        qof_registers=qof_registers_to_list(patient_profile.qof_registers),
        frailty_deficit_list=frailty_deficit_list_to_list(patient_profile.frailty_deficit_list),
        prescriptions=get_prescriptions(patient_profile),
        medguard_patient_review=replace_absolute_dates_with_relative(
            medguard_analysis.patient_review, patient_profile.sample_date.date()
        ),
        medguard_clinical_issues=clean_clinical_issues(
            medguard_analysis.clinical_issues, patient_profile.sample_date.date()
        ),
        medguard_intervention=replace_absolute_dates_with_relative(
            medguard_analysis.intervention, patient_profile.sample_date.date()
        ),
        medguard_intervention_required=medguard_analysis.intervention_required,
        medguard_intervention_probability=medguard_analysis.intervention_probability,
    )


def generate_vignette_with_feedback(
    patient_profile: PatientProfile,
    medguard_analysis: MedGuardAnalysis,
    clinician_feedback: Stage2Data,
) -> PatientVignetteWithFeedback:
    base_vignette = generate_vignette(patient_profile, medguard_analysis)
    return PatientVignetteWithFeedback(
        **base_vignette.model_dump(),
        clinician_feedback=clinician_feedback,
    )
