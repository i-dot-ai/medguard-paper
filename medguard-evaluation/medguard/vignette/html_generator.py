"""
Generate static HTML files from patient vignettes for offline clinical review.
"""

from pathlib import Path
from medguard.vignette.models import (
    PatientVignette,
    PatientVignetteWithFeedback,
    ClinicalIssue,
    Prescription,
)


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


def generate_html_from_vignette(vignette: PatientVignette) -> str:
    """
    Generate a standalone HTML file from a patient vignette.

    Args:
        vignette: PatientVignette instance

    Returns:
        HTML string
    """

    # Generate patient information section
    patient_info_html = generate_patient_info_section(vignette)

    # Generate prescriptions section
    prescriptions_html = generate_prescriptions_section(vignette.prescriptions)

    # Generate MedGuard analysis section
    analysis_html = generate_analysis_section(vignette)

    # Complete HTML document
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Patient Vignette - {vignette.patient_id_hash[:8]}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{
            font-family: Arial, Helvetica, sans-serif;
            overflow: hidden;
        }}
        .hidden {{
            display: none !important;
        }}
    </style>
    <script>
        function searchPrescriptions() {{
            const searchTerm = document.getElementById('prescriptionSearch').value.toLowerCase();
            const prescriptionCards = document.querySelectorAll('.prescription-card');
            let visibleCount = 0;

            prescriptionCards.forEach(card => {{
                const description = card.getAttribute('data-description').toLowerCase();
                if (description.includes(searchTerm)) {{
                    card.classList.remove('hidden');
                    visibleCount++;
                }} else {{
                    card.classList.add('hidden');
                }}
            }});

            // Update count
            const countElement = document.getElementById('prescriptionCount');
            if (countElement) {{
                countElement.textContent = `${{visibleCount}} of ${{prescriptionCards.length}} prescriptions`;
            }}
        }}
    </script>
</head>
<body class="bg-gray-50">
    <div class="flex h-screen">
        <!-- Left Panel - Patient Information (60%) -->
        <div class="w-3/5 border-r border-gray-200 bg-white p-6 overflow-y-auto">
            <div class="space-y-4">
                {patient_info_html}
                {prescriptions_html}
            </div>
        </div>

        <!-- Right Panel - MedGuard Analysis (40%) -->
        <div class="w-2/5 bg-white p-6 overflow-y-auto">
            <div class="space-y-4">
                {analysis_html}
            </div>
        </div>
    </div>
</body>
</html>
"""
    return html


def generate_patient_info_section(vignette: PatientVignette) -> str:
    """Generate the patient information section."""

    # Demographics
    demographics_html = f"""
    <div class="bg-white border border-gray-200 rounded-xl shadow-sm">
        <div class="p-5">
            <h3 class="text-lg font-bold text-gray-900 mb-4 flex items-center">
                <div class="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                Patient Information
            </h3>

            <!-- Demographics Section -->
            <div class="mb-5">
                <h4 class="text-sm font-semibold text-gray-700 mb-2 uppercase tracking-wide">Demographics</h4>
                <div class="bg-blue-50 rounded-lg p-3 space-y-2 text-sm">
                    <div class="flex justify-between">
                        <span class="text-gray-600">Patient ID:</span>
                        <span class="font-medium text-gray-900">{vignette.patient_id_hash[:16]}...</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-600">Age:</span>
                        <span class="font-medium text-gray-900">{vignette.age} years</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-600">Sex:</span>
                        <span class="font-medium text-gray-900">{vignette.sex.value}</span>
                    </div>
                </div>
            </div>

            <!-- Clinical Status -->
            <div class="mb-5">
                <h4 class="text-sm font-semibold text-gray-700 mb-2 uppercase tracking-wide">Clinical Status</h4>
                <div class="bg-gray-50 rounded-lg p-3 space-y-2 text-sm">
                    <div class="flex justify-between">
                        <span class="text-gray-600">IMD Deprivation:</span>
                        <span class="font-medium text-gray-900">
                            {vignette.imd_percentile:.1f}%
                            <span class="text-xs text-gray-500 ml-1">(higher = less deprived)</span>
                        </span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-600">Frailty Score:</span>
                        <span class="font-medium text-gray-900">
                            {vignette.frailty_score:.2f}
                            <span class="text-xs text-gray-500 ml-1">(0.0-1.0 scale)</span>
                        </span>
                    </div>
                </div>
            </div>
    """

    # QOF Registers
    if vignette.qof_registers:
        qof_html = """
            <!-- QOF Registers -->
            <div class="mb-5">
                <h4 class="text-sm font-semibold text-gray-700 mb-2 uppercase tracking-wide">QOF Registers</h4>
                <div class="bg-green-50 rounded-lg p-3">
                    <div class="space-y-1 text-xs">
        """
        for register in vignette.qof_registers:
            qof_html += f"""
                        <div class="text-green-800 leading-relaxed">
                            • {register}
                        </div>
            """
        qof_html += """
                    </div>
                </div>
            </div>
        """
        demographics_html += qof_html

    # Frailty Deficits
    if vignette.frailty_deficit_list:
        frailty_html = """
            <!-- Frailty Deficits -->
            <div class="mb-5">
                <h4 class="text-sm font-semibold text-gray-700 mb-2 uppercase tracking-wide">Frailty Deficits</h4>
                <div class="bg-orange-50 rounded-lg p-3">
                    <div class="grid grid-cols-1 gap-1 text-xs">
        """
        for deficit in vignette.frailty_deficit_list:
            frailty_html += f"""
                        <div class="text-orange-800 flex items-start">
                            <span class="inline-block w-2 h-2 bg-orange-400 rounded-full mt-1.5 mr-2 flex-shrink-0"></span>
                            <span>{deficit}</span>
                        </div>
            """
        frailty_html += """
                    </div>
                </div>
            </div>
        """
        demographics_html += frailty_html

    demographics_html += """
        </div>
    </div>
    """

    return demographics_html


def generate_prescriptions_section(prescriptions: list[Prescription]) -> str:
    """Generate the prescriptions section."""

    if not prescriptions:
        return ""

    # Filter out prescriptions that haven't started yet (days_since_start < 0)
    # Then sort by days_since_end (most negative first = active prescriptions at top)
    started_prescriptions = [p for p in prescriptions if p.days_since_start >= 0]
    sorted_prescriptions = sorted(started_prescriptions, key=lambda p: p.days_since_end)

    html = f"""
    <div class="bg-white border border-gray-200 rounded-xl shadow-sm">
        <div class="p-5">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-bold text-gray-900">Prescriptions</h3>
                <span id="prescriptionCount" class="text-sm text-gray-600">{len(sorted_prescriptions)} of {len(sorted_prescriptions)} prescriptions</span>
            </div>

            <!-- Search Input -->
            <div class="mb-4">
                <input
                    type="text"
                    id="prescriptionSearch"
                    placeholder="Search prescriptions by description..."
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    oninput="searchPrescriptions()"
                />
            </div>

            <div class="space-y-3">
    """

    for prescription in sorted_prescriptions:
        start_display = format_days_human_readable(prescription.days_since_start)

        # Status badge
        status_badge = (
            """
                        <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">
                            Active
                        </span>
        """
            if prescription.active_at_review
            else """
                        <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-800">
                            Ended
                        </span>
        """
        )

        repeat_badge = (
            """
                        <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                            Repeat
                        </span>
        """
            if prescription.is_repeat_medication
            else ""
        )

        # Date information
        if prescription.active_at_review:
            date_info = f"""
                    <div class="text-sm text-gray-600">
                        <span class="font-medium">Started:</span> {start_display}
                    </div>
            """
        else:
            end_display = format_days_human_readable(prescription.days_since_end)
            date_info = f"""
                    <div class="text-sm text-gray-600">
                        <span class="font-medium">Started:</span> {start_display}
                    </div>
                    <div class="text-sm text-gray-600">
                        <span class="font-medium">Ended:</span> {end_display}
                    </div>
            """

        description_text = prescription.description or "Unnamed medication"
        # Escape quotes in description for data attribute
        escaped_description = description_text.replace('"', "&quot;").replace("'", "&#39;")

        html += f"""
                <div class="prescription-card border rounded-lg p-3 bg-white border-gray-200" data-description="{escaped_description}">
                    <div class="flex items-center gap-2 mb-1">
                        <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-800">
                            Prescription
                        </span>
                        {status_badge}
                        {repeat_badge}
                    </div>
                    <div class="font-medium text-gray-900 mb-1">
                        {description_text}
                    </div>
                    <div class="text-sm text-gray-700 mb-1">
                        {prescription.dosage or ""} {prescription.units or ""}
                    </div>
                    {date_info}
                </div>
        """

    html += """
            </div>
        </div>
    </div>
    """

    return html


def generate_analysis_section(vignette: PatientVignette) -> str:
    """Generate the MedGuard analysis section."""

    intervention_color = "red" if vignette.medguard_intervention_required else "green"
    intervention_text = "Yes" if vignette.medguard_intervention_required else "No"

    html = f"""
    <h3 class="text-lg font-semibold mb-4">MedGuard Analysis</h3>

    <!-- Intervention Required Summary -->
    <div class="border-2 rounded-xl p-4 shadow-sm mb-6 bg-{intervention_color}-50 border-{intervention_color}-200">
        <div class="flex items-center justify-between">
            <span class="font-semibold text-{intervention_color}-900">
                Intervention Required:
            </span>
            <span class="px-3 py-1.5 rounded-full text-sm font-bold bg-{intervention_color}-200 text-{intervention_color}-900">
                {intervention_text}
            </span>
        </div>
    </div>

    <!-- Patient Review -->
    <div class="border rounded-lg p-4 bg-white shadow-sm mb-4">
        <h4 class="font-medium mb-2">Patient Review</h4>
        <div class="text-sm text-gray-700 whitespace-pre-wrap">{vignette.medguard_patient_review}</div>
    </div>
    """

    # Clinical Issues
    if vignette.medguard_clinical_issues:
        html += """
    <div class="border rounded-lg p-4 bg-white shadow-sm mb-4">
        <h4 class="font-medium mb-4">Clinical Issues</h4>
        <div class="space-y-3">
        """

        for idx, issue in enumerate(vignette.medguard_clinical_issues, 1):
            issue_color = "red" if issue.intervention_required else "blue"
            issue_badge = (
                "Intervention Required" if issue.intervention_required else "No Intervention"
            )

            html += f"""
            <div class="border-l-4 pl-3 py-2 border-{issue_color}-600">
                <div class="flex items-start justify-between mb-2">
                    <h5 class="font-semibold text-gray-900">Issue {idx}</h5>
                    <span class="ml-3 px-2 py-1 rounded-full text-xs font-medium whitespace-nowrap bg-{issue_color}-100 text-{issue_color}-800">
                        {issue_badge}
                    </span>
                </div>
                <p class="font-medium text-gray-800 mb-1">{issue.issue}</p>
                <p class="text-sm text-gray-700 whitespace-pre-wrap">{issue.evidence}</p>
            </div>
            """

        html += """
        </div>
    </div>
        """

    # Intervention
    html += f"""
    <div class="border rounded-lg p-4 bg-white shadow-sm mb-4">
        <h4 class="font-medium mb-2">Intervention</h4>
        <div class="text-sm text-gray-700 whitespace-pre-wrap">{vignette.medguard_intervention}</div>
    </div>

    <!-- Intervention Probability -->
    <div class="border rounded-lg p-4 bg-white shadow-sm">
        <div class="flex items-center justify-between">
            <h4 class="font-medium">Intervention Probability</h4>
            <span class="text-2xl font-bold text-blue-600">
                {int(vignette.medguard_intervention_probability * 100)}%
            </span>
        </div>
        <p class="text-xs text-gray-500 mt-2">
            Probability that an intervention is required for this patient
        </p>
    </div>
    """

    return html


def save_vignette_html(vignette: PatientVignette, output_path: Path) -> None:
    """
    Generate and save HTML file for a vignette.

    Args:
        vignette: PatientVignette instance
        output_path: Path where to save the HTML file
    """
    html = generate_html_from_vignette(vignette)
    output_path.write_text(html, encoding="utf-8")


def generate_html_from_vignette_with_feedback(vignette: PatientVignetteWithFeedback) -> str:
    """
    Generate a standalone HTML file from a patient vignette with clinician feedback.

    Args:
        vignette: PatientVignetteWithFeedback instance

    Returns:
        HTML string
    """
    patient_info_html = generate_patient_info_section(vignette)
    prescriptions_html = generate_prescriptions_section(vignette.prescriptions)
    analysis_html = generate_analysis_with_feedback_section(vignette)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Patient Vignette - {vignette.patient_id_hash[:8]}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{
            font-family: Arial, Helvetica, sans-serif;
            overflow: hidden;
        }}
        .hidden {{
            display: none !important;
        }}
    </style>
    <script>
        function searchPrescriptions() {{
            const searchTerm = document.getElementById('prescriptionSearch').value.toLowerCase();
            const prescriptionCards = document.querySelectorAll('.prescription-card');
            let visibleCount = 0;

            prescriptionCards.forEach(card => {{
                const description = card.getAttribute('data-description').toLowerCase();
                if (description.includes(searchTerm)) {{
                    card.classList.remove('hidden');
                    visibleCount++;
                }} else {{
                    card.classList.add('hidden');
                }}
            }});

            const countElement = document.getElementById('prescriptionCount');
            if (countElement) {{
                countElement.textContent = `${{visibleCount}} of ${{prescriptionCards.length}} prescriptions`;
            }}
        }}
    </script>
</head>
<body class="bg-gray-50">
    <div class="flex h-screen">
        <!-- Left Panel - Patient Information (40%) -->
        <div class="w-2/5 border-r border-gray-200 bg-white p-6 overflow-y-auto">
            <div class="space-y-4">
                {patient_info_html}
                {prescriptions_html}
            </div>
        </div>

        <!-- Right Panel - MedGuard Analysis with Clinician Feedback (60%) -->
        <div class="w-3/5 bg-white p-6 overflow-y-auto">
            <div class="space-y-4">
                {analysis_html}
            </div>
        </div>
    </div>
</body>
</html>
"""
    return html


def generate_analysis_with_feedback_section(vignette: PatientVignetteWithFeedback) -> str:
    """Generate the MedGuard analysis section with clinician feedback."""
    feedback = vignette.clinician_feedback
    intervention_color = "red" if vignette.medguard_intervention_required else "green"
    intervention_text = "Yes" if vignette.medguard_intervention_required else "No"

    html = f"""
    <h3 class="text-lg font-semibold mb-4">MedGuard Analysis with Clinician Feedback</h3>

    <!-- Intervention Required Summary -->
    <div class="border-2 rounded-xl p-4 shadow-sm mb-6 bg-{intervention_color}-50 border-{intervention_color}-200">
        <div class="flex items-center justify-between">
            <span class="font-semibold text-{intervention_color}-900">
                Intervention Required:
            </span>
            <span class="px-3 py-1.5 rounded-full text-sm font-bold bg-{intervention_color}-200 text-{intervention_color}-900">
                {intervention_text}
            </span>
        </div>
    </div>
    """

    # Data Error Section (clinician feedback)
    if feedback.data_error:
        html += f"""
    <div class="border-2 border-red-500 rounded-lg p-4 bg-red-50 shadow-sm mb-4">
        <h4 class="font-semibold text-red-900 mb-2 flex items-center">
            <span class="inline-block px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs mr-2">CLINICIAN</span>
            <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
            </svg>
            Data Error Identified
        </h4>
        <div class="text-sm text-red-800 whitespace-pre-wrap">{feedback.data_error_explanation or "No explanation provided"}</div>
    </div>
        """

    # Agreement with Rules Section (clinician feedback - purple theme with semantic colors)
    if feedback.agrees_with_rules == "no":
        html += f"""
    <div class="border-2 border-yellow-500 rounded-lg p-4 bg-yellow-50 shadow-sm mb-4">
        <h4 class="font-semibold text-yellow-900 mb-2">
            <span class="inline-block px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs mr-2">CLINICIAN</span>
            Disagrees with PINCER Rules
        </h4>
        <div class="text-sm text-yellow-800 whitespace-pre-wrap">{feedback.rules_assessment_reasoning or "No reasoning provided"}</div>
    </div>
        """
    elif feedback.agrees_with_rules == "yes":
        # Show MedGuard identified rule issues when clinician agrees
        html += f"""
    <div class="border-2 border-green-500 rounded-lg p-4 bg-green-50 shadow-sm mb-4">
        <h4 class="font-semibold text-green-900 mb-2">
            <span class="inline-block px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs mr-2">CLINICIAN</span>
            Agrees with PINCER Rules
        </h4>
        <div class="text-sm mb-3 p-2 bg-white rounded border border-gray-300">
            <strong class="text-gray-900">MedGuard Identified Issues:</strong>
            <div class="whitespace-pre-wrap mt-1 text-gray-800">{feedback.medguard_identified_rule_issues or "None specified"}</div>
        </div>
        <div class="text-sm p-2 bg-white rounded border border-gray-300">
            <strong class="text-gray-900">MedGuard Addressed Issues:</strong>
            <div class="whitespace-pre-wrap mt-1 text-gray-800">{feedback.medguard_addressed_rule_issues or "None specified"}</div>
        </div>
    </div>
        """

    # Patient Review (MedGuard output - neutral theme)
    html += f"""
    <div class="border rounded-lg p-4 bg-white shadow-sm mb-4">
        <h4 class="font-semibold text-gray-900 mb-2">MedGuard Patient Review</h4>
        <div class="text-sm text-gray-700 whitespace-pre-wrap">{vignette.medguard_patient_review}</div>
    </div>
    """

    # Clinical Issues with Assessments
    if vignette.medguard_clinical_issues:
        html += """
    <div class="border rounded-lg p-4 bg-white shadow-sm mb-4">
        <h4 class="font-semibold text-gray-900 mb-4">MedGuard Clinical Issues</h4>
        <div class="space-y-4">
        """

        for idx, issue in enumerate(vignette.medguard_clinical_issues):
            issue_color = "red" if issue.intervention_required else "blue"
            issue_badge = (
                "Intervention Required" if issue.intervention_required else "No Intervention"
            )

            # Get clinician assessment for this issue
            is_correct = (
                feedback.issue_assessments[idx] if idx < len(feedback.issue_assessments) else None
            )
            reasoning = (
                feedback.issue_reasoning[idx] if idx < len(feedback.issue_reasoning) else None
            )

            html += f"""
            <div class="border-l-4 pl-3 py-2 border-gray-300 bg-gray-50 rounded shadow-sm">
                <div class="flex items-start justify-between mb-2">
                    <h5 class="font-semibold text-gray-900">Issue {idx + 1}</h5>
                    <div class="flex items-center">
                        <span class="px-2 py-1 rounded-full text-xs font-medium whitespace-nowrap bg-{issue_color}-100 text-{issue_color}-800">
                            {issue_badge}
                        </span>
                    </div>
                </div>
                <p class="font-medium text-gray-800 mb-1">{issue.issue}</p>
                <p class="text-sm text-gray-700 whitespace-pre-wrap mb-2">{issue.evidence}</p>
            """

            if is_correct is not None or reasoning:
                assessment_color = "green" if is_correct else "red"
                assessment_text = "Correct" if is_correct else "Incorrect"

                html += f"""
                <div class="mt-2 pt-2 border-t border-purple-200 bg-purple-50 -mx-3 px-3 py-2">
                    <div class="flex items-center mb-1">
                        <p class="text-xs font-semibold text-purple-900 mr-2">Clinician Feedback:</p>
                """

                if is_correct is not None:
                    html += f"""
                        <span class="px-2 py-1 rounded-full text-xs font-medium bg-{assessment_color}-100 text-{assessment_color}-800">
                            {assessment_text}
                        </span>
                    """

                html += """
                    </div>
                """

                if reasoning:
                    html += f"""
                    <p class="text-xs text-purple-800 whitespace-pre-wrap">{reasoning}</p>
                    """

                html += """
                </div>
                """

            html += """
            </div>
            """

        html += """
        </div>
    </div>
        """

    # Missed Issues (clinician feedback - purple theme)
    if feedback.missed_issues == "yes":
        html += f"""
    <div class="border-2 border-purple-400 rounded-lg p-4 bg-purple-50 shadow-sm mb-4">
        <h4 class="font-semibold text-purple-900 mb-2">Clinician: Missed Issues</h4>
        <div class="text-sm text-purple-800 whitespace-pre-wrap">{feedback.missed_issues_detail or "No details provided"}</div>
    </div>
        """

    # Intervention with Assessment (MedGuard output - neutral theme)
    html += f"""
    <div class="border rounded-lg p-4 bg-white shadow-sm mb-4">
        <h4 class="font-semibold text-gray-900 mb-2">MedGuard Intervention</h4>
        <div class="text-sm text-gray-700 whitespace-pre-wrap mb-3">{vignette.medguard_intervention}</div>
    """

    # Add intervention assessment (clinician feedback)
    intervention_assessment_map = {
        "yes": ("green", "Correct"),
        "partial": ("yellow", "Partial"),
        "no": ("red", "Incorrect"),
    }
    if feedback.medguard_specific_intervention in intervention_assessment_map:
        color, text = intervention_assessment_map[feedback.medguard_specific_intervention]
        html += f"""
        <div class="mt-3 pt-3 border-t border-purple-300 bg-purple-50 -mx-4 px-4 py-3">
            <div class="flex items-center mb-2">
                <span class="text-xs font-semibold text-purple-900 mr-2">Clinician Assessment:</span>
                <span class="px-2 py-1 rounded-full text-xs font-medium bg-{color}-100 text-{color}-800">
                    {text}
                </span>
            </div>
            <p class="text-xs text-purple-800 whitespace-pre-wrap">{feedback.medguard_specific_intervention_reasoning}</p>
        </div>
        """

    html += """
    </div>
    """

    # Intervention Should Be (clinician feedback - purple theme)
    html += f"""
    <div class="border-2 border-purple-400 rounded-lg p-4 bg-purple-50 shadow-sm mb-4">
        <h4 class="font-semibold text-purple-900 mb-2">Clinician: Recommended Intervention</h4>
        <div class="text-sm text-purple-800 whitespace-pre-wrap">{feedback.intervention_should_be}</div>
    </div>
    """

    # Failure Modes (clinician feedback - purple theme)
    if feedback.failure_modes:
        html += """
    <div class="border-2 border-purple-400 rounded-lg p-4 bg-purple-50 shadow-sm mb-4">
        <h4 class="font-semibold text-purple-900 mb-3">Clinician: Failure Modes</h4>
        <div class="space-y-2">
        """

        for mode in feedback.failure_modes:
            explanation = feedback.failure_mode_explanations.get(mode, "No explanation provided")
            html += f"""
            <div class="bg-white rounded p-2 border border-purple-300">
                <p class="text-sm font-semibold text-purple-900">{mode}</p>
                <p class="text-xs text-purple-800 mt-1 whitespace-pre-wrap">{explanation}</p>
            </div>
            """

        html += """
        </div>
    </div>
        """

    # Intervention Probability (MedGuard output - neutral theme)
    html += f"""
    <div class="border rounded-lg p-4 bg-white shadow-sm">
        <div class="flex items-center justify-between">
            <h4 class="font-semibold text-gray-900">MedGuard Intervention Probability</h4>
            <span class="text-2xl font-bold text-gray-700">
                {int(vignette.medguard_intervention_probability * 100)}%
            </span>
        </div>
        <p class="text-xs text-gray-600 mt-2">
            Model's confidence that an intervention is required
        </p>
    </div>
    """

    return html


def save_vignette_with_feedback_html(
    vignette: PatientVignetteWithFeedback, output_path: Path
) -> None:
    """
    Generate and save HTML file for a vignette with feedback.

    Args:
        vignette: PatientVignetteWithFeedback instance
        output_path: Path where to save the HTML file
    """
    html = generate_html_from_vignette_with_feedback(vignette)
    output_path.write_text(html, encoding="utf-8")
