import subprocess
import shutil
import re
import os

from elleelleaime.core.benchmarks.benchmark import Benchmark

# TODO: Implement as `RichBug` later on
from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.benchmarks.test_result import TestResult
from elleelleaime.core.benchmarks.compile_result import CompileResult


class BugsInPyBug(Bug):
    """
    The class for representing BugsInPy bugs
    """

    def __init__(
        self,
        benchmark: Benchmark,
        project_name: str,
        bug_id: str,
        version_id: str,
        ground_truth: str,
        failing_tests: dict[str, str],
    ) -> None:
        self.project_name = project_name
        self.bug_id = bug_id
        self.version_id = version_id
        super().__init__(
            benchmark,
            f"{project_name}-{bug_id}-{version_id}",
            ground_truth,
            failing_tests,
            ground_truth_inverted=True,
        )

    def checkout(self, path: str, fixed: bool = False) -> bool:
        # Remove the directory if it exists
        shutil.rmtree(path, ignore_errors=True)

        # Checkout the bug
        checkout_run = subprocess.run(
            f"{self.benchmark.get_bin()}bugsinpy-checkout -p {self.project_name} -v {self.version_id} -i {self.bug_id} -w {path}",
            shell=True,
            capture_output=True,
            check=True,
        )

        # Convert line endings to unix
        dos2unix_run = subprocess.run(
            f"find {path} -type f -print0 | xargs -0 -n 1 -P 4 dos2unix",
            shell=True,
            capture_output=True,
            check=True,
        )

        return checkout_run.returncode == 0 and dos2unix_run.returncode == 0

    def compile(self, path: str) -> CompileResult:
        run = subprocess.run(
            f"cd {path} && timeout {5*60} {self.benchmark.get_bin()}bugsinpy-compile",
            shell=True,
            capture_output=True,
            check=True,
        )
        return CompileResult(run.returncode == 0, run.stdout, run.stderr)

    def test(self, path: str) -> TestResult:
        # First run only relevant tests
        run = subprocess.run(
            f"cd {path} && timeout {30*60} {self.benchmark.get_bin()}bugsinpy-test",
            shell=True,
            capture_output=True,
            check=False,
        )

        pattern = r"FAIL: ([\w_.]+ \([\w_.]+\))"
        m = re.findall(pattern, run.stdout.decode("utf-8"))

        if not (run.returncode == 0 and m != None and int(m.group(1)) == 0):
            return TestResult(False)
        return TestResult(run.returncode == 0 and m != None and int(m.group(1)) == 0)

    # TODO: Implement later
    # def get_src_test_dir(self, path: str) -> str:
    #     run = subprocess.run(
    #         f"cd {path} && {self.benchmark.get_bin()} export -p dir.src.tests",
    #         shell=True,
    #         capture_output=True,
    #         check=True,
    #     )

    #     return run.stdout.decode("utf-8").strip()
