from pathlib import Path
from unidiff import PatchSet
from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.runbugrun.runbugrunbug import RunBugRunBug

import subprocess
import logging
from tqdm import tqdm
import pandas as pd

class RunBugRun(Benchmark):
    """
    The class for representing the RunBugRun benchmark.
    """

    def __init__(
        self, path: Path = Path("benchmarks/run_bug_run").absolute()
    ) -> None:
        super().__init__("runbugrun", path)
        
    def initialize(self) -> None:
        """
        Initializes the RunBugRun benchmark object by collecting all the bugs.
        """
        logging.info("Initializing RunBugRun benchmark...")
        
        python_path = Path(self.get_path(), 'python_valid0.jsonl')
        test_path = Path(self.get_path(), 'tests_all.jsonl')
        
        python_df = pd.read_json(python_path, lines=True).set_index('problem_id')
        test_df = pd.read_json(test_path, lines=True).set_index('id')

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

        buggy_submissions = python_df.drop_duplicates(subset=['buggy_submission_id']).head(10)

        for prob_id, (buggy_submission_id, buggy_code, fixed_submission_id, fixed_code) \
        in tqdm(
            buggy_submissions[['buggy_submission_id','buggy_code', 'fixed_submission_id', 'fixed_code']].iterrows(), 
            total=len(buggy_submissions)
        ):

            buggy_file = Path(self.path, 'buggy',  f'{prob_id}_{buggy_submission_id}.py')
            fixed_file = Path(self.path, 'fixed', f'{prob_id}_{buggy_submission_id}.py') # using buggy id for both to maintain file correspondence

            with open(buggy_file, 'w') as f:
                f.write(buggy_code)
                f.write('\n')

            with open(fixed_file, 'w') as f:
                f.write(fixed_code)
                f.write('\n')

            run = subprocess.run(
                f"""cd {self.get_path()} && 
                diff --unified {fixed_file.relative_to(self.path)} {buggy_file.relative_to(self.path)}""",
                shell=True,
                capture_output=True
            )

            diff = PatchSet(run.stdout.decode("utf-8"))
            # Change the source file path to point to the buggy version
            diff[0].source_file = f"{buggy_file.relative_to(self.path)}"

            failing_tests = {}

            for test_id, (test_input, test_output) in test_df[test_df.problem_id == prob_id][['input', 'output']].iterrows():
                error_code, result = RunBugRunBug.execute_test_case(buggy_file, test_input)

                if error_code:
                    cause = f"""Function with input {test_input.replace('"', "'")} failed with error: {result}""" 
                elif result != test_output.strip():
                    cause = f"""Expected function with input {test_input.replace('"', "'")} to output {test_output.replace('"', "'").replace("'", r"\'")} but got {result}"""
                else:
                    continue # skip passing   
                
                failing_tests[f"""{test_input} -> {test_output}"""] = cause
    
            self.add_bug(RunBugRunBug(self, f"{prob_id}_{buggy_submission_id}", str(diff), failing_tests))
        