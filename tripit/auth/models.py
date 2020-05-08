"""
These are tables used to represent relationships between access keys and various
different kinds of tokens.
"""

import os
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute
from pynamodb.exceptions import TableDoesNotExist
from tripit.logging import logger


# pylint: disable=too-few-public-methods
class TripitRequestToken(Model):
    """
    This table is used to map access keys to request tokens/token secrets.
    """

    class Meta:
        """ Table configuration. """

        table_name = "tripit_request_tokens"
        read_capacity_units = os.environ.get("AWS_DYNAMODB_RCU") or 2
        write_capacity_units = os.environ.get("AWS_DYNAMODB_WCU") or 2
        if os.environ.get("AWS_REGION"):
            region = os.environ.get("AWS_REGION")
        if os.environ.get("AWS_DYNAMODB_ENDPOINT_URL"):
            host = os.environ.get("AWS_DYNAMODB_ENDPOINT_URL")

    access_key = UnicodeAttribute(hash_key=True)
    token = UnicodeAttribute()
    token_secret = UnicodeAttribute()

    def as_dict(self, access_key, **attributes):
        """
        Returns the token data mapped to this access key as a hash.
        """
        try:
            data = self.get(access_key, **attributes)
            return {
                "access_key": access_key,
                "token": data.token,
                "token_secret": data.token_secret,
            }
        except TableDoesNotExist:
            logger.warning("Request token not created yet for key %s", access_key)
            return None


# pylint: disable=too-few-public-methods
class TripitAccessToken(Model):
    """
    This table is used to map access keys to access tokens.
    """

    class Meta:
        """ Table configuration. """

        table_name = "tripit_access_tokens"
        read_capacity_units = os.environ.get("AWS_DYNAMODB_RCU") or 2
        write_capacity_units = os.environ.get("AWS_DYNAMODB_WCU") or 2
        if os.environ.get("AWS_REGION"):
            region = os.environ.get("AWS_REGION")
        if os.environ.get("AWS_DYNAMODB_ENDPOINT_URL"):
            host = os.environ.get("AWS_DYNAMODB_ENDPOINT_URL")

    access_key = UnicodeAttribute(hash_key=True)
    token = UnicodeAttribute()
    token_secret = UnicodeAttribute()

    def as_dict(self, access_key, **attributes):
        """
        Returns the token data mapped to this access key as a hash.
        """
        try:
            data = self.get(access_key, **attributes)
            return {
                "access_key": access_key,
                "token": data.token,
                "token_secret": data.token_secret,
            }
        except TableDoesNotExist:
            logger.warning("Request token not created yet for key %s", access_key)
            return None
