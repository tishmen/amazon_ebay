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

    def image(self):
        return '<img src="{}" />'.format(to_list(self.image_list)[0])

    def price_(self):
        return '${}'.format(self.price)

    def feature_list_(self):
        feature_list = ''
        for feature in to_list(self.feature_list):
            if feature:
                feature_list += '{}\n'.format(feature)
        return feature_list.strip()

    def image_list_(self):
        image_list = ''
        for image in to_list(self.image_list):
            if image:
                image_list += (
                    '<a href="{0}" target="_blank">{0}</a><br>'.format(image)
                )
        return image_list[:-4]

    def url_(self):
        return '<a href="{0}" target="_blank">{0}</a>'.format(self.url)

    image_list_.allow_tags = True
    url_.short_description = 'url'
    url_.allow_tags = True
    url_.admin_order_field = 'url'


class ItemReview(models.Model):

    item = models.OneToOneField('AmazonItem')
    title = models.CharField(max_length=80, null=True)
    html = models.TextField(null=True)
    category = models.IntegerField(null=True)
    manufacturer = models.TextField(null=True)
    mpn = models.TextField(null=True)
    upc = models.CharField(max_length=12, null=True, blank=True)

    def __str__(self):
        return self.item.title
