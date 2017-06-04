from flask import Flask
import lucene

lucene.initVM()

app = Flask(__name__)
app.config.from_object('config')

from app import views


