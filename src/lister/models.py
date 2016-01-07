import json
import logging
import traceback

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
    price = models.DecimalField(max_digits=8, decimal_places=2)
    manufacturer = models.TextField(null=True)
    mpn = models.TextField(null=True)
    review_count = models.PositiveIntegerField(verbose_name='number of reviews')
    date_added = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        if self.price < MIN_AMAZON_ITEM_PRICE:
            logger.info(
                'Less than minimum amazon item price {} for item {} with price {}'.format(
                    MIN_AMAZON_ITEM_PRICE, self.title, self.price
                )
            )
            return
        if len(self.image_list) < MIN_AMAZON_ITEM_IMAGE_COUNT:
            logger.info(
                'Less than minimum item image count {} for item {} with image count of {}'.format(
                    MIN_AMAZON_ITEM_IMAGE_COUNT, self.title, len(self.image_list)
                )
            )
            return
        if self.review_count < MIN_AMAZON_ITEM_REVIEW_COUNT:
            logger.info(
                'Less than minimum item review count {} for item {} with review count of '
                '{}'.format(MIN_AMAZON_ITEM_REVIEW_COUNT, self.title, self.review_count)
            )
            return
        if self.review_count > MAX_AMAZON_ITEM_REVIEW_COUNT:
            logger.info(
                'More than maximum allowed item review count {} for item {} with review count '
                '{}'.format(MAX_AMAZON_ITEM_REVIEW_COUNT, self.title, self.review_count)
            )
            return
        return True

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
            logger.info('Saved amazon item: {}'.format(self.title))
        except:
            logger.error(traceback.format_exc())
            logger.warn('Failed to save amazon item: {}'.format(self.title))

    def __str__(self):
        return self.title
