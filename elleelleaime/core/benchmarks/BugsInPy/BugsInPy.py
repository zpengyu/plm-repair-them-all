from pathlib import Path
from typing import Optional
from io import StringIO
from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.BugsInPy.BugsInPybug import BugsInPyBug

import subprocess
import logging
import tqdm
import re

# import os
import pandas as pd


class BugsInPy(Benchmark):
    """
    The class for representing the BugsInPy benchmark.
    """

    def __init__(self, path: Path = Path("benchmarks/BugsInPy").absolute()) -> None:
        super().__init__("BugsInPy", path)

    def get_bin(self, options: str = "") -> Optional[str]:
        return f'{Path(self.path, "framework/bin/bugsinpy-")}'

    def initialize(self) -> None:
        # TODO: Make specific asjustments for BugsInPy when needed
        """
        Initializes the BugsInPy benchmark object by collecting the list of all projects and bugs.
        """
        logging.info("Initializing BugsInPy benchmark...")

        # Get all project names
        run = subprocess.run(
            f"ls {self.path}/projects",
            shell=True,
            capture_output=True,
            check=True,
        )
        project_names = {
            project_name.decode("utf-8") for project_name in run.stdout.split()
        }
        logging.info("Found %3d projects" % len(project_names))

        # Get all bug names for all project_name
        bugs = {}
        for project_name in tqdm.tqdm(project_names):
            run = subprocess.run(
                f"ls {self.path}/projects/{project_name}/bugs",
                shell=True,
                capture_output=True,
                check=True,
            )
            bugs[project_name] = {
                int(bug_id.decode("utf-8")) for bug_id in run.stdout.split()
            }
            logging.info(
                "Found %3d bugs for project %s"
                % (len(bugs[project_name]), project_name)
            )

        # TODO: Check if/how this is doable
        # Initialize dataset
        # for project_name in project_names:
        #     # Extract failing test and trigger cause
        #     run = subprocess.run(
        #         f"{self.get_bin()} query -p {pid} -q 'tests.trigger,tests.trigger.cause'",
        #         shell=True,
        #         capture_output=True,
        #         check=True,
        #     )
        # data = run.stdout.decode("utf-8").split("\n")
        # df = pd.read_csv(StringIO(data), sep=",", names=["bid", "tests", "errors"])

        for bug_id in bugs[project_name]:
            # Extract ground truth diff
            # buggy_commit_id -- fixed_commit_id
            diff_path = f"benchmarks/BugsInPy/framework/projects/{project_name}/bugs/{bug_id}/bug_patch.txt"
            with open(diff_path, "r", encoding="ISO-8859-1") as diff_file:
                diff = diff_file.read()

            # TODO: Check if/how this is doable
            # Extract failing test cases and trigger causes
            failing_test_cases = df[df["bug_id"] == bug_id]["tests"].values[0]
            trigger_cause = df[df["bug_id"] == bug_id]["errors"].values[0]

            # In file (Figure out how file content will look like): `benchmarks/BugsInPy/projects/{project_name}/{project_name}-fail.txt`
            fail_path = f"benchmarks/BugsInPy/projects/{project_name}/{project_name}-fail.txt"
            with open(fail_path, "r", encoding="ISO-8859-1") as fail_file:
                failing_tests = fail_file.read()


            # failing_tests = {}
            # for failing_test_case in failing_test_cases.split(";"):
            #     cause = trigger_cause.split(f"{failing_test_case} --> ")[1]

            # if " --> " in cause:
            #     while " --> " in cause:
            #         cause = cause.split(" --> ")[1]
            #     for test in failing_test_case.split(";"):
            #         if test in cause:
            #             cause = cause.replace(test, "")
            # failing_tests[failing_test_case] = cause.strip()

            self.add_bug(
                BugsInPyBug(self, project_name, bug_id, diff, failing_tests=None)
            )
