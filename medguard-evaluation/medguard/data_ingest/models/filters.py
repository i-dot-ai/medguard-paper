from datetime import datetime
from enum import Enum

from pydantic import BaseModel, computed_field

from medguard.data_ingest.utils import format_datetime


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
    FilterType.NO_MATCH: "Choose this if the patient does not match any of the clinical filters",
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
    FilterType.NO_MATCH: [],
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
        return filter_descriptions.get(FilterType(self.filter_id), f"Filter {self.filter_id}")

    def prompt(self) -> str:
        """Generate a prompt-friendly description of this filter match"""
        return f"Filter {self.filter_id}: {self.description} (Period: {format_datetime(self.start_date)} to {format_datetime(self.end_date)})"

    def active_at_date(self, at_date: datetime) -> bool:
        return self.start_date < at_date and self.end_date > at_date


def get_filter_description() -> str:
    res = ""
    for filter in FilterType:
        res += f"Category Number {filter.value}: {filter_descriptions[filter]}\n"
        for i, factor in enumerate(filter_factors[filter]):
            res += f"  {i + 1}. {factor}\n"
        res += "\n\n"
    return res
