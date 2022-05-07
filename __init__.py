from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
import pymongo

app = Flask(__name__)
app.config['SECRET_KEY'] = '152b76aba12004c9d5de86a4cc433d36' # Used to add Cross Site Request Forgery (CSRF) token
app.config["UPLOAD_VIP"] = 'upark/static/vip'
app.config["UPLOAD_PATH"] = 'upark/static/ads'
mongo = pymongo.MongoClient("mongodb+srv://upark:upark@cluster0.kyjwa.mongodb.net/UPark?retryWrites=true&w=majority")
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
db = mongo.upark # upark is a database, has 4 collections: customers, parkings, clusters, images
bcrypt = Bcrypt(app)

from upark import routes