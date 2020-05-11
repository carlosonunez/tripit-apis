"""
Lambda doesn't automatically recognized vendored pips, so
one needs to apply this fix to add the location of those pips into
their path.
"""

import os
import sys


def include_vendored_pips():
    """
    See module doc.

    Cribbed from:
    https://stackoverflow.com/questions/49399140/module-import-error-when-executing-a-lambda-python-function
    """
    if "LAMBDA_TASK_ROOT" in os.environ:
        sys.path.append(f"{os.environ['LAMBDA_TASK_ROOT']}/lib")

    # this will render all of your packages placed as subdirs available
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))
