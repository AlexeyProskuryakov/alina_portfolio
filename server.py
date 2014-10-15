from alina_portfolio.data_storage.data_handler import FlickrDataHandler
from flask import Flask, render_template

__author__ = '4ikist'

app = Flask('aptf')
dh = FlickrDataHandler()


@app.route('/')
def index():
    header_data = dh.get_photo_objects(tags=['header'], size='Large')[0]
    header_url = header_data['urls']['Large']
    figures_art = dh.get_photo_objects(tags=['art'])
    figures_sketch = dh.get_photo_objects(tags=['sketch'])
    return render_template('index.html', header_pic=header_url, figures_art=figures_art, figures_sketch=figures_sketch)


if __name__ == '__main__':
    app.run()