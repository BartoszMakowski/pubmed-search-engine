from flask_wtf import Form
from wtforms import StringField
from wtforms.validators import DataRequired


class SearchArtForm(Form):
    search_phrase = StringField('search phrase', validators=[DataRequired()])
