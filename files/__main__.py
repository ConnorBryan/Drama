import gevent.monkey
gevent.monkey.patch_all()
from os import environ
import secrets
from flask import *
from flask_caching import Cache
from flask_limiter import Limiter
from flask_compress import Compress
from flask_limiter.util import get_ipaddr
from flask_mail import Mail
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import *
import gevent
from werkzeug.middleware.proxy_fix import ProxyFix
import redis
import time
from sys import stdout
import faulthandler

app = Flask(__name__, template_folder='templates')
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=3)
app.url_map.strict_slashes = False
app.jinja_env.cache = {}
app.jinja_env.auto_reload = True
faulthandler.enable()

app.config["SITE_NAME"]=environ.get("SITE_NAME").strip()
app.config["GUMROAD_LINK"]=environ.get("GUMROAD_LINK", "https://marsey1.gumroad.com/l/tfcvri").strip()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DATABASE_URL'] = environ.get("DATABASE_URL")
app.config['SECRET_KEY'] = environ.get('MASTER_KEY')
app.config["SERVER_NAME"] = environ.get("DOMAIN").strip()
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 86400
app.config["SESSION_COOKIE_NAME"] = "session_" + environ.get("SITE_NAME").strip().lower()
app.config["VERSION"] = "1.0.0"
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 60 * 24 * 365
app.config["SLOGAN"] = environ.get("SLOGAN", "").strip()
app.config["DEFAULT_COLOR"] = environ.get("DEFAULT_COLOR", "ff0000").strip()
app.config["DEFAULT_THEME"] = environ.get("DEFAULT_THEME", "midnight").strip()
app.config["FORCE_HTTPS"] = 1
app.config["UserAgent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
app.config["HCAPTCHA_SITEKEY"] = environ.get("HCAPTCHA_SITEKEY","").strip()
app.config["HCAPTCHA_SECRET"] = environ.get("HCAPTCHA_SECRET","").strip()
app.config["SPAM_SIMILARITY_THRESHOLD"] = float(environ.get("SPAM_SIMILARITY_THRESHOLD", 0.5))
app.config["SPAM_URL_SIMILARITY_THRESHOLD"] = float(environ.get("SPAM_URL_SIMILARITY_THRESHOLD", 0.1))
app.config["SPAM_SIMILAR_COUNT_THRESHOLD"] = int(environ.get("SPAM_SIMILAR_COUNT_THRESHOLD", 10))
app.config["COMMENT_SPAM_SIMILAR_THRESHOLD"] = float(environ.get("COMMENT_SPAM_SIMILAR_THRESHOLD", 0.5))
app.config["COMMENT_SPAM_COUNT_THRESHOLD"] = int(environ.get("COMMENT_SPAM_COUNT_THRESHOLD", 10))
app.config["READ_ONLY"]=bool(int(environ.get("READ_ONLY", "0")))
app.config["BOT_DISABLE"]=bool(int(environ.get("BOT_DISABLE", False)))
app.config["CACHE_TYPE"] = "filesystem"
app.config["CACHE_DIR"] = "cache"
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = environ.get("MAIL_USERNAME", "").strip()
app.config['MAIL_PASSWORD'] = environ.get("MAIL_PASSWORD", "").strip()
app.config['DESCRIPTION'] = environ.get("DESCRIPTION", "rdrama.net caters to drama in all forms such as: Real life, videos, photos, gossip, rumors, news sites, Reddit, and Beyond™. There isn't drama we won't touch, and we want it all!").strip()

r=redis.Redis(host=environ.get("REDIS_URL", "redis://localhost"), decode_responses=True, ssl_cert_reqs=None)

limiter = Limiter(
	app,
	key_func=get_ipaddr,
	default_limits=["3/second;30/minute;200/hour;1000/day"],
	application_limits=["10/second;200/minute;5000/hour;10000/day"],
	storage_uri=environ.get("REDIS_URL", "redis://localhost")
)

Base = declarative_base()

engine = create_engine(app.config['DATABASE_URL'])

db_session = scoped_session(sessionmaker(bind=engine, autoflush=False))

cache = Cache(app)
Compress(app)
mail = Mail(app)

@app.before_request
def before_request():

	if request.method.lower() != "get" and app.config["READ_ONLY"]:
		return {"error":f"{app.config['SITE_NAME']} is currently in read-only mode."}, 500

	if app.config["BOT_DISABLE"] and request.headers.get("Authorization"): abort(503)

	g.db = db_session()

	g.timestamp = int(time.time())

	if '; wv) ' in request.headers.get("User-Agent",""): g.webview = True
	else: g.webview = False

@app.teardown_appcontext
def teardown_request(error):
	if hasattr(g, 'db') and g.db:
		g.db.close()
	stdout.flush()

@app.after_request
def after_request(response):

	response.headers.add("Strict-Transport-Security", "max-age=31536000")
	response.headers.add("X-Frame-Options", "deny")
	return response

from files.routes import *