__author__ = '4ikist'
import data_handler

if __name__ == '__main__':
    dh = data_handler.FlickrDataHandler()
    photo_objects = dh.get_photo_objects(size='Square', tags=['enot'])
    photo_objects2 = dh.get_photo_objects(size=['Square', 'Original'], tags='test')
    print ''