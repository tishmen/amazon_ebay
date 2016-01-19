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

from .models import AmazonItem

logger = logging.getLogger(__name__)


class Amazon(object):

    def __init__(self):
        try:
            self.connection = AmazonAPI(
                settings.AMAZON_ACCESS_KEY, settings.AMAZON_SECRET_KEY,
                settings.AMAZON_ASSOCIATE_TAG
            )
            logger.info(u'Established Amazon API connection')
        except:
            self.connection = None
            logger.error(traceback.format_exc())
            logger.error(u'Failed to establish Amazon API connection')
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
            if height >= 500 and width >= 500:
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
            message += '{}: {}\n'.format(key.upper(), value)
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
            if count > settings.MAX_AMAZON_ITEM_COUNT_PER_SEARCH:
                logger.info(
                    u'Reached maximum Amazon item count per search limit'
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
                devid=settings.EBAY_PRODUCTION_DEVID,
                appid=settings.EBAY_PRODUCTION_APPID,
                certid=settings.EBAY_PRODUCTION_CERTID,
                token=settings.EBAY_PRODUCTION_TOKEN, config_file=None
            )
            logger.info(u'Established Ebay Production API connection')
            self.sandbox_connection = Trading(
                domain='api.sandbox.ebay.com',
                devid=settings.EBAY_SANDBOX_DEVID,
                appid=settings.EBAY_SANDBOX_APPID,
                certid=settings.EBAY_SANDBOX_CERTID,
                token=settings.EBAY_SANDBOX_TOKEN, config_file=None
            )
            logger.info(u'Established Ebay Sandbox API connection')
        except:
            self.production_connection = self.sandbox_connection = None
            logger.error(traceback.format_exc())
            logger.error(u'Failed to establish Ebay API connection')
        self.total_count = 0

    def category_search(self, query):
        response = self.production_connection.execute(
            'GetSuggestedCategories', {'Query': query}
        )
        response = response.dict()
        logger.info(
            u'Got {} suggested categories for query {}'.format(
                response['SuggestedCategoryArray']['SuggestedCategory'],
                query
            )
        )
        return [
            (int(c['Category']['CategoryID']), c['Category']['CategoryName'])
            for c in response['SuggestedCategoryArray']['SuggestedCategory']
        ]

    def list(self, item_obj):
        if settings.USE_SANDBOX:
            connection = self.sandbox_connection
            url = 'http://cgi.sandbox.ebay.com/ws/eBayISAPI.dll?ViewItem&item'\
                '={}&ssPageName=STRK:MESELX:IT'
        else:
            connection = self.produiction_connection
            url = 'http://www.ebay.com/itm/-/{}?ssPageName=ADME:L:LCA:US:1123'
        item_dict = {
            'Item': {
                'Title': item_obj.title,
                'Description': u'<![CDATA[{}]]>'.format(item_obj.html),
                'PrimaryCategory': {'CategoryID': item_obj.category_id},
                'StartPrice': item_obj.price,
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
                'PictureDetails': {
                    'PictureURL': item_obj.get_image_list(),
                },
                'ItemSpecifics': {
                    'NameValueList': [
                        {'Name': 'Brand', 'Value': item_obj.manufacturer},
                        {'Name': 'MPN', 'Value': item_obj.mpn},
                    ]
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
                    'Description': '14 days money back, you pay return shippin'
                    'g',
                    'ReturnsAcceptedOption': 'ReturnsAccepted',
                    'RefundOption': 'MoneyBack',
                    'ReturnsWithinOption': 'Days_14',
                    'ShippingCostPaidByOption': 'Buyer'
                },
                'Site': 'US',
            }
        }
        if item_obj.upc:
            item_dict['Item'] = {
                'ProductListingDetails': {
                    'UPC': item_obj.upc,
                    'ListIfNoProduct': 'true',
                },
            }
        try:
            response = connection.execute('AddFixedPriceItem', item_dict)
            logger.info(u'Listed Ebay item {}'.format(item_obj.title))
            item_obj.url = url.format(response.dict()['ItemID'])
            item_obj.is_listed = True
            item_obj.date_listed = timezone.now()
        except:
            logger.info(u'Failed to list Ebay item {}'.format(item_obj.title))
            item_obj.error = traceback.format_exc()
        try:
            item_obj.save()
            logger.info(u'Saved Ebay item {}'.format(item_obj.title))
            self.total_count += 1
        except:
            logger.info(u'Failed to save Ebay item {}'.format(item_obj.title))
