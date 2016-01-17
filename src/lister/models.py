from __future__ import unicode_literals

import json
import logging
import math

from django.contrib.auth.models import User
from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible

logger = logging.getLogger(__name__)


def get_html(title, feature_list):
    html = '<div id="ds_div"><h1 class="p1" style="text-align: center;"><span'\
        ' class="s1"><strong>{}</strong></span></h1><h1 class="p2" style="tex'\
        't-align: center;"><span class="s1"><strong>Product Description:</str'\
        'ong></span></h1><h2><strong>&lt; Insert Description Here &gt;</stron'\
        'g></h2><h2>&nbsp;</h2><h2 class="p2"><span class="s1">Features:</spa'\
        'n></h2><ul class="ul1">'.format(title)
    for feature in json.loads(feature_list):
        html += '<li class="li3"><span class="s1">{}</span></li>'.format(
            feature
        )
    return html + '</ul><br></br><h2>Shipping / Return Policies (Balanced):</'\
        'h2><h3>Shipping Policies:</h3><ul><li>We ship to the Lower 48 States'\
        ' only (Does NOT include Hawaii or Alaska)</li><li>We cannot ship to '\
        'PO Boxes/APO\'s</li><li>We cannot combine shipping.</li><li>No Local'\
        ' Pickup.</li></ul><p>All items will be shipped directly to you from '\
        'our supplier within 1-3 business days. Most items are delivered with'\
        'in 3-5 business days, however, please allow 3-10 business days.</p><'\
        'p>All items are in stock when they are listed. Inventory is tracked '\
        'and updated regularly. However, if demand exceeds our supply, we wil'\
        'l give the customer the following options: Full refund. Have the ite'\
        'm back ordered and shipped when it becomes available. We will offer '\
        'other items in similar style and quality. Your bid / purchase of the'\
        ' item implies you agree to this policy.</p><p>If you have a question'\
        ' about a product not otherwise answered in the item description, ple'\
        'ase contact us via eBay messages first and allow us the opportunity '\
        'to help you and be sure we have what you\'re looking for.</p><h3>Exc'\
        'hange/Return Policy:</h3><p>Your satisfaction is guaranteed! If for '\
        'any reason you are unhappy with your item, just return it within 14 '\
        'days for a full refund, minus shipping cost. Please contact us prior'\
        ' to initiating a return so that we can issue you a refund authorizat'\
        'ion.</p><h3>Payment Policy</h3><p>We require Immediate Payment. Must'\
        ' be an authorized address.</p></div><p>Thank you for viewing the {}<'\
        '/p>'.format(title).encode('utf-8')


@python_2_unicode_compatible
class AmazonSearch(models.Model):

    query = models.CharField(max_length=100)
    date_searched = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'amazon searches'

    def __str__(self):
        return self.query


@python_2_unicode_compatible
class AmazonItem(models.Model):

    search = models.ForeignKey('AmazonSearch')
    reviewer = models.ForeignKey(User, null=True, blank=True)
    url = models.URLField(unique=True)
    title = models.TextField()
    feature_list = models.TextField()
    image_list = models.TextField()
    price = models.FloatField()
    manufacturer = models.TextField(null=True, blank=True)
    mpn = models.TextField(null=True, blank=True)
    review_count = models.PositiveIntegerField(verbose_name='reviews')
    date_added = models.DateTimeField(auto_now_add=True)

    def get_url(self):
        return '<a href="{0}" target="_blank">{0}</a>'.format(self.url)

    get_url.short_description = get_url.admin_order_field = 'url'
    get_url.allow_tags = True

    def get_title(self):
        return '<a href="/admin/lister/amazonitem/{}/change/">{}</a>'.format(
            self.id, self.title
        )

    get_title.allow_tags = True

    def get_price(self):
        return '${}'.format(self.price)

    get_price.short_description = get_price.admin_order_field = 'price'
    get_price.allow_tags = True

    def get_feature_list(self):
        feature_list = ''
        for feature in json.loads(self.feature_list):
            if feature:
                feature_list += '{}\n'.format(feature)
        return feature_list.strip()

    get_feature_list.short_description = 'features'

    def get_html(self):
        return get_html(self.title, self.feature_list)

    def get_image(self):
        return '<img src="{}" />'.format(json.loads(self.image_list)[0])

    def get_price_markup(self):
        return math.ceil(self.price * settings.EBAY_ITEM_PERCENTAGE_MARKUP)

    def get_related_ebay_item(self):
        return self.ebayitem_set.first()

    def is_valid(self):
        image_list = json.loads(self.image_list)
        if len(image_list) < settings.MIN_AMAZON_ITEM_IMAGE_COUNT:
            logger.info(
                'Less than minimum item image count {} for item {} with image '
                'count of {}'.format(
                    settings.MIN_AMAZON_ITEM_IMAGE_COUNT, self.title,
                    len(image_list)
                )
            )
            return
        if self.price < settings.MIN_AMAZON_ITEM_PRICE:
            logger.info(
                'Less than minimum amazon item price {} for item {} with price'
                ' {}'.format(
                    settings.MIN_AMAZON_ITEM_PRICE, self.title, self.price
                )
            )
            return
        if self.price > settings.MAX_AMAZON_ITEM_PRICE:
            logger.info(
                'More than minimum amazon item price {} for item {} with price'
                ' {}'.format(
                    settings.MIN_AMAZON_ITEM_PRICE, self.title, self.price
                )
            )
            return
        if self.review_count < settings.MIN_AMAZON_ITEM_REVIEW_COUNT:
            logger.info(
                'Less than minimum item review count {} for item {} with revie'
                'w count of {}'.format(
                    settings.MIN_AMAZON_ITEM_REVIEW_COUNT, self.title,
                    self.review_count
                )
            )
            return
        if self.review_count > settings.MAX_AMAZON_ITEM_REVIEW_COUNT:
            logger.info(
                'More than maximum allowed item review count {} for item {} wi'
                'th review count {}'.format(
                    settings.MAX_AMAZON_ITEM_REVIEW_COUNT, self.title,
                    self.review_count
                )
            )
            return
        return True

    def __str__(self):
        return self.title


@python_2_unicode_compatible
class EbayItem(models.Model):

    item = models.ForeignKey('AmazonItem', unique=True)
    title = models.CharField(max_length=80)
    url = models.URLField(unique=True, null=True, blank=True)
    price = models.FloatField()
    html = models.TextField()
    category_search = models.TextField()
    category_id = models.IntegerField()
    category_name = models.TextField()
    manufacturer = models.CharField(max_length=65)
    mpn = models.CharField(max_length=65)
    upc = models.CharField(max_length=12, null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    is_ready = models.BooleanField(default=False)
    is_listed = models.BooleanField(default=False)
    date_listed = models.DateTimeField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)

    def get_url(self):
        if self.url:
            return '<a href="{0}" target="_blank">{0}</a>'.format(self.url)

    get_url.short_description = get_url.admin_order_field = 'url'
    get_url.allow_tags = True

    def get_ebay_url(self):
        return self.get_url()

    get_ebay_url.short_description = 'ebay url'
    get_ebay_url.allow_tags = True

    def get_amazon_url(self):
        return '<a href="{0}" target="_blank">{0}</a>'.format(self.item.url)

    get_amazon_url.short_description = 'amazon url'
    get_amazon_url.allow_tags = True
    get_amazon_url.admin_order_field = 'item__url'

    def get_price(self):
        return '${}'.format(self.price)

    get_price.short_description = get_price.admin_order_field = 'price'
    get_price.allow_tags = True

    def get_image(self):
        return self.item.get_image()

    def get_image_list(self):
        return json.loads(self.item.image_list)

    def get_error(self):
        return '<strong style="color:red">{}</strong>'.format(self.error)

    get_error.short_description = 'error'
    get_error.allow_tags = True

    def __str__(self):
        return self.title
