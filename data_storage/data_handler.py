from datetime import datetime
import json
import requests
from threading import Thread
from pymongo.mongo_client import MongoClient
from alina_portfolio.properties import flickr_base_url, flickr_api_key, flickr_user_id, logger, portfolio_tags, \
    photo_data_ttl, photo_ids_ttl, min_photos_count, mongo_host, mongo_port, mongo_db_name

__author__ = '4ikist'

photo_sizes = ['Square', 'Large Square', 'Thumbnail', 'Small', 'Small 320', 'Medium', 'Medium 800', 'Medium 640',
               'Large', 'Original']

log = logger.getChild('data_handler')


class Cache(object):
    def __init__(self, ttl=3600):
        self.data = {}
        self.ttl = ttl
        try:
            self.storage = MongoClient(host=mongo_host, port=mongo_port)[mongo_db_name]['temp']
        except:
            class FakeStorage():
                def save(self, data):
                    pass

                def find_one(self, spec):
                    return None
            self.storage = FakeStorage()

    def add(self, k, v, ttl=None):
        saved = {'key':k,'content': v, 'time': datetime.now(), 'ttl': self.ttl if ttl is None else ttl}
        self.data[k] = saved
        self.storage.save(saved)

    def get(self, k):
        if k in self.data:
            if (datetime.now() - self.data[k]['time']).total_seconds() > self.data[k]['ttl']:
                del self.data[k]
                return None
            else:
                return self.data[k]['content']
        else:
            found = self.storage.find_one({'key':k})
            if found:
                self.data[k] = found
                return self.data[k]['content']
            return None

cache = Cache(ttl=photo_data_ttl)

class FlickrDataHandler(object):
    def __init__(self, ttl=3600):
        self.__fill_cache = False
        self.start_fill_cache(init=True)

    def start_fill_cache(self, init=False):
        def target():
            self.__fill_cache = True
            ids = self._get_photos_ids(init)
            for i, el in enumerate(ids):
                self._get_or_load_photo_data(force=init if i<=min_photos_count else False,**el)

            self.__fill_cache = False

        if not self.__fill_cache:
            t = Thread(target=target)
            t.start()

    def _fill_params(self, params):
        return dict({'api_key': flickr_api_key,
                     'format': 'json',
                     'nojsoncallback': 1},
                    **params)

    def _get_photos_ids(self, init=False):
        photos_ids = cache.get('photos_ids')
        if not photos_ids:
            def target():
                photos_ids = []
                user_photos_result = requests.get(flickr_base_url,
                                                  params=self._fill_params(
                                                      {'method': 'flickr.people.getPhotos', 'user_id': flickr_user_id}))
                if user_photos_result.status_code == 200:
                    user_photos_result = json.loads(user_photos_result.content)
                    for photo in user_photos_result['photos']['photo']:
                        photos_ids.append({'photo_id': photo['id'], 'secret': photo['secret']})
                    cache.add('photos_ids', photos_ids, ttl=photo_ids_ttl)
                else:
                    log.error('can not load photos ids because:\n%s' % user_photos_result.content)

                log.info('indexes loaded! For %s photos' % len(photos_ids))
                return photos_ids

            th = Thread(target=target)
            th.start()
            if init:
                th.join()

                log.info('photo_ids will loaded, now: %s'%cache.get('photo_ids'))

            return cache.get('photo_ids') or []

        return photos_ids

    def __get_photo_urls(self, photo_id):
        photo_url_result = requests.get(flickr_base_url,
                                        params=self._fill_params(
                                            {'method': 'flickr.photos.getSizes', 'photo_id': photo_id}))
        if photo_url_result.status_code == 200:
            photo_url_result = json.loads(photo_url_result.content)
            result = {}
            for url_data in photo_url_result['sizes']['size']:
                result[url_data['label']] = url_data['source']
            return result
        else:
            log.error('can not load photo urls because:\n%s' % photo_url_result.content)

    def __get_photo_info(self, photo_id, photo_secret):
        photo_url_result = requests.get(flickr_base_url,
                                        params=self._fill_params(
                                            {'method': 'flickr.photos.getInfo', 'photo_id': photo_id,
                                             'secret': photo_secret}))
        if photo_url_result.status_code == 200:
            photo_url_result = json.loads(photo_url_result.content)
            tags = []
            for tag_data in photo_url_result['photo']['tags']['tag']:
                tags.append(tag_data['_content'])
            date_posted = datetime.fromtimestamp(float(photo_url_result['photo']['dates']['posted']))
            name = photo_url_result['photo']['title']['_content']
            description = photo_url_result['photo']['description']['_content']
            return tags, date_posted, name, description
        else:
            log.error('can not load photo info because:\n%s' % photo_url_result.content)

    def _get_or_load_photo_data(self, photo_id, secret, force=False):
        photo_cache = cache.get(photo_id)
        if not photo_cache:
            log.info('photo not in cache will load')
            def target():
                log.info('photo %s retrieve started '% photo_id)
                urls = self.__get_photo_urls(photo_id)
                tags, date_posted, name, descr = self.__get_photo_info(photo_id, secret)
                photo_cache = {'urls': urls, 'tags': tags, 'date': date_posted, 'name': name, 'description': descr}
                cache.add(photo_id, photo_cache, ttl=photo_data_ttl)
                log.info('photo %s was retrieved' % photo_id)

            th = Thread(target=target)
            th.start()
            if force:
                try:
                    th.join(1000)

                except:
                    return self._get_or_load_photo_data(photo_id, secret, force)

        return cache.get(photo_id)

    def get_photo_objects(self, tags=None, size=None):
        """
        :param tags: tags which must be in photo
        :param size: one or list of: ['Square', 'Large Square', 'Thumbnail', 'Small', 'Small 320', 'Medium', 'Medium 800', 'Medium 640',
               'Large', 'Original']
        :return: [{
            urls:{'Square':'url_of square'},
            tags:['portfolio',...],
            date: date when upload in flickr
        }, ...]
        """

        def get_only_this_size(photo_info):
            if size:
                if isinstance(size, list):
                    predicate = lambda x: x in size
                else:
                    predicate = lambda x: x == size
                photo_info['urls'] = dict([(k, v) for k, v in photo_info['urls'].iteritems() if predicate(k)])
            return photo_info

        photo_objects = []
        if tags:
            if isinstance(tags, (list)):
                interested_tags = set(portfolio_tags).union(tags)
            else:
                interested_tags = set(portfolio_tags).union([tags])
        else:
            interested_tags = set(portfolio_tags)

        photos_ids = self._get_photos_ids()
        for photo_id in photos_ids:
            photo_info = self._get_or_load_photo_data(**photo_id)

            if photo_info and \
                    (interested_tags.issubset(photo_info['tags']) or interested_tags.issuperset(photo_info['tags'])):
                photo_objects.append(get_only_this_size(photo_info))
        photo_objects.sort(key=lambda x: x['date'], reverse=True)
        return photo_objects
