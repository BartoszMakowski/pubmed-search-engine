from app import app
from .forms import SearchArtForm
from flask import render_template
from .lucene_logic import search, index_articles, my_tokenizer


@app.route('/', methods=['GET', 'POST'])
@app.route('/index')
def index():
    form = SearchArtForm()
    if form.validate_on_submit():
        arts, tokens = search(form.search_phrase.data)
        return render_template('search_results.html.j2', form=form, articles=arts, tokens=tokens)
    return render_template('index.html.j2', form=form)
