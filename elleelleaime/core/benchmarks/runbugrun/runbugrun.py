from pathlib import Path
from unidiff import PatchSet
from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.runbugrun.runbugrunbug import RunBugRunBug

import os
import json
import subprocess
import logging
from tqdm import tqdm
import pandas as pd
import concurrent.futures


class RunBugRun(Benchmark):
    """
    The class for representing the RunBugRun benchmark.
    """

    def __init__(self, path: Path = Path("benchmarks/run_bug_run").absolute()) -> None:
        super().__init__("runbugrun", path)

    def initialize(self) -> None:
        """
        Initializes the RunBugRun benchmark object by collecting all the bugs.
        """
        logging.info("Initializing RunBugRun benchmark...")

        python_path = Path(self.get_path(), "python_valid0.jsonl")
        test_path = Path(self.get_path(), "tests_all.jsonl")

        python_df = pd.read_json(open(python_path), lines=True).set_index("problem_id")
        test_df = pd.read_json(open(test_path), lines=True).set_index("id")

        subprocess.run(
            f"mkdir -p {self.path}/buggy",
            shell=True,
            capture_output=True,
            check=True,
        )

        subprocess.run(
            f"mkdir -p {self.path}/fixed",
            shell=True,
            capture_output=True,
            check=True,
        )

        buggy_submissions = python_df.drop_duplicates(
            subset=["buggy_submission_id"]
        )  # .head(105)
        pbar = tqdm(
            buggy_submissions[
                [
                    "buggy_submission_id",
                    "buggy_code",
                    "fixed_submission_id",
                    "fixed_code",
                    "errors",
                ]
            ].iterrows(),
            total=len(buggy_submissions),
        )

        for prob_id, (
            buggy_submission_id,
            buggy_code,
            fixed_submission_id,
            fixed_code,
            errors,
        ) in pbar:
            buggy_file = Path(self.path, "buggy", f"{prob_id}_{buggy_submission_id}.py")
            fixed_file = Path(
                self.path, "fixed", f"{prob_id}_{buggy_submission_id}.py"
            )  # using buggy id for both to maintain file correspondence

            pbar.set_postfix({"file": buggy_file})
            pbar.update()

            with open(buggy_file, "w") as f:
                f.write(buggy_code)
                f.write("\n")

            with open(fixed_file, "w") as f:
                f.write(fixed_code)
                f.write("\n")

            run = subprocess.run(
                f"""cd {self.get_path()} && 
                diff --unified {fixed_file.relative_to(self.path)} {buggy_file.relative_to(self.path)}""",
                shell=True,
                capture_output=True,
            )

            diff = PatchSet(run.stdout.decode("utf-8"))
            # Change the source file path to point to the buggy version
            diff[0].source_file = f"{buggy_file.relative_to(self.path)}"

            test_rows = test_df[test_df.problem_id == prob_id][["input", "output"]]
            failing_tests = self.get_failing_tests(buggy_file, errors, test_rows)
            if failing_tests:
                self.add_bug(
                    RunBugRunBug(
                        self,
                        f"{prob_id}_{buggy_submission_id}",
                        str(diff),
                        failing_tests,
                    )
                )

    def get_failing_tests(self, buggy_file, errors, test_rows):
        failing_tests = {}
        test_results = []

        results_path = Path(self.get_path(), buggy_file.with_suffix(".jsonl"))
        already_cached = os.path.exists(results_path)
        if already_cached:
            test_results = pd.read_json(open(results_path), lines=True).set_index("id")

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            futures_to_tests = {}

            for test_id, (test_input, test_output) in test_rows.iterrows():
                test_input = test_input.strip()
                test_output = test_output.strip()

                if isinstance(errors, list):
                    result = errors[0]["exception"] + "\n" + errors[0]["output"]
                    cause = f"""Function with input:\n{test_input}\nexpected to output:\n{test_output}\nfailed with error:\n{result.strip()}"""
                    failing_tests[f"""test_{test_id}"""] = cause
                elif (
                    not already_cached
                ):  # if there isn't a runtime exception, need to execute to get the cause of test failure
                    # TODO: checkout first?
                    futures.append(
                        executor.submit(
                            RunBugRunBug.execute_test_case, buggy_file, test_input
                        )
                    )
                    futures_to_tests[futures[-1]] = (
                        test_input.strip(),
                        test_output.strip(),
                    )
                else:
                    pass

            if not already_cached:
                for future in concurrent.futures.as_completed(futures):
                    returncode, result = future.result()
                    test_input, test_output = futures_to_tests[future]
                    if returncode:
                        cause = f"""Function with input:\n{test_input}\nexpected to output:\n{test_output}\nfailed with error:\n{result.strip()}"""
                        failing_tests[f"""test_{test_id}"""] = cause
                    elif result != test_output:
                        cause = f"""Function with input:\n{test_input}\nexpected to output:\n{test_output}\nbut got:\n{result}"""
                        failing_tests[f"""test_{test_id}"""] = cause
                    else:
                        pass
                    test_results.append(
                        {
                            "id": test_id,
                            "input": test_input,
                            "output": test_output,
                            "returncode": returncode,
                            "result": result,
                        }
                    )

                if test_results:
                    pd.DataFrame(test_results).to_json(
                        results_path, orient="records", lines=True
                    )

            else:
                for test_id, (
                    test_input,
                    test_output,
                    returncode,
                    result,
                ) in test_results.iterrows():
                    if returncode:
                        cause = f"""Function with input:\n{test_input}\nexpected to output:\n{test_output}\nfailed with error:\n{result.strip()}"""
                        failing_tests[f"""test_{test_id}"""] = cause
                    elif result != test_output:
                        cause = f"""Function with input:\n{test_input}\nexpected to output:\n{test_output}\nbut got:\n{result}"""
                        failing_tests[f"""test_{test_id}"""] = cause
                    else:
                        continue

        return failing_tests
