from app import app
import requests
import json
import os

IPSTACK_API_KEY = os.getenv("IPSTACK_API_KEY")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")


def is_admin(username, password):
    return username == USERNAME and password == PASSWORD


def get_location(ip):
    url = f"http://api.ipstack.com/{ip}?access_key={IPSTACK_API_KEY}"
    try:
        response = requests.get(url)
        identity = json.loads(response.text)
        longitude = identity["longitude"]
        latitude = identity["latitude"]
        location = f"{latitude:.3f},{longitude:.3f}"
        return location
    except:
        return "NA,NA"


def get_client_information(request):
    # ip
    if 'HTTP_X_REAL_IP' in request.environ:
        ip = request.environ.get('HTTP_X_REAL_IP')
    elif 'CF-Connecting-IP' in request.headers:
        ip = request.headers['CF-Connecting-IP']
    elif request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
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
