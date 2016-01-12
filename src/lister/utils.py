import json
import re
import logging
import traceback
from io import BytesIO

import requests
from amazon.api import AmazonAPI
from bs4 import BeautifulSoup
from ebaysdk.trading import Connection as Trading
from PIL import Image

from django.conf import settings
from django.utils import timezone

from .models import AmazonItem, EbayItem

MAX_AMAZON_ITEM_COUNT_PER_SEARCH = 10
EBAY_ITEM_PERCENTAGE_MARKUP = 1.5

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
        self.total_count = 0

    def get_review_count(self, title, url, has_review, review_url):
        if not has_review:
            return 0
        try:
            response = requests.get(review_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            count = soup.find(string=re.compile('[0-9,]+ customer reviews'))
            count = int(count.split()[0].replace(',', ''))
            logger.info(
                u'Review count for Amazon item {} from url {} is {}'.format(
                    title, url, count
                )
            )
            return count
        except AttributeError:
            logger.warning(
                u'Review count for Amazon item {} from url {} not foun'
                'd'.format(title, url)
            )
            return 0
        except:
            logger.error(traceback.format_exc())
            return 0

    def get_image_list(self, result):
        image_list = []
        for url in [str(image.LargeImage.URL) for image in result.images]:
            response = requests.get(url)
            image = Image.open(BytesIO(response.content))
            height, width = image.size
            if height >= 500 or width >= 500:
                image_list.append(url)
        logger.info(
            u'Got {} images for Amazon item {}'.format(
                len(image_list), result.title
            )
        )
        return json.dumps(image_list)

    def parse_result(self, result, search_obj):
        url = '/'.join(result.offer_url.split('/')[:-1])
        title = result.title
        feature_list = json.dumps(result.features)
        image_list = self.get_image_list(result)
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
            message += u'{}: {}\n'.format(key.upper(), value)
        logger.info(message.strip())
        return item

    def search(self, search_obj):
        try:
            results = self.connection.search(
                Keywords=search_obj.query, SearchIndex='All'
            )
            results = list(reversed(list(results)))
            logger.info(
                u'Got {} search results from Amazon API for query {}'.format(
                    len(results), search_obj.query
                )
            )
        except:
            results = []
            logger.error(traceback.format_exc())
            logger.warning(
                u'Got 0 search results from Amazon API for query {}'.format(
                    search_obj.query
                )
            )
        search_obj.date_searched = timezone.now()
        search_obj.save()
        count = 0
        for result in results:
            if count > MAX_AMAZON_ITEM_COUNT_PER_SEARCH:
                logger.info(
                    'Reached maximum Amazon item count per search limit'
                )
                break
            result = self.parse_result(result, search_obj)
            item_obj = AmazonItem(**result)
            if item_obj.is_valid():
                try:
                    item_obj.save()
                    logger.info(
                        u'Saved amazon item: {}'.format(item_obj.title)
                    )
                    count += 1
                except:
                    logger.error(traceback.format_exc())
                    logger.warning(
                        u'Failed to save amazon item: {}'.format(
                            item_obj.title
                        )
                    )
        logger.info(
            u'Saved {} amazon items for query {}'.format(
                count, search_obj.query
            )
        )
        self.total_count += count


class Ebay(object):

    def __init__(self):
        try:
            self.production_connection = Trading(
                devid=settings.EBAY_DEVID,
                appid=settings.EBAY_PRODUCTION_APPID,
                certid=settings.EBAY_PRODUCTION_CERTID,
                token=settings.EBAY_PRODUCTION_TOKEN,
                config_file=None
            )
            logger.info('Established Ebay Production API connection')
            self.sandbox_connection = Trading(
                domain='api.sandbox.ebay.com',
                devid=settings.EBAY_DEVID,
                appid=settings.EBAY_SANDBOX_APPID,
                certid=settings.EBAY_SANDBOX_CERTID,
                token=settings.EBAY_SANDBOX_TOKEN,
                config_file=None
            )
            logger.info('Established Ebay Sandbox API connection')
        except:
            self.production_connection = None
            self.sandbox_connection = None
            logger.error(traceback.format_exc())
            logger.error('Failed to establish Ebay API connection')
        self.total_count = 0

    def category_search(self, query):
        response = self.production_connection.execute(
            'GetSuggestedCategories', {'Query': query}
        )
        response = response.dict()
        logger.info(
            'Got {} suggested categories for query {}'.format(
                response['SuggestedCategoryArray']['SuggestedCategory'],
                query
            )
        )
        return [
            (int(c['Category']['CategoryID']), c['Category']['CategoryName'])
            for c in response['SuggestedCategoryArray']['SuggestedCategory']
        ]

    def list(self, amazon_item):
        title = amazon_item.itemreview.title
        html = amazon_item.itemreview.html
        category_id = str(amazon_item.itemreview.category_id)
        price = str(amazon_item.price * EBAY_ITEM_PERCENTAGE_MARKUP)
        image_list = amazon_item.image_list
        manufacturer = amazon_item.itemreview.manufacturer
        mpn = amazon_item.itemreview.mpn
        upc = amazon_item.itemreview.upc
        item_dict = {
            'Item': {
                'Title': title,
                'Description': html,
                'PrimaryCategory': {'CategoryID': category_id},
                'StartPrice': price,
                'CategoryMappingAllowed': 'true',
                'ConditionID': '1000',
                'Country': 'US',
                'Currency': 'USD',
                'DispatchTimeMax': '3',
                'ListingDuration': 'Days_30',
                'ListingType': 'FixedPriceItem',
                'Location': 'Los Angeles, CA',
                'PaymentMethods': 'PayPal',
                'PayPalEmailAddress': 'joshwardini@gmail.com',
                'PictureDetails': {'PictureURL': image_list},
                'ItemSpecifics': {
                    'NameValueList': [
                        {'Name': 'Brand', 'Value': manufacturer},
                        {'Name': 'MPN', 'Value': mpn},
                    ]
                },
                'ProductListingDetails': {
                    'UPC': upc,
                    'ListIfNoProduct': 'true',
                },
                'PostalCode': '90001',
                'Quantity': '1',
                'ShippingDetails': {
                    'ShippingType': 'Flat',
                    'ShippingServiceOptions': {
                        'ShippingServicePriority': '1',
                        'ShippingService': 'USPSMedia',
                        'ShippingServiceCost': '0.00'
                    }
                },
                'ReturnPolicy': {
                    'Description': (
                        '14 days money back, you pay return shipping'
                    ),
                    'ReturnsAcceptedOption': 'ReturnsAccepted',
                    'RefundOption': 'MoneyBack',
                    'ReturnsWithinOption': 'Days_14',
                    'ShippingCostPaidByOption': 'Buyer'
                },
                'Site': 'US',
            }
        }
        if settings.DEBUG:
            connection = self.sandbox_connection
        else:
            connection = self.production_connection
        try:
            response = connection('AddFixedPriceItem', item_dict)
            logger.info('Listed ebay item {}'.format(title))
        except:
            logger.info('Failed to list ebay item {}'.format(title))
            return
        url = 'http://www.ebay.com/itm/-/{}?ssPageName=ADME:L:LCA:US:112'\
            '3'.format(response.dict()['ItemID'])
        item = EbayItem(review=amazon_item.itemreview, price=price, url=url)
        try:
            item.save()
            logger.info(u'Saved ebay item: {}'.format(item.title))
            self.total_count += 1
        except:
            logger.error(traceback.format_exc())
            logger.warning(u'Failed to save ebay item: {}'.format(item.title))
