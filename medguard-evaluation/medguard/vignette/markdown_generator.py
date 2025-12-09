"""
Generate markdown files from patient vignettes with clinician feedback.
"""

from medguard.vignette.models import PatientVignetteWithFeedback, ClinicalIssue, Prescription


def format_days_human_readable(days: int) -> str:
    """
    Convert days to human-readable format (years, months, days).

    Args:
        days: Number of days (positive for time in past)

    Returns:
        Formatted string like "3 years, 2 months ago"
    """
    abs_days = abs(days)

    years = abs_days // 365
    remaining_days = abs_days % 365
    months = remaining_days // 30
    days_remainder = remaining_days % 30

    parts = []
    if years > 0:
        parts.append(f"{years} year{'s' if years != 1 else ''}")
    if months > 0:
        parts.append(f"{months} month{'s' if months != 1 else ''}")
    if days_remainder > 0 and years == 0:  # Only show days if less than a year
        parts.append(f"{days_remainder} day{'s' if days_remainder != 1 else ''}")

    if not parts:
        return "today"

    result = ", ".join(parts)
    return f"{result} ago"


def generate_markdown_from_vignette_with_feedback(vignette: PatientVignetteWithFeedback) -> str:
    """
    Generate markdown from a patient vignette with clinician feedback.
    Only includes MedGuard analysis and clinician feedback (no patient demographics or prescriptions).

    Args:
        vignette: PatientVignetteWithFeedback instance

    Returns:
        Markdown string
    """
    feedback = vignette.clinician_feedback

    # Header
    md = f"# Patient {vignette.patient_id_hash[:16]}\n\n"
    md += "---\n\n"

    # MedGuard Analysis
    md += "## MedGuard Analysis\n\n"

    intervention_emoji = "🔴" if vignette.medguard_intervention_required else "🟢"
    intervention_text = "Yes" if vignette.medguard_intervention_required else "No"
    md += f"### Intervention Required: {intervention_emoji} **{intervention_text}**\n\n"
    md += f"*Confidence: {vignette.medguard_intervention_probability:.0%}*\n\n"

    # Patient Review
    md += "### Patient Review\n\n"
    md += f"{vignette.medguard_patient_review}\n\n"

    # Clinical Issues
    if vignette.medguard_clinical_issues:
        md += "### Clinical Issues\n\n"
        for idx, issue in enumerate(vignette.medguard_clinical_issues, 1):
            intervention_emoji = "⚠️" if issue.intervention_required else "ℹ️"
            md += f"#### {intervention_emoji} Issue {idx}\n\n"
            md += f"**Issue:** {issue.issue}\n\n"
            md += f"**Evidence:** {issue.evidence}\n\n"
            md += f"**Intervention Required:** {issue.intervention_required}\n\n"

    # Intervention
    md += "### Proposed Intervention\n\n"
    md += f"{vignette.medguard_intervention}\n\n"

    md += "---\n\n"

    # Clinician Feedback
    md += "## 👨‍⚕️ Clinician Feedback\n\n"

    # Data Error
    if feedback.data_error:
        md += "### ⚠️ Data Error Identified\n\n"
        md += f"{feedback.data_error_explanation or 'No explanation provided'}\n\n"

    # Agreement with Rules
    if feedback.agrees_with_rules == "no":
        md += "### ⚠️ Disagrees with PINCER Rules\n\n"
        md += f"{feedback.rules_assessment_reasoning or 'No reasoning provided'}\n\n"
    elif feedback.agrees_with_rules == "yes":
        md += "### ✅ Agrees with PINCER Rules\n\n"
        md += f"**MedGuard Identified Rule Issues:** {feedback.medguard_identified_rule_issues}\n\n"
        md += f"**MedGuard Addressed Rule Issues:** {feedback.medguard_addressed_rule_issues}\n\n"

    # Issue Assessments
    if feedback.issue_assessments:
        md += "### Issue Assessments\n\n"
        for idx, (correct, reasoning) in enumerate(
            zip(feedback.issue_assessments, feedback.issue_reasoning), 1
        ):
            emoji = "✅" if correct else "❌"
            md += f"{idx}. {emoji} **{'Correct' if correct else 'Incorrect'}**\n"
            md += f"   - {reasoning}\n\n"

    # Missed Issues
    md += f"### Missed Issues: {feedback.missed_issues}\n\n"
    if feedback.missed_issues_detail:
        md += f"{feedback.missed_issues_detail}\n\n"

    # Intervention Assessment
    md += f"### Intervention Assessment: {feedback.medguard_specific_intervention}\n\n"
    md += f"{feedback.medguard_specific_intervention_reasoning}\n\n"

    # What Intervention Should Be
    md += "### What Intervention Should Be\n\n"
    md += f"{feedback.intervention_should_be}\n\n"

    # Failure Modes
    if feedback.failure_modes:
        md += "### Failure Modes\n\n"
        for mode in feedback.failure_modes:
            explanation = feedback.failure_mode_explanations.get(mode, "No explanation provided")
            md += f"- **{mode}:** {explanation}\n"
        md += "\n"

    md += "---\n\n"

    return md
