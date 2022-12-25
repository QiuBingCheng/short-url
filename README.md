# Url Shortener

## Introduction

![Index](images/index.png)

![Trace](images/trace.png)

![Admin](images/admin.png)

## Setting up a development environment
```
Create the 'env' virtual environment and activate
python -m virtualenv env
env\Scripts\activate

# Install required Python packages
pip install -r requirements.txt
```

## Initializing the Database
```
# Create DB tables
python manage.py init_db
```

## Running the app
```
# Start the Flask development web server
python manage.py runserver
```
