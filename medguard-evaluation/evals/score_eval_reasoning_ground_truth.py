from inspect_ai import score
from inspect_ai.log import read_eval_log, write_eval_log

from medguard.scorer.ground_truth.scorer import llm_as_a_judge


def run_eval(input: str, output: str):
    eval_log = score(
        log=read_eval_log(input),
        scorers=[llm_as_a_judge()],
        action="overwrite",
        display="rich",
    )

    write_eval_log(eval_log, output)


def main():
    run_eval(
        input="outputs/logs/2025-11-03T22-50-04+00-00_test-190-gpt-oss-20b-medium-unscored.eval",
        output="outputs/logs/2025-11-03T22-50-04+00-00_test-190-gpt-oss-20b-medium-scored.eval",
    )


if __name__ == "__main__":
    main()
