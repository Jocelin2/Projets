# We start to activate the virtual environment : source acd_env/bin/activate (Linux) / .\acd_env\Scripts\activate (Windows)
# We start the server : python run.py

from __init__ import app

if __name__ == '__main__':
    app.run(debug=True)