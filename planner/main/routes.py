import folium
from flask import render_template

from planner.main import bp


@bp.route('/')
def index():
    m = folium.Map()
    # set the iframe width and height
    m.get_root().width = "100%"
    m.get_root().height = "100%"
    iframe = m.get_root()._repr_html_()
    return render_template('index.html', iframe=iframe)
