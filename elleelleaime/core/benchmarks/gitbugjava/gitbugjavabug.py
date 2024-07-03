import subprocess
import backoff
import shutil
import re
import os
from elleelleaime.core.benchmarks.benchmark import Benchmark

from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.benchmarks.test_result import TestResult
from elleelleaime.core.benchmarks.compile_result import CompileResult


class GitBugJavaBug(Bug):
    """
    The class for representing GitBug-Java bugs
    """

    def __init__(self, benchmark: Benchmark, bid: str, ground_truth: str) -> None:
        self.bid = bid
        super().__init__(benchmark, bid, ground_truth)

    @backoff.on_exception(
        backoff.constant, subprocess.CalledProcessError, interval=1, max_tries=3
    )
    def checkout(self, path: str, fixed: bool = False) -> bool:
        # Remove the directory if it exists
        shutil.rmtree(path, ignore_errors=True)

        # Checkout the bug
        checkout_run = subprocess.run(
            f"{self.benchmark.get_bin()} checkout {self.bid} {path} {'--fixed' if fixed else ''}",
            shell=True,
            capture_output=True,
            check=True,
        )

        return checkout_run.returncode == 0

    def compile(self, path: str) -> CompileResult:
        raise NotImplementedError(
            "GitBug-Java does not support compilation of bugs, only execution of the entire test pipeline."
        )

    def test(self, path: str) -> TestResult:
        try:
            env = os.environ.copy()
            env[
                "PATH"
            ] = f"{self.benchmark.path}:{self.benchmark.path}/bin:{env['PATH']}"
            run = subprocess.run(
                f"{self.benchmark.get_bin()} run {path}",
                shell=True,
                capture_output=True,
                timeout=30 * 60,
                env=env,
            )
            print(run.stdout.decode("utf-8"))

            m = re.search(r"Failing tests: ([0-9]+)", run.stdout.decode("utf-8"))
            return TestResult(
                run.returncode == 0 and m != None and int(m.group(1)) == 0
            )
        except subprocess.TimeoutExpired:
            return TestResult(False)