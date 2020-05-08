"""
These are a series of helpers that make creating messages acceptable by
the AWS API gateway a little easier.
"""
import json
from tripit.logging import logger


def get_host(event):
    """
    Get the host associated with this API gateway from an event.
    """
    try:
        return event["headers"]["Host"]
    except KeyError:
        logger.error(
            "Failed to get host from headers, %s", json.dumps(event["Headers"]),
        )
        return None


def get_endpoint(event):
    """
    Get an endpoint path from an event.
    """
    try:
        return event["requestContext"]["path"]
    except KeyError:
        logger.error(
            "Failed to get endpoint path from requestContext, %s",
            json.dumps(event["requestContext"]),
        )
        return None


def get_access_key(event):
    """
    Gets an access key from an event.
    """
    try:
        return event["requestContext"]["identity"]["apiKey"]
    except KeyError:
        logger.error("Failed to get access key from event, %s", json.dumps(event["requestContext"]))
        return None


def get_query_parameter(event, parameter):
    """
    Finds a query parameter from an event.
    """
    try:
        return event["queryStringParameters"][parameter]
    except KeyError:
        logger.error("Couldn't find parameter %s in event %s", parameter, json.dumps(event))
        return None


def return_ok(message=None, additional_json=None):
    """
    Returns HTTP 200 with a custom message and additional JSON, if desired.
    """
    payload = {"status": "ok"}
    if additional_json is not None:
        payload = {**payload, **additional_json}
    if message is not None:
        payload["message"] = message
    return return_200(payload)


def return_error(message=None, code=400):
    """
    Returns HTTP 400 Bad Request if something went wrong.
    I would normally throw HTTP 500 here but API gateway eats these.
    """
    return globals()[f"return_{code}"](message)


def return_unauthenticated(message="Access denied."):
    """
    Returns HTTP 403 if denied access to something.
    """
    return return_error(message=message, code=403)


def return_not_found(message):
    """
    Returns HTTP 404 with a custom message.
    """
    return return_error(message=message, code=404)


def return_200(body=None, json_payload=None):
    """
    Returns 200
    """
    if body is None and json_payload is None:
        raise Exception("json_payload can't be empty.")
    if json_payload is None:
        return make_api_gateway_response(code=200, payload=body)
    return make_api_gateway_response(code=200, payload=json_payload)


def return_400(message=None):
    """
    Returns 400
    """
    payload = {"status": "error", "message": message}
    return make_api_gateway_response(code=400, payload=payload)


def return_403(message=None):
    """
    Returns 403
    """
    payload = {"status": "error", "message": message}
    return make_api_gateway_response(code=403, payload=payload)


def return_404(message=None):
    """
    Returns 404
    """
    payload = {"status": "error", "message": message}
    return make_api_gateway_response(code=404, payload=payload)


def make_api_gateway_response(code, payload):
    """
    Crafts a HTTP response suitable for API gateway.
    """
    if not isinstance(payload, dict):
        raise TypeError("Payload must be a hash")
    return {"statusCode": code, "body": json.dumps(payload)}
