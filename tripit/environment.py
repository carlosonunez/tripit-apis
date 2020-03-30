"""
Useful functions for verifying environments.
"""
import os


class EnvironmentCheck:  # pylint: disable=too-few-public-methods
    """
    Class for ensuring that an environment has been properly initialized.
    Disabling this because this class doesn't yet have multiple methods, but
    I am anticipating that it will, and I don't want to rewrite environment
    var checking code in multiple modules.
    """

    def __init__(self, vars_to_check):
        self.ready = False
        self.missing_vars = []
        self.__check_environment(vars_to_check)

    def check_environment(self, vars_to_check):
        """
        Verifies that all env vars are defined
        """
        self.missing_vars = [var for var in vars_to_check if os.environ.get(var) is None]
        self.ready = self.missing_vars == []

    __check_environment = check_environment
