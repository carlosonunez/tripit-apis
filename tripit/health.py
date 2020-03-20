"""
Healthiness methods
"""
import json


def ping():
    """
    Returns 200 if everything's fine or the cloud provider will
    (hopefully) return 5xx if not.
    """
    return {'status': 'ok',
            'body': json.dumps({'message': 'sup dawg'})}
