from flask_wtf import Form
from wtforms import StringField, FileField
from wtforms.validators import DataRequired


class SearchArtForm(Form):
    search_phrase = StringField('search phrase', validators=[DataRequired()])

class AddDataForm(Form):
    file = FileField('file')