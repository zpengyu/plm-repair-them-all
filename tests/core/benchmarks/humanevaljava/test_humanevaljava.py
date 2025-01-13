from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.benchmarks.bug import Bug

from pathlib import Path
import uuid
import shutil
import tqdm
import pytest
import getpass, tempfile
import concurrent.futures


class TestHumanEvalJava:
    def test_get_benchmark(self):
        humanevaljava = get_benchmark("humanevaljava")
        assert humanevaljava is not None
        humanevaljava.initialize()

        bugs = humanevaljava.get_bugs()

        assert bugs is not None
        assert len(bugs) == 163
        assert len(set([bug.get_identifier() for bug in bugs])) == 163

    def checkout_bug(self, bug: Bug) -> bool:
        buggy_path = f"{tempfile.gettempdir()}/elleelleaime-{getpass.getuser()}/{bug.get_identifier()}-buggy-{uuid.uuid4()}"
        fixed_path = f"{tempfile.gettempdir()}/elleelleaime-{getpass.getuser()}/{bug.get_identifier()}-fixed-{uuid.uuid4()}"

        try:
            # Checkout buggy version
            bug.checkout(buggy_path, fixed=False)
            # Checkout fixed version
            bug.checkout(fixed_path, fixed=True)

            # Assert that there are files in the directories
            if len(list(Path(buggy_path).glob("**/*"))) == 0:
                return False
            if len(list(Path(fixed_path).glob("**/*"))) == 0:
                return False

            # Assert that we can reach the java file
            if not Path(
                buggy_path,
                "src",
                "main",
                "java",
                "humaneval",
                "buggy",
                f"{bug.get_identifier()}.java",
            ).exists():
                return False
            if not Path(
                fixed_path,
                "src",
                "main",
                "java",
                "humaneval",
                "buggy",
                f"{bug.get_identifier()}.java",
            ).exists():
                return False

            return True
        finally:
            shutil.rmtree(buggy_path, ignore_errors=True)
            shutil.rmtree(fixed_path, ignore_errors=True)

    def test_checkout_bugs(self):
        humanevaljava = get_benchmark("humanevaljava")
        assert humanevaljava is not None
        humanevaljava.initialize()

        # Run only the first 3 bugs to not take too long
        bugs = humanevaljava.get_bugs()[:3]
        assert bugs is not None

        for bug in bugs:
            assert self.checkout_bug(bug), f"Failed checkout for {bug.get_identifier()}"

    @pytest.mark.skip(reason="This test is too slow to run on CI.")
    def test_checkout_all_bugs(self):
        humanevaljava = get_benchmark("humanevaljava")
        assert humanevaljava is not None
        humanevaljava.initialize()

        bugs = humanevaljava.get_bugs()
        assert bugs is not None

        for bug in bugs:
            assert self.checkout_bug(bug), f"Failed checkout for {bug.get_identifier()}"

    def run_bug(self, bug: Bug) -> bool:
        buggy_path = f"{tempfile.gettempdir()}/elleelleaime-{getpass.getuser()}/{bug.get_identifier()}-buggy-{uuid.uuid4()}"
        fixed_path = f"{tempfile.gettempdir()}/elleelleaime-{getpass.getuser()}/{bug.get_identifier()}-fixed-{uuid.uuid4()}"

        try:
            # Checkout buggy version
            bug.checkout(buggy_path, fixed=False)
            # Checkout fixed version
            bug.checkout(fixed_path, fixed=True)

            # Compile buggy version
            compile_result = bug.compile(buggy_path)
            if not compile_result.is_passing():
                return False

            # Test buggy version
            test_result = bug.test(buggy_path)
            if test_result.is_passing():
                return False

            # Compile fixed version
            compile_result = bug.compile(fixed_path)
            if not compile_result.is_passing():
                return False

            # Test fixed version
            test_result = bug.test(fixed_path)
            if not test_result.is_passing():
                return False

            return True
        finally:
            shutil.rmtree(buggy_path, ignore_errors=True)
            shutil.rmtree(fixed_path, ignore_errors=True)

    def test_run_bugs(self):
        humanevaljava = get_benchmark("humanevaljava")
        assert humanevaljava is not None
        humanevaljava.initialize()

        bugs = humanevaljava.get_bugs()
        assert bugs is not None

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            futures_to_bugs = {}
            for bug in bugs[:3]:  # Only run the first 3 bugs
                # Submit the bug to be tested as a separate task
                futures.append(executor.submit(self.run_bug, bug))
                futures_to_bugs[futures[-1]] = bug
            # Wait for all tasks to complete
            for future in tqdm.tqdm(concurrent.futures.as_completed(futures)):
                result = future.result()
                assert (
                    result
                ), f"Failed run for {futures_to_bugs[future].get_identifier()}"

    @pytest.mark.skip(reason="This test is too slow to run on CI.")
    def test_run_all_bugs(self):
        humanevaljava = get_benchmark("humanevaljava")
        assert humanevaljava is not None
        humanevaljava.initialize()

        bugs = humanevaljava.get_bugs()
        assert bugs is not None

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            futures_to_bugs = {}
            for bug in bugs:
                # Submit the bug to be tested as a separate task
                futures.append(executor.submit(self.run_bug, bug))
                futures_to_bugs[futures[-1]] = bug
            # Wait for all tasks to complete
            for future in tqdm.tqdm(concurrent.futures.as_completed(futures)):
                result = future.result()
                assert (
                    result
                ), f"Failed run for {futures_to_bugs[future].get_identifier()}"
