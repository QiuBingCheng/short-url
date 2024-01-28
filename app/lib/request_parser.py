from app import app
import requests
import json
import logging
from collections import namedtuple

ClientInfo = namedtuple('ClientInfo', ['ip', 'port', 'user_agent', 'location'])

IPSTACK_API_KEY = app.config['IPSTACK_API_KEY']


def get_location(ip):
    """
    Retrieves the geographical location (latitude and longitude) of a given IP address using the IPStack API.

    Parameters:
        ip (str): The IP address for which the location needs to be retrieved.

    Returns:
        str: A string containing the latitude and longitude separated by commas. Returns "NA,NA" if the location retrieval fails.
    """
    default_location = "NA,NA"

    url = f'http://api.ipstack.com/{ip}?access_key={IPSTACK_API_KEY}'
    try:
        response = requests.get(url)
        identity = json.loads(response.text)
        longitude = identity['longitude']
        latitude = identity['latitude']
        location = f"{latitude:.3f},{longitude:.3f}"
        return location

    except requests.exceptions.RequestException as e:
        # Log the error or handle it as needed
        logging.error(f'Error in get_location: {e}')
        return default_location

    except json.JSONDecodeError as e:
        # Log the error or handle it as needed
        logging.error(f'Error decoding JSON in get_location: {e}')
        return default_location


def get_client_info(request):
    """
    Retrieves information from an HTTP request, including the client's IP address, port, user agent, and geographical location.

    Parameters:
        request (object): The HTTP request object containing client information.

    Returns:
        dict: A dictionary containing the following client information:
            - 'ip' (str): The client's IP address.
            - 'port' (str): The client's port number.
            - 'user_agent' (str): The user agent string indicating the client's browser and device.
            - 'location' (str): The geographical location of the client in the format "latitude,longitude". Defaults to "NA,NA" if location retrieval fails.
    """

    # Default values
    default_location = 'NA,NA'
    default_info = ClientInfo(
        ip='', port='', user_agent='', location=default_location)

    try:
        ip = (
            request.headers.get('HTTP_X_REAL_IP') or
            request.headers.get('CF-Connecting-IP') or
            request.headers.get('X-Forwarded-For', '').split(',')[0] or
            request.environ.get('REMOTE_ADDR')
        )

        port = request.environ.get('REMOTE_PORT', "")
        user_agent = request.environ.get('HTTP_USER_AGENT')
        location = get_location(ip)

        # Return client information as a namedtuple
        return ClientInfo(ip=ip, port=port, user_agent=user_agent, location=location)

    except Exception as e:
        # Log the error or handle it as needed
        logging.error(f'Error in get_client_info: {e}')
        return default_info
