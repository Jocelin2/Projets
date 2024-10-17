# We start to activate the virtual environment : source acd_env/bin/activate (Linux) / .\acd_env\Scripts\activate (Windows)
# We start the server : python run.py

from flask import render_template
from __init__ import app
import requests
import re
import csv

# recupération des températures de la base de données

# url = 'http://10.59.65.210/temperatures.csv'

def get_temperature():
    """response = requests.get(url)
    # On vérifie que la requête a fonctionné
    if response.status_code == 200:
        print('Requête effectuée avec succès')
    else:
        print('Erreur', response.status_code)
    # On eleve les retours à la ligne, les espaces et les tabulations du contenu de la requête
    data = response.text.replace('\n', '').replace(' ', '').replace('\t', '')
    # On enregistre le contenu de la requête dans un fichier
    with open('./temperatures.csv', 'w') as file:
        file.write(data)"""
    # On lit le fichier csv
    with open('./temperatures.csv', 'r') as file:
        reader = csv.reader(file)
        temp= []
        date_list= []
        heure_list= []
        for row in reader:
            date = r'(\d{2}\/\d{2}\/\d{4})'
            heure = r'(\d{2}:\d{2})\;'
            temperature = r'(\;)(\-*\d{2}\.*\d*)'
            temp.append(float(re.search(temperature, row[0]).group(2)))
            date_list.append(f"{re.search(date, row[0]).group()}")
            heure_list.append(f"{re.search(heure, row[0]).group(1)}")
        temperature = r'(\;)(\-*\d{2}\.*\d*)'
        actually = f'{re.search(temperature, row[0]).group(2)}°C'

    return temp, date_list,heure_list, actually

#le code suivant permet de rafraichir les données toutes les 10 secondes et de les afficher sur la page web

@app.route("/")
@app.route("/accueil")
@app.route("/home")
def index():
    temp, date_list, heure_list, actually = get_temperature()
    return render_template("index.html", actually=actually, temp=temp, date=date_list, heure=heure_list)