#! /usr/bin/python3.12

#python3 -m venv python_env
#source python_env/bin/activate on Linux (or .\python_env\Scripts\activate on Windows)
#pip install -r requirements.txt

import time
import pickle
import os
import dotenv
import jsonlines
import json
import csv
from flask import Flask, render_template
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from stravalib.client import Client

dotenv.load_dotenv()  # Load environment variables from .env file

#values

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URL = 'http://localhost:8000/authorized'
PATH = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(PATH, 'activities-all.json')
client_path = os.path.join(PATH, 'client.pkl')

app = FastAPI()
app_flask = Flask(__name__)
client = Client()

def save_object(obj, filename):
    with open(filename, 'wb') as output:
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)

def load_object(filename):
    with open(filename, 'rb') as input:
        return pickle.load(input)

def check_token():
    if time.time() > client.token_expires_at:
        refresh_response = client.refresh_access_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, refresh_token=client.refresh_token)
        client.access_token = refresh_response['access_token']
        client.refresh_token = refresh_response['refresh_token']
        client.token_expires_at = refresh_response['expires_at']

@app.get("/")
def read_root():
    authorize_url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URL)
    return RedirectResponse(authorize_url)

@app.get("/authorized/")
def get_code(state=None, code=None, scope=None):
    try:
        token_response = client.exchange_code_for_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, code=code)
        client.access_token = token_response['access_token']
        client.refresh_token = token_response['refresh_token']
        client.token_expires_at = token_response['expires_at']
        save_object(client, os.path.join(PATH, 'client.pkl'))
        return {"state": state, "code": code, "scope": scope}
    except Exception as e:
        return {f'Error: {e} line {e.__traceback__.tb_lineno}'}

def get_num(num):
    return float(str(num).split()[0])

def get_activities():
    try:
        if os.path.exists(os.path.join(PATH, 'client.pkl')):
            global client
            client = load_object(os.path.join(PATH, 'client.pkl'))
        check_token()
        athlete = client.get_athlete()
        print(f"For {athlete.id}, I now have an access token {client.access_token}")

        existing_activities = set()
        if os.path.exists(json_path):
            with jsonlines.open(json_path, mode='r') as reader:
                for line in reader:
                    existing_activities.add(line['id'])

        with jsonlines.open(json_path, mode='w') as writer:
            for activity in client.get_activities():
                '''with open('test.txt', 'w') as f:
                    f.write(str(activity))
                    test = activity.end_latlng
                    print(str(test), type(test))
                break'''
                if activity.id in existing_activities:
                    print(f'Activity {activity.id} already exists, skipping.')
                    continue
                print('New activity:', activity.id)
                writer.write({
                    "id": activity.id,
                    "distance": get_num(activity.distance),
                    "moving_time": activity.moving_time.seconds,
                    "elapsed_time": activity.elapsed_time.seconds,
                    "total_elevation_gain": get_num(activity.total_elevation_gain),
                    "elev_high": activity.elev_high,
                    "elev_low": activity.elev_low,
                    "average_speed": get_num(activity.average_speed),
                    "max_speed": get_num(activity.max_speed),
                    "average_heartrate": activity.average_heartrate,
                    "max_heartrate": activity.max_heartrate,
                    "start_date": str(activity.start_date),
                    "name": activity.name,
                    "calories": activity.calories,
                    "polyline": activity.map.summary_polyline,
                })
                #
        print(f'Activities saved in {json_path} at {time.ctime()} on {time.strftime("%d/%m/%Y")}')
    except FileNotFoundError as e:
        print("No access token stored yet, run `uvicorn authenticate:app --reload` and visit http://localhost:8000/ to get it")
        print("After visiting that URL, a pickle file is stored. Run this file again to download your activities.")
        print()
    except Exception as e:
        print(f'Error: {e} line {e.__traceback__.tb_lineno}')

def get_data():
    polylines = []
    dates = []
    data = []
    try:
        with jsonlines.open(json_path, mode='r') as reader:
            for line in reader:
                date = line['start_date']
                polyline = line['polyline']
                polylines.append(polyline)  
                dates.append(date)
                data.append(line)
        return polylines, dates, data
    except FileNotFoundError:
        return "No activities found."
    except Exception as e:
        return str(f'Error: {e} line {e.__traceback__.tb_lineno}')
    

@app_flask.route('/activities')
def activities():
    json_path = os.path.join(PATH, 'activities-all.json')
    try:
        with open(json_path, 'r') as file:
            data = file.read()
        return render_template('activities.html', data=data)
    except FileNotFoundError:
        return "No activities found."
    except Exception as e:
        return str(f'Error: {e} line {e.__traceback__.tb_lineno}')

@app_flask.route('/')
def my_runs():
    runs, dates, data = get_data()
    return render_template('leaflet.html', runs=runs, dates=dates, activities=data)
    
@app_flask.route('/refresh', methods=['GET'])
def refresh_activities():
    get_activities()
    return render_template('refresh.html')

if __name__ == '__main__':
    app_flask.run(port=8000, debug=True)
    