from pathlib import Path
from unidiff import PatchSet
from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.runbugrun.runbugrunbug import RunBugRunBug

import subprocess
import logging

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
        # test_path = Path(self.get_path(), 'tests_all.jsonl')
        
        python_df = pd.read_json(python_path, lines=True).set_index('problem_id')
        
        for prob_id, (buggy_submission_id, buggy_code, fixed_submission_id, fixed_code) \
        in python_df.drop_duplicates(subset=['buggy_submission_id'])[
            ['buggy_submission_id','buggy_code', 'fixed_submission_id', 'fixed_code']
        ].iterrows():
            
            buggy_file = Path(self.path, f'{prob_id}_{buggy_submission_id}.py')
            fixed_file = Path(self.path, f'{prob_id}_{fixed_submission_id}.py')

            run = subprocess.run(
                f"""cd {self.get_path()} && 
                echo '''{buggy_code}''' > {buggy_file} && 
                echo '''{fixed_code}''' > {fixed_file} && 
                diff --unified {fixed_file.relative_to(self.path)} {buggy_file.relative_to(self.path)}""",
                shell=True,
                capture_output=True
            )
            if run.returncode:
                print (run)

            diff = PatchSet(run.stdout.decode("utf-8"))
            # Change the source file path to point to the buggy version
            diff[0].source_file = f"{buggy_file.relative_to(self.path)}"
    
            self.add_bug(RunBugRunBug(self, f"{prob_id}_{buggy_submission_id}", str(diff)))
        