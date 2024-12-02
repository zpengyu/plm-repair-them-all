from generate_samples import generate_sample
from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.benchmarks.benchmark import Benchmark

import pytest
import os


class TestInstructPromptingDefects4J:
    DEFECTS4J: Benchmark
    PROMPT_STRATEGY: str = "instruct"

    @classmethod
    def setup_class(cls):
        TestInstructPromptingDefects4J.DEFECTS4J = get_benchmark("defects4j")
        assert TestInstructPromptingDefects4J.DEFECTS4J is not None
        TestInstructPromptingDefects4J.DEFECTS4J.initialize()

    def test_closure_115(self):
        bug = TestInstructPromptingDefects4J.DEFECTS4J.get_bug("Closure-115")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestInstructPromptingDefects4J.PROMPT_STRATEGY,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Closure-115"
        assert sample["prompt_strategy"] == "instruct"

        # Assert that the buggy code and fixed code are properly separated
        assert "boolean hasSideEffects = false;" in sample["buggy_code"]
        assert "boolean hasSideEffects = false;" not in sample["fixed_code"]
        assert (
            "if (hasSideEffects && NodeUtil.canBeSideEffected(cArg)) {"
            in sample["buggy_code"]
        )
        assert (
            "if (hasSideEffects && NodeUtil.canBeSideEffected(cArg)) {"
            not in sample["fixed_code"]
        )

        # Assert that the prompt is properly constructed
        assert (
            "/**\n   * Determines whether a function can be inlined at a particular call site."
            in sample["prompt"]
        )

    def test_closure_4(self):
        bug = TestInstructPromptingDefects4J.DEFECTS4J.get_bug("Closure-4")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestInstructPromptingDefects4J.PROMPT_STRATEGY,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Closure-4"
        assert sample["prompt_strategy"] == "instruct"

        # Assert that the buggy code and fixed code are properly separated
        assert "if (detectImplicitPrototypeCycle()) {" in sample["buggy_code"]
        assert "if (detectImplicitPrototypeCycle()) {" not in sample["fixed_code"]
        assert "if (detectInheritanceCycle()) {" not in sample["buggy_code"]
        assert "if (detectInheritanceCycle()) {" in sample["fixed_code"]

        # Assert that the prompt is properly constructed
        assert (
            "/**\n   * Resolve the referenced type within the enclosing scope.\n   */"
            in sample["prompt"]
        )


class TestInstructPromptingGitBugJava:
    GITBUGJAVA: Benchmark
    PROMPT_STRATEGY: str = "instruct"

    @classmethod
    def setup_class(cls):
        TestInstructPromptingGitBugJava.GITBUGJAVA = get_benchmark("gitbugjava")
        assert TestInstructPromptingGitBugJava.GITBUGJAVA is not None
        TestInstructPromptingGitBugJava.GITBUGJAVA.initialize()

    @pytest.mark.skipif(
        os.environ.get("CI") is not None,
        reason="This test requires completing GitBug-Java's setup, which is too heavy for CI.",
    )
    def test_traccar_traccar_37ed394724c0(self):
        bug = TestInstructPromptingGitBugJava.GITBUGJAVA.get_bug(
            "traccar-traccar-37ed394724c0"
        )
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestInstructPromptingGitBugJava.PROMPT_STRATEGY,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "traccar-traccar-37ed394724c0"
        assert sample["prompt_strategy"] == "instruct"

        # Assert that the prompt is properly constructed
        assert sample["prompt"] is not None

    @pytest.mark.skipif(
        os.environ.get("CI") is not None,
        reason="This test requires completing GitBug-Java's setup, which is too heavy for CI.",
    )
    def test_TheAlgorithms_Java_e5c7a08874a6(self):
        bug = TestInstructPromptingGitBugJava.GITBUGJAVA.get_bug(
            "TheAlgorithms-Java-e5c7a08874a6"
        )
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestInstructPromptingGitBugJava.PROMPT_STRATEGY,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "TheAlgorithms-Java-e5c7a08874a6"
        assert sample["prompt_strategy"] == "instruct"

        # Assert that the prompt is properly constructed
        assert sample["prompt"] is not None

    @pytest.mark.skipif(
        os.environ.get("CI") is not None,
        reason="This test requires completing GitBug-Java's setup, which is too heavy for CI.",
    )
    def test_BrightSpots_rcv_688920f27706(self):
        bug = TestInstructPromptingGitBugJava.GITBUGJAVA.get_bug(
            "BrightSpots-rcv-688920f27706"
        )
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestInstructPromptingGitBugJava.PROMPT_STRATEGY,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "BrightSpots-rcv-688920f27706"
        assert sample["prompt_strategy"] == "instruct"

        # Assert that the prompt is properly constructed
        assert sample["prompt"] is None


class TestInstructPromptingRunBugRun:
    RUNBUGRUN: Benchmark
    PROMPT_STRATEGY: str = "instruct_python"

    @classmethod
    def setup_class(cls):
        TestInstructPromptingRunBugRun.RUNBUGRUN = get_benchmark("runbugrun")
        assert TestInstructPromptingRunBugRun.RUNBUGRUN is not None
        TestInstructPromptingRunBugRun.RUNBUGRUN.initialize()

    def test_p02714_476958(self):
        bug = TestInstructPromptingRunBugRun.RUNBUGRUN.get_bug("p02714_476958")
        assert bug is not None
        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestInstructPromptingRunBugRun.PROMPT_STRATEGY,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "p02714_476958"
        assert sample["prompt_strategy"] == "instruct_python"

        # Assert that the buggy code and fixed code are properly separated
        assert "print(c)" in sample["buggy_code"]
        assert "print(c)" not in sample["fixed_code"]
        assert "for d in range(1, n//2 + 1):" in sample["fixed_code"]
        assert "for d in range(1, n//2):" in sample["buggy_code"]

        # Assert that the prompt is properly constructed
        assert """assert result == \"2356504491\"""" in sample["prompt"]

        assert """but got:""" in sample["prompt"]

    def test_p03062_876858(self):
        bug = TestInstructPromptingRunBugRun.RUNBUGRUN.get_bug("p03062_876858")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestInstructPromptingRunBugRun.PROMPT_STRATEGY,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "p03062_876858"
        assert sample["prompt_strategy"] == "instruct_python"

        # Assert that the buggy code and fixed code are properly separated
        assert "B = list(map(abs,a))" in sample["buggy_code"]
        assert "B = list(map(abs,a))" not in sample["fixed_code"]
        assert "B = list(map(abs, A))" in sample["fixed_code"]
        assert "B = list(map(abs, A))" not in sample["buggy_code"]

        # Assert that the prompt is properly constructed
        assert """assert result == \"26\"""" in sample["prompt"]
        assert """failed with error:""" in sample["prompt"]
