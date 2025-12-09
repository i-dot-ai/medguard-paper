from pathlib import Path

from inspect_ai.log import EvalLog, EvalSample, read_eval_log, write_eval_log


def sanitise_eval_sample(sample: EvalSample) -> EvalSample:
    # We remove the input, messages, events, and output choices fields because this removes the internal reasoning trace which could contain further patient information.
    # We keep the MedGuard response

    sample.input = ""
    sample.messages = []
    sample.events = []
    sample.output.choices = []

    return sample


def sanitise_eval_log(log: EvalLog) -> EvalLog:
    # We only need to sanatise the individual EvalLogs

    log.samples = [sanitise_eval_sample(sample) for sample in log.samples]

    return log


def run_sanitise_eval_log(input_path: Path, output_path: Path):
    # Load the eval log
    log = read_eval_log(input_path)

    # Sanitise it
    sanitised_log = sanitise_eval_log(log)

    # Save it
    write_eval_log(sanitised_log, output_path)
