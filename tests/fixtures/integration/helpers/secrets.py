"""
Integration helpers for API gateway.
"""
from os import path
from pathlib import Path
from tripit.logging import logger

SECRETS_DIRECTORY = "/secrets"


def read_secret(secret_name):
    """ Reads a secret. """
    if path.exists(_secret_path(secret_name)):
        return Path(_secret_path(secret_name)).read_text()
    logger.warning("Unable to retrieve secret during integration test: %s", secret_name)
    return None


def _secret_path(name):
    """ Builds a path to the secret """
    return "/".join([SECRETS_DIRECTORY, name])
