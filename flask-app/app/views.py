from app import app
from .forms import SearchArtForm, AddDataForm
from flask import render_template, request
from flask_wtf import Form
from .lucene_logic import search, index_articles, my_tokenizer
from werkzeug.utils import secure_filename
import os


@app.route('/search', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
@app.route('/index')
def index():
    form = SearchArtForm()
    if form.validate_on_submit():
        arts, tokens = search(form.search_phrase.data)
        return render_template('search_results.html.j2', form=form, articles=arts, tokens=tokens.split())
    return render_template('index.html.j2', form=form)


@app.route('/add', methods=['GET', 'POST'])
def add_data():
    form = AddDataForm()
    if request.method == 'POST':
        file = request.files['file']
        filename = secure_filename(file.filename)
        # print(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        index_articles(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        alert = 'Pomyślnie zaindeksowano przesłaną aktualizację'
        return render_template('add_data.html.j2', form=form, alert=alert)
    return render_template('add_data.html.j2', form=form)
