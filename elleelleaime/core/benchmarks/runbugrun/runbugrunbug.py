import subprocess
import shutil
import os
from elleelleaime.core.benchmarks.benchmark import Benchmark

from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.benchmarks.test_result import TestResult
from elleelleaime.core.benchmarks.compile_result import CompileResult

class RunBugRunBug(Bug):
    """
    The class for representing RunBugRun bugs
    """

    def __init__(self, benchmark: Benchmark, bid: str, ground_truth: str) -> None:
        super().__init__(benchmark, bid, ground_truth, True)
        
    def checkout(self, path: str, fixed: bool = False) -> bool:
        pass

    def compile(self, path: str) -> CompileResult:
        pass

    def test(self, path: str) -> TestResult:
        pass