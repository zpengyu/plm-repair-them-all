from pathlib import Path
from typing import Optional
from io import StringIO
from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.BugsInPy.BugsInPybug import BugsInPyBug

import subprocess
import logging

# import tqdm
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
        return f'{Path(self.path, "framework/bin/")}'

    def initialize(self) -> None:
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
        # for project_name in tqdm.tqdm(project_names):
        for project_name in project_names:
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

        # Initialize dataset
        for project_name in project_names:
            # Create a DataFrame to store the failing test cases and trigger causes
            df = pd.DataFrame(columns=["bid", "tests", "errors"])

            for bug_id in bugs[project_name]:
                # Extract ground truth diff
                diff_path = f"benchmarks/BugsInPy/framework/projects/{project_name}/bugs/{bug_id}/bug_patch.txt"
                with open(diff_path, "r", encoding="ISO-8859-1") as diff_file:
                    diff = diff_file.read()

                # Extract failing test cases and trigger causes
                # failing_test_cases = df[df["bug_id"] == bug_id]["tests"].values[0]
                # trigger_cause = df[df["bug_id"] == bug_id]["errors"].values[0]

                # Check with default path
                fail_path = f"/temp/projects/{project_name}/bugsinpy_fail.txt"
                with open(fail_path, "r", encoding="ISO-8859-1") as fail_file:
                    failing_tests_content = fail_file.read()

                # Use a regular expression to extract the test name and its context
                pattern = r"FAIL: ([\w_.]+ \([\w_.]+\))"
                matches = re.findall(pattern, failing_tests_content)

                # Store the results in a dictionary if needed
                failing_tests = {"failing_tests": matches}

                self.add_bug(
                    BugsInPyBug(self, project_name, bug_id, diff, failing_tests)
                )
