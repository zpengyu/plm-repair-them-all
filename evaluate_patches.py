from concurrent.futures import ThreadPoolExecutor, as_completed
from unidiff import PatchSet
from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.utils.jsonl import stream_jsonl, write_jsonl
from elleelleaime.evaluate.strategies.registry import PatchEvaluationStrategyRegistry

import fire
import sys
import tqdm
import logging
import json
import os
import difflib


def evaluate_candidate(bug: Bug, sample: dict, strategy: str, **kwargs) -> dict:
    """
    Evaluates the candidate patch for the given sample.
    """

    evaluation_strategy = PatchEvaluationStrategyRegistry(**kwargs).get_evaluation(
        strategy
    )
    evaluation = evaluation_strategy.evaluate(bug, sample)
    sample["evaluation"] = evaluation

    return sample


def exact_match(evaluation: dict) -> bool:
    """
    Returns True if the evaluation is an exact match.
    """
    return evaluation["exact_match"]


def plausible(evaluation: dict) -> bool:
    """
    Returns True if the evaluation is plausible.
    """
    return evaluation["compile"] and evaluation["test"]


def compilable(evaluation: dict) -> bool:
    """
    Returns True if the evaluation is compilable.
    """
    return evaluation["compile"]


def is_single_chunk(sample: dict) -> bool:
    """
    Return True if the sample's ground truth is a single chunk.
    Single chunk means that there is only one hunk in the ground truth and that the changes are all contiguous.
    """
    diff = PatchSet(sample["ground_truth"])
    # Check if there is only one hunk
    if len(diff) == 1 and len(diff[0]) == 1:
        # Check if the changes are contiguous
        hunk = diff[0][0]
        i = 0
        found_change = False
        while i < len(hunk):
            # Find a change
            if hunk[i].is_added or hunk[i].is_removed:
                if found_change:
                    return False
                found_change = True
                # Skip over the remainder of the added/removed chunk
                while i < len(hunk) and (hunk[i].is_added or hunk[i].is_removed):
                    i += 1
            # Skip over the unchanged chunk
            else:
                i += 1
        return True
    else:
        return False


def is_single_hunk(sample: dict) -> bool:
    """
    Return True if the sample's ground truth is a single hunk.
    Single hunk means that there is only one hunk in the ground truth.
    """
    diff = PatchSet(sample["ground_truth"])
    return len(diff) == 1 and len(diff[0]) == 1


def compute_statistics(samples: list) -> dict:
    """
    Computes statistics over the evaluation.
    """
    statistics = {
        "num_bugs": 0,
        "num_bugs_with_prompt": 0,
        "num_bugs_with_candidates": 0,
        "num_bugs_with_exact_match_candidates": 0,
        "num_bugs_with_plausible_candidates": 0,
        "num_bugs_with_compilable_candidates": 0,
        "num_patches": 0,
        "num_compilable_patches": 0,
        "num_plausible_patches": 0,
        "num_exact_match_patches": 0,
        "bugs_with_exact_match_candidates": [],
        "bugs_with_plausible_candidates": [],
        "bugs_with_compilable_candidates": [],
    }

    for sample in tqdm.tqdm(samples):
        statistics["num_bugs"] += 1
        if sample["prompt"] is not None:
            statistics["num_bugs_with_prompt"] += 1
        if (
            sample["generation"] is not None
            and len(sample["generation"]) > 0
            and not all(
                candidate["generation"] is None for candidate in sample["evaluation"]
            )
        ):
            statistics["num_bugs_with_candidates"] += 1
            statistics["num_patches"] += sum(
                [
                    candidate["generation"] is not None
                    for candidate in sample["evaluation"]
                ]
            )
            statistics["num_compilable_patches"] += sum(
                [compilable(candidate) for candidate in sample["evaluation"]]
            )
            statistics["num_plausible_patches"] += sum(
                [plausible(candidate) for candidate in sample["evaluation"]]
            )
            statistics["num_exact_match_patches"] += sum(
                [exact_match(candidate) for candidate in sample["evaluation"]]
            )
            if any(exact_match(candidate) for candidate in sample["evaluation"]):
                statistics["num_bugs_with_exact_match_candidates"] += 1
                statistics["bugs_with_exact_match_candidates"].append(
                    sample["identifier"]
                )
            if any(compilable(candidate) for candidate in sample["evaluation"]):
                statistics["num_bugs_with_compilable_candidates"] += 1
                statistics["bugs_with_compilable_candidates"].append(
                    sample["identifier"]
                )
            if any(plausible(candidate) for candidate in sample["evaluation"]):
                statistics["num_bugs_with_plausible_candidates"] += 1
                statistics["bugs_with_plausible_candidates"].append(
                    sample["identifier"]
                )

    return statistics


def export_patches(samples: list) -> None:
    """
    Exports the patches to text files in structured directories.
    """
    for sample in tqdm.tqdm(samples):
        if (
            sample["generation"] is not None
            and len(sample["generation"]) > 0
            and not all(
                candidate["generation"] is None for candidate in sample["evaluation"]
            )
        ):
            # Write prompt, target diff to file
            target_diff = difflib.unified_diff(
                sample["buggy_code"].splitlines(keepends=True),
                sample["fixed_code"].splitlines(keepends=True),
                n=max(len(sample["buggy_code"]), len(sample["fixed_code"])),
            )
            os.makedirs(f"patches/{sample['identifier']}", exist_ok=True)
            with open(f"patches/{sample['identifier']}/target.diff", "w") as f:
                f.writelines(target_diff)
            with open(f"patches/{sample['identifier']}/prompt.txt", "w") as f:
                f.write(sample["prompt"])

            for i, candidate in enumerate(sample["evaluation"]):
                if candidate["generation"] is not None:
                    # Compute diff between generated code and buggy code
                    diff = difflib.unified_diff(
                        sample["buggy_code"].splitlines(keepends=True),
                        candidate["generation"].splitlines(keepends=True),
                        n=max(len(sample["buggy_code"]), len(candidate["generation"])),
                    )
                    if exact_match(candidate):
                        sub_dir = "exact_match"
                    elif plausible(candidate):
                        sub_dir = "plausible"
                    elif compilable(candidate):
                        sub_dir = "compilable"
                    else:
                        sub_dir = "non_compilable"

                    os.makedirs(
                        f"patches/{sample['identifier']}/{sub_dir}", exist_ok=True
                    )
                    with open(
                        f"patches/{sample['identifier']}/{sub_dir}/{i}.diff", "w"
                    ) as f:
                        f.writelines(diff)


def entry_point(
    benchmark: str,
    samples_path: str,
    strategy: str = "replace",
    n_workers: int = 4,
    correctness: bool = True,
    **kwargs,
):
    """
    Evaluates the candidate patches given the samples,
    and writes the results to f"evaluation_{benchmark}_{prompt_strategy}_{model_name}.jsonl.gz"

    There are several modes to run this script:
        - Correctness: correctness=True (default) evaluates the candidate patches for correctness with the given strategy.
        - Statistics: statistics=True computes statistics over the evaluation.
        - Export: export=True exports the patches to text files in structured directories.
    """
    # Get the benchmark, check if it exists, and initialize it
    samples_file_name = os.path.basename(samples_path)
    prompt_strategy = samples_file_name.split("_")[2].split(".")[0]
    model_name = samples_file_name.split("_")[3].split(".")[0]
    benchmark_obj = get_benchmark(benchmark)
    if benchmark_obj is None:
        raise ValueError(f"Unknown benchmark {benchmark}")
    benchmark_obj.initialize()

    # Read the samples
    logging.info("Reading samples...")
    samples = list(stream_jsonl(samples_path))

    # Correctness evaluation
    if correctness:
        with ThreadPoolExecutor(max_workers=n_workers) as executor:
            futures = []
            for sample in tqdm.tqdm(samples):
                bug = benchmark_obj.get_bug(sample["identifier"])
                if bug is None:
                    raise ValueError(f"Unknown bug {sample['identifier']}")
                futures.append(
                    executor.submit(evaluate_candidate, bug, sample, strategy, **kwargs)
                )

            logging.info("Evaluating candidates...")
            results = []
            for future in tqdm.tqdm(as_completed(futures), total=len(futures)):
                results.append(future.result())
            samples = results

    # Compute statistics over the evaluation
    if "statistics" in kwargs and kwargs["statistics"]:
        # Compute statistics for single chunk samples
        statistics = compute_statistics(
            [sample for sample in samples if is_single_chunk(sample)]
        )
        with open(
            f"statistics_single_chunk_{benchmark}_{prompt_strategy}_{model_name}.json",
            "w",
        ) as f:
            json.dump(statistics, f, indent=4)

        # Compute statistics for single hunk samples
        statistics = compute_statistics(
            [sample for sample in samples if is_single_hunk(sample)]
        )
        with open(
            f"statistics_single_hunk_{benchmark}_{prompt_strategy}_{model_name}.json",
            "w",
        ) as f:
            json.dump(statistics, f, indent=4)

        # Compute statistics for all samples
        statistics = compute_statistics(samples)
        with open(
            f"statistics_{benchmark}_{prompt_strategy}_{model_name}.json", "w"
        ) as f:
            json.dump(statistics, f, indent=4)

    # Export patches to text files in structured directories
    if "export" in kwargs and kwargs["export"]:
        export_patches(samples)

    # Write results to jsonl file
    write_jsonl(
        f"evaluation_{benchmark}_{prompt_strategy}_{model_name}.jsonl.gz", samples
    )


def main():
    logging.getLogger().setLevel(logging.INFO)
    fire.Fire(entry_point)


if __name__ == "__main__":
    sys.exit(main())