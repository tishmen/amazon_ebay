import re
import logging
import traceback

import requests
from amazon.api import AmazonAPI
from bs4 import BeautifulSoup

from django.conf import settings

from .models import AmazonItem

MAX_AMAZON_ITEM_COUNT_PER_SEARCH = 10

logger = logging.getLogger(__name__)


class Amazon(object):

    def __init__(self):
        try:
            self.connection = AmazonAPI(
                settings.AMAZON_ACCESS_KEY,
                settings.AMAZON_SECRET_KEY,
                settings.AMAZON_ASSOCIATE_TAG
            )
            logger.info('Established Amazon API connection')
        except:
            self.connection = None
            logger.error(traceback.format_exc())
            logger.error('Failed to establish Amazon API connection')

    def get_review_count(self, title, url, has_review, review_url):
        if not has_review:
            return 0
        try:
            response = requests.get(review_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            count = soup.find(string=re.compile('[0-9,]+ customer reviews'))
            count = int(count.split()[0].replace(',', ''))
            logger.info(
                'Review count for Amazon item {} from url {} is {}'.format(title, url, count)
            )
            return count
        except:
            logger.error(traceback.format_exc())
            logger.warning(
                'Review count for Amazon item {} from url {} not found'.format(title, url)
            )
            return 0

    def parse_result(self, result, search_obj):
        url = '/'.join(result.offer_url.split('/')[:-1])
        title = result.title
        feature_list = result.features
        image_list = [str(image.LargeImage.URL) for image in result.images]
        price = result.price_and_currency[0] or result.list_price[0] or 0
        manufacturer = result.manufacturer
        mpn = result.mpn
        review_count = self.get_review_count(title, url, *result.reviews)
        item = {
            'search': search_obj,
            'url': url,
            'title': title,
            'feature_list': feature_list,
            'image_list': image_list,
            'price': price,
            'manufacturer': manufacturer,
            'mpn': mpn,
            'review_count': review_count,
        }
        message = 'Parsed Amazon item:\n'
        for key, value in item.items():
            message += '{}: {}\n'.format(key.upper(), value)
        logger.info(message.strip())
        return item

    def search(self, search_objs):
        if not self.connection:
            return
        for search_obj in search_objs:
            total_count = 0
            try:
                results = list(
                    self.connection.search(Keywords=search_obj.query, SearchIndex='All')
                )
                logger.info(
                    'Got {} search results from Amazon API for query {}'.format(
                        len(results), search_obj.query
                    )
                )
            except:
                results = []
                logger.error(traceback.format_exc())
                logger.warning(
                    'Got 0 search results from Amazon API for query {}'.format(search_obj.query)
                )
            count = 0
            for result in results:
                if count > MAX_AMAZON_ITEM_COUNT_PER_SEARCH:
                    logger.info('Reached maximum Amazon item count per search limit')
                    break
                result = self.parse_result(result, search_obj)
                item_obj = AmazonItem(**result)
                if item_obj.is_valid():
                    item_obj.save()
                    logger.info('Saved amazon item: {}'.format(item_obj.title))
                    count += 1
            logger.info('Saved {} amazon items for query {}'.format(count, search_obj.query))
            total_count += count
        logger.info('Saved total of {} amazon items'.format(total_count))
