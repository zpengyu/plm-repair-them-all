import subprocess
import shutil
import os
from pathlib import Path
import re

from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.bug import RichBug
from elleelleaime.core.benchmarks.test_result import TestResult
from elleelleaime.core.benchmarks.compile_result import CompileResult

class RunBugRunBug(RichBug):
    """
    The class for representing RunBugRun bugs
    """
        
    def checkout(self, path: str, fixed: bool = False) -> bool:
        # Remove the directory if it exists
        shutil.rmtree(path, ignore_errors=True)
        # Make the directory
        subprocess.run(
            f"mkdir -p {path}",
            shell=True,
            capture_output=True,
            check=True,
        )

        # Checkout the bug is the same as copying the entire benchmark
        # Copy source file
        
        subfolder = 'fixed' if fixed else 'buggy'
        cmd = f"cd {self.benchmark.get_path()}; mkdir {path}/buggy; cp {subfolder}/{self.identifier}.py {path}/buggy" #FIXME
        run = subprocess.run(cmd, shell=True, capture_output=True, check=True)
        
        return run.returncode == 0

    def compile(self, path: str) -> CompileResult:
        file_path = Path(path, 'buggy', f"{self.get_identifier()}.py")
        assert file_path.exists()

        with open(file_path) as f:
            bug_code = f.read()
        assert bug_code

        try:
            compile(bug_code, file_path, 'exec')
            return CompileResult(True)
        except:
            return CompileResult(False)

    def test(self, path: str) -> TestResult:
        file_path = Path(path, 'buggy', f"{self.get_identifier()}.py")
        assert file_path.exists()

        for test_case, cause in self.failing_tests.items():
            match = re.search('Function with input:\n(.*)\nexpected to output:\n(.*)\n(?:failed|but got)', cause, re.DOTALL)
            test_input, test_output = match.group(1), match.group(2)
            error_code, result = RunBugRunBug.execute_test_case(file_path, test_input)
            
            if error_code:
                return TestResult(False)
            elif result != test_output.strip():
                return TestResult(False)

        return TestResult(True)
    
    @staticmethod
    def execute_test_case(code_path, test_input):
        if test_input.strip():
            cmd = f"""echo "{test_input}" | python {code_path}"""
        else:
            cmd = f"""python {code_path}"""
        try:
            run = subprocess.run(
                cmd, 
                shell=True,
                capture_output=True,
                check=False,
                timeout=1,
            )
        except OSError:
            return 255, "OSError: [Errno 7] Argument list too long: '/bin/sh'"
        except subprocess.TimeoutExpired:
            return 1, f"Command '{cmd}' timed out after 1 seconds"

        return run.returncode, run.stderr.decode("utf-8").strip() if run.returncode else run.stdout.decode("utf-8").strip()

    def get_src_test_dir(self, path: str) -> str:
        return path
    
