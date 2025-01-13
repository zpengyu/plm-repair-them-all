from typing import Optional, Tuple, List
from unidiff import PatchSet
from uuid import uuid4
from pathlib import Path
import logging
import getpass, tempfile, difflib, shutil
import subprocess
import re
import ast

from elleelleaime.core.benchmarks.bug import Bug, RichBug


def extract_functions(source_code):
    # Parse the source code into an AST
    tree = ast.parse(source_code)

    # Extract all function definitions
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]

    # Convert the function nodes back to source code
    function_sources = [ast.get_source_segment(source_code, func) for func in functions]

    return function_sources


def extract_single_function(bug: Bug) -> Optional[Tuple[str, str]]:
    """
    Extracts the buggy and fixed code of single-function bugs.
    Returns None is bug is not single-function

    Args:
        bug (Bug): THe bug to extract the code from

    Returns:
        Optional[Tuple[str, str]]: None if the bug is not single-function, otherwise a tuple of the form (buggy_code, fixed_code)
    """
    buggy_path = Path(
        tempfile.gettempdir(),
        f"elleelleaime-{getpass.getuser()}",
        bug.get_identifier(),
        str(uuid4()),
    )
    fixed_path = Path(
        tempfile.gettempdir(),
        f"elleelleaime-{getpass.getuser()}",
        bug.get_identifier(),
        str(uuid4()),
    )

    try:
        # Checkout the buggy and fixed versions of the bug
        bug.checkout(str(buggy_path), fixed=False)
        bug.checkout(str(fixed_path), fixed=True)
        # FIXME
        with open(Path(buggy_path, "buggy", f"{bug.get_identifier()}.py")) as f:
            buggy_code = f.read()
        # FIXME
        with open(Path(fixed_path, "buggy", f"{bug.get_identifier()}.py")) as f:
            fixed_code = f.read()

        buggy_functions = extract_functions(buggy_code)
        fixed_functions = extract_functions(fixed_code)

        assert len(buggy_functions) == len(fixed_functions)

        # if len(buggy_functions) == len(fixed_functions) == 1:
        #     return buggy_functions[0], fixed_functions[0]

        # most of run bug run are straight through scripts, not functions
        return buggy_code, fixed_code

    finally:
        # Remove the checked-out bugs
        shutil.rmtree(buggy_path, ignore_errors=True)
        shutil.rmtree(fixed_path, ignore_errors=True)
