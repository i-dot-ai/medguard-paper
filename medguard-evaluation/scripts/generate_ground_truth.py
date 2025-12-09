"""
Wrapper script for ground truth generation from clinician evaluations.

Synthesises clinician feedback into structured ground truth format for
automated scoring. Requires access to clinician evaluation data.
"""

from medguard.ground_truth.main import main

if __name__ == "__main__":
    main()
