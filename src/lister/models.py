from __future__ import unicode_literals

import json
import logging

from django.contrib.auth.models import User
from django.db import models

logger = logging.getLogger(__name__)

MIN_AMAZON_ITEM_IMAGE_COUNT = 2
MIN_AMAZON_ITEM_PRICE = 35
MAX_AMAZON_ITEM_PRICE = 1000
MIN_AMAZON_ITEM_REVIEW_COUNT = 10
MAX_AMAZON_ITEM_REVIEW_COUNT = 30


def to_list(value):
    return json.loads(value)


class AmazonSearch(models.Model):

    query = models.CharField(max_length=100)
    date_searched = models.DateTimeField(null=True, blank=True)

    class Meta:

        verbose_name_plural = 'amazon searches'

    def __str__(self):
        return self.query


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
    review_count = models.PositiveIntegerField()
    date_added = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        if self.price < MIN_AMAZON_ITEM_PRICE:
            logger.info(
                'Less than minimum amazon item price {} for item {} with price'
                ' {}'.format(MIN_AMAZON_ITEM_PRICE, self.title, self.price)
            )
            return
        if self.price < MAX_AMAZON_ITEM_PRICE:
            logger.info(
                'More than minimum amazon item price {} for item {} with price'
                ' {}'.format(MIN_AMAZON_ITEM_PRICE, self.title, self.price)
            )
            return
        image_list = to_list(self.image_list)
        if len(image_list) < MIN_AMAZON_ITEM_IMAGE_COUNT:
            logger.info(
                'Less than minimum item image count {} for item {} with image '
                'count of {}'.format(
                    MIN_AMAZON_ITEM_IMAGE_COUNT, self.title,
                    len(image_list)
                )
            )
            return
        if self.review_count < MIN_AMAZON_ITEM_REVIEW_COUNT:
            logger.info(
                'Less than minimum item review count {} for item {} with revie'
                'w count of {}'.format(
                    MIN_AMAZON_ITEM_REVIEW_COUNT, self.title, self.review_count
                )
            )
            return
        if self.review_count > MAX_AMAZON_ITEM_REVIEW_COUNT:
            logger.info(
                'More than maximum allowed item review count {} for item {} wi'
                'th review count {}'.format(
                    MAX_AMAZON_ITEM_REVIEW_COUNT, self.title, self.review_count
                )
            )
            return
        return True

    def __str__(self):
        return self.title

    def url_(self):
        return '<a href="{0}" target="_blank">{0}</a>'.format(self.url)

    def title_(self):
        return '<a href="/admin/lister/amazonitem/{}/change/">{}</a>'.format(
            self.id, self.title
        )

    def price_(self):
        return '${}'.format(self.price)

    def image(self):
        return '<img src="{}" />'.format(to_list(self.image_list)[0])

    def feature_list_(self):
        feature_list = ''
        for feature in to_list(self.feature_list):
            if feature:
                feature_list += '{}\n'.format(feature)
        return feature_list.strip()

    def html(self):
        html = '<div id="ds_div">'\
            '<h1 class="p1" style="text-align: center;"><span class="s1"><str'\
            'ong>{}</strong></span></h1>'\
            '<h1 class="p2" style="text-align: center;"><span class="s1"><str'\
            'ong>Product Description:</strong></span></h1>'\
            '<h1><strong>&lt;Insert Description Here&gt;</strong></h1>'\
            '<p class="p2"><span class="s1"><strong>Features:</strong></span>'\
            '</p><ul class="ul1">'.format(self.title)
        for feature in to_list(self.feature_list):
            html += '<li class="li3"><span class="s1">{}</span></li>'.format(
                feature
            )
        html += '</ul><br></br><h2>Shipping / Return Policies (Balanced):</h2'\
            '><h3>Shipping Policies:</h3>'\
            '<ul><li>We ship to the Lower 48 States only (Does NOT include Ha'\
            'waii or Alaska)</li><li>'\
            'We cannot ship to PO Boxes/APO\'s</li><li>We cannot combine ship'\
            'ping.</li><li>No Local Pickup.</li></ul>'\
            '<p>All items will be shipped directly to you from our supplier w'\
            'ithin 1-3 business days. Most items are delivered within 3-5 bus'\
            'iness days, however, please allow 3-10 business days.</p>'\
            '<p>All items are in stock when they are listed. Inventory is tra'\
            'cked and updated regularly. However, if demand exceeds our suppl'\
            'y, we will give the customer the following options: Full refund.'\
            ' Have the item back ordered and shipped when it becomes availabl'\
            'e. We will offer other items in similar style and quality. Your '\
            'bid / purchase of the item implies you agree to this policy.</p>'\
            '<p>If you have a question about a product not otherwise answered'\
            ' in the item description, please contact us via eBay messages fi'\
            'rst and allow us the opportunity to help you and be sure we have'\
            ' what you\'re looking for.</p>'\
            '<h3>Exchange/Return Policy:</h3>'\
            '<p>Your satisfaction is guaranteed! If for any reason you are un'\
            'happy with your item, just return it within 14 days for a full r'\
            'efund, minus shipping cost. Please contact us prior to initiatin'\
            'g a return so that we can issue you a refund authorization.</p>'\
            '<h3>Payment Policy</h3>'\
            '<p>We require Immediate Payment. Must be an authorized address.'\
            '</p></div>'\
            '<p>Thank you for viewing the {}</p>'.format(self.title)
        return html

    url_.short_description = 'url'
    url_.allow_tags = True
    url_.admin_order_field = 'url'
    title_.allow_tags = True


class ItemReview(models.Model):

    item = models.OneToOneField('AmazonItem')
    title = models.CharField(max_length=80)
    html = models.TextField()
    category = models.IntegerField()
    manufacturer = models.CharField(max_length=65)
    mpn = models.CharField(max_length=65)
    upc = models.CharField(max_length=12, null=True, blank=True)
    is_listed = models.BooleanField(default=False)
    note = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.item.title
