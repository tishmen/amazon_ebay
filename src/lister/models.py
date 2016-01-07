import json

from django.db import models

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
            return
        if len(self.image_list) < MIN_AMAZON_ITEM_IMAGE_COUNT:
            return
        if self.review_count < MIN_AMAZON_ITEM_REVIEW_COUNT:
            return
        if self.review_count > MAX_AMAZON_ITEM_REVIEW_COUNT:
            return
        return True

    def __str__(self):
        return self.title
