import sys
import json

sys.path.insert(0,'/webapps/catalog')

from project import app

app.secret_key = 'my_super_secret_app_key'

application = app
