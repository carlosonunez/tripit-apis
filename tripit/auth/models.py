"""
These are tables used to represent relationships between access keys and various
different kinds of tokens.
"""

import os
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute
from pynamodb.exceptions import TableDoesNotExist, TransactWriteError
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

    @staticmethod
    def as_dict(access_key, **attributes):
        """
        Returns the token data mapped to this access key as a hash.
        """
        try:
            data = TripitRequestToken.get(access_key, **attributes)
            return {
                "access_key": access_key,
                "token": data.token,
                "token_secret": data.token_secret,
            }
        except TableDoesNotExist:
            logger.warning("Request token not created yet for key %s", access_key)
            return None

    @staticmethod
    def insert(access_key, token, token_secret):
        """
        Inserts a new access token.
        """
        try:
            if not TripitRequestToken.exists():
                TripitRequestToken.create_table()
            new_mapping = TripitRequestToken(access_key, token=token, token_secret=token_secret)
            new_mapping.save()
            new_mapping.refresh()
        except TransactWriteError as failed_write_error:
            logger.error("Failed to write new data for ak %s: %s", access_key, failed_write_error)

    @staticmethod
    def delete_tokens_by_access_key(access_key):
        """
        Deletes a token associated with an access key.
        """
        try:
            existing_request_token_mapping = TripitRequestToken.get(access_key)
            existing_request_token_mapping.delete()
            existing_request_token_mapping.save()
            existing_request_token_mapping.refresh()
            return None
        except TransactWriteError as failed_write_error:
            logger.error("Failed to write new data for ak %s: %s", access_key, failed_write_error)
            return None
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

    @staticmethod
    def as_dict(access_key, **attributes):
        """
        Returns the token data mapped to this access key as a hash.
        """
        try:
            data = TripitAccessToken.get(access_key, **attributes)
            return {
                "access_key": access_key,
                "token": data.token,
                "token_secret": data.token_secret,
            }
        except TableDoesNotExist:
            logger.warning("Request token not created yet for key %s", access_key)
            return None

    @staticmethod
    def insert(access_key, token, token_secret):
        """
        Inserts a new access token.
        """
        try:
            if not TripitAccessToken.exists():
                TripitAccessToken.create_table()
            new_mapping = TripitAccessToken(access_key, token=token, token_secret=token_secret)
            new_mapping.save()
            new_mapping.refresh()
        except TransactWriteError as failed_write_error:
            logger.error("Failed to write new data for ak %s: %s", access_key, failed_write_error)

    @staticmethod
    def delete_tokens_by_access_key(access_key):
        """
        Deletes a token associated with an access key.
        """
        try:
            existing_request_token_mapping = TripitAccessToken.get(access_key)
            existing_request_token_mapping.delete()
            existing_request_token_mapping.save()
            existing_request_token_mapping.refresh()
            return None
        except TransactWriteError as failed_write_error:
            logger.error("Failed to write new data for ak %s: %s", access_key, failed_write_error)
            return None
        except TableDoesNotExist:
            logger.warning("Access token not created yet for key %s", access_key)
            return None
