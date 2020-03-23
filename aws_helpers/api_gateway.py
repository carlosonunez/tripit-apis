"""
These are a series of helpers that make creating messages acceptable by
the AWS API gateway a little easier.
"""
import json


def return_ok(message=None, additional_json=None):
    """
    Returns HTTP 200 with a custom message and additional JSON, if desired.
    """
    if message is None and additional_json is None:
        return return_200(json_payload={"status": "ok"})
    if message is None:
        return return_200(json_payload={**{"status": "ok"}, **additional_json})
    if additional_json is None:
        return return_200(json_payload={"status": "ok", "message": message})
    return return_200(json_payload={**{"status": "ok", "message": message},
                                    **additional_json})


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


def make_api_gateway_response(code, payload):
    """
    Crafts a HTTP response suitable for API gateway.
    """
    if not isinstance(payload, dict):
        raise TypeError("Payload must be a hash")
    return {"statusCode": code, "body": json.dumps(payload)}
