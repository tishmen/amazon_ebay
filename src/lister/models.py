import json

from django.db import models


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

    url = models.URLField()
    title = models.TextField()
    feature_list = ArrayField(verbose_name='list of features')
    image_list = ArrayField(verbose_name='list of images')
    price = models.DecimalField(max_digits=8, decimal_places=2)
    manufacturer = models.TextField(null=True)
    model = models.TextField(null=True)
    review_count = models.PositiveIntegerField(verbose_name='number of reviews')
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
