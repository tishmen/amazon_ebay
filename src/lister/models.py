import json
import logging

from django.db import models

logger = logging.getLogger(__name__)

MIN_AMAZON_ITEM_PRICE = 35
MIN_AMAZON_ITEM_IMAGE_COUNT = 2
MIN_AMAZON_ITEM_REVIEW_COUNT = 10
MAX_AMAZON_ITEM_REVIEW_COUNT = 30


class ArrayField(models.TextField):

    def get_prep_value(self, value):
        return json.dumps(value)

    def to_python(self, value):
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

    url = models.URLField(unique=True)
    title = models.TextField()
    feature_list = ArrayField()
    image_list = ArrayField(verbose_name='list of images')
    price = models.FloatField()
    manufacturer = models.TextField(null=True)
    mpn = models.TextField(null=True)
    review_count = models.PositiveIntegerField(
        verbose_name='number of reviews'
    )
    date_added = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        if self.price < MIN_AMAZON_ITEM_PRICE:
            logger.info(
                'Less than minimum amazon item price {} for item {} with price'
                ' {}'.format(MIN_AMAZON_ITEM_PRICE, self.title, self.price)
            )
            return
        if len(self.image_list) < MIN_AMAZON_ITEM_IMAGE_COUNT:
            logger.info(
                'Less than minimum item image count {} for item {} with image '
                'count of {}'.format(
                    MIN_AMAZON_ITEM_IMAGE_COUNT, self.title,
                    len(self.image_list)
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

    url_.short_description = 'url'
    url_.allow_tags = True
    url_.admin_order_field = 'url'
