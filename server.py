import random
from time import sleep
from alina_portfolio.data_storage.data_handler import FlickrDataHandler

from flask import Flask, render_template, jsonify, request

__author__ = '4ikist'

app = Flask('aptf')
dh = FlickrDataHandler(ttl=3600 * 24 * 365)
count_in_block = 3


@app.route('/')
def index():
    po = dh.get_photo_objects(tags=['header'])
    header = random.choice(po) if po else None
    header_url = header['urls']['Large'] if header else '//c2.staticflickr.com/6/5601/15528778702_c93a776733_h.jpg'

    figures_art = dh.get_photo_objects(tags=['art'])
    figures_sketch = dh.get_photo_objects(tags=['sketch'])

    return render_template('index.html', header_pic=header_url, figures_art=figures_art,
                           figures_sketch=figures_sketch, )


@app.route('/tags')
def get_object_by_tag():
    dh.get_photo_objects(tags=request)
    return jsonify({})


def refresh_cache():
    for id in dh._get_photos_ids(True):
        dh._get_or_load_photo_data(force=True, **id)

if __name__ == '__main__':
    refresh_cache()
    app.run()
