from app import app
import requests
import json
import logging

IPSTACK_API_KEY = app.config["IPSTACK_API_KEY"]
USERNAME = app.config["USERNAME"]
PASSWORD = app.config["PASSWORD"]


def is_admin(username, password):
    return username == USERNAME and password == PASSWORD


def get_location(ip):
    # get Latitude and longitude separated by commas
    default_location = "NA,NA"

    url = f"http://api.ipstack.com/{ip}?access_key={IPSTACK_API_KEY}"
    try:
        response = requests.get(url)
        identity = json.loads(response.text)
        longitude = identity["longitude"]
        latitude = identity["latitude"]
        location = f"{latitude:.3f},{longitude:.3f}"
        return location
    except requests.exceptions.RequestException as e:
        # Log the error or handle it as needed
        logging.error(f"Error in get_location: {e}")
        return default_location
    except json.JSONDecodeError as e:
        # Log the error or handle it as needed
        logging.error(f"Error decoding JSON in get_location: {e}")
        return default_location


def get_client_information(request):
    # get information from request

    # ip
    if 'HTTP_X_REAL_IP' in request.environ:
        ip = request.environ.get('HTTP_X_REAL_IP')
    elif 'CF-Connecting-IP' in request.headers:
        ip = request.headers['CF-Connecting-IP']
    elif 'X-Forwarded-For' in request.headers:
        ip = request.headers['X-Forwarded-For'].split(',')[0]
    else:
        ip = request.environ.get('REMOTE_ADDR')

    # port
    port = request.environ.get('REMOTE_PORT')

    # user_agent
    user_agent = request.environ.get('HTTP_USER_AGENT')

    # get location
    location = get_location(ip)

    info = {"ip": ip, "port": port, "user_agent": user_agent,
            "location": location
            }
    return info
