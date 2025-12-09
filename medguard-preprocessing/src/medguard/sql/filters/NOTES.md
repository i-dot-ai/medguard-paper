# Filter Implementation Notes

This document tracks filters that cannot be implemented with the current data sources and explains why.

## Filters Not Implemented

### Filter 024: Methotrexate prescriptions should state 'weekly'

**Reason:** This filter requires checking free-text dosing instructions to verify that the prescription explicitly states "weekly" dosing. While the `SharedCare_GP_Medications` table contains a `Dosage` field, this field is not consistently populated with structured text that can be reliably parsed to detect the presence/absence of "weekly" instructions.

**What would be needed:**
- Structured dosing instruction field with consistent formatting
- OR Natural language processing to parse free-text `Dosage` field
- OR Integration with prescription system that enforces structured dosing intervals

**Clinical context:** Methotrexate for rheumatological/dermatological conditions is dosed weekly, but daily dosing errors have led to serious adverse events and deaths. The PINCER intervention aimed to ensure prescriptions explicitly state "weekly" to prevent confusion.

**Alternative approaches:**
- Could flag methotrexate prescriptions where `Dosage` field is NULL or empty
- Could flag prescriptions with very short `CourseLengthPerIssue` suggesting daily rather than weekly dosing
- However, these would have high false positive rates without reliable dosing instruction text

### Filter 025: Methotrexate 2.5/10mg co-prescription

**Status:** May be implementable if we can identify simultaneous prescriptions of both 2.5mg and 10mg methotrexate tablets to the same patient. This would require checking for overlapping prescription periods of different strengths.

**To be determined:** Whether the current data structure supports identifying this pattern reliably.

### Filter 048: Warfarin without INR monitoring (excluding self-monitoring patients)

**Reason:** This filter requires identifying patients who self-monitor their INR at home using portable devices. While we found one SNOMED code for portable INR monitoring devices (440432009 - "International normalised ratio result obtained using portable international normalised ratio monitoring device"), we cannot confidently identify all self-monitoring patients from the available data.

**What would be needed:**
- Comprehensive codes for all self-monitoring scenarios (home testing, patient self-management programs)
- Structured data indicating patient enrollment in self-monitoring programs
- Records of portable INR device prescriptions or provision

**Clinical context:** Self-monitoring patients test their own INR at home using portable devices and may not have formal GP records of all INR measurements. The filter needs to exclude these patients to avoid false positives, but without reliable identification of self-monitoring status, the filter would have high false positive rates.

**Partial implementation possible:** Could implement the filter without the self-monitoring exclusion, but this would flag some patients inappropriately and reduce clinical utility.
