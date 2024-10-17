from flask import Flask

app = Flask(__name__)
app.config["SECRET_KEY"] = b'0427fc711bc8cf7d6a81c233a23bb1531f6a4d817c16d48dc739dffff6add6a8'
TEMPLATES_AUTO_RELOAD = True

import routes