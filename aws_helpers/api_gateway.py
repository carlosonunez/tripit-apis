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


def return_200(body=None, json_payload=None):
    """
    Returns 200
    """
    if body is None and json_payload is None:
        raise Exception("json_payload can't be empty.")
    if json_payload is None:
        return make_api_gateway_response(code=200, payload=body)
    return make_api_gateway_response(code=200, payload=json_payload)


def make_api_gateway_response(code, payload):
    """
    Crafts a HTTP response suitable for API gateway.
    """
    if not isinstance(payload, dict):
        raise TypeError("Payload must be a hash")
    return {"statusCode": code, "body": json.dumps(payload)}
