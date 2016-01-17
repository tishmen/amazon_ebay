import traceback

from celery import shared_task
from celery.utils.log import get_task_logger

from .utils import Amazon, Ebay

logger = get_task_logger(__name__)


@shared_task(bind=True)
def search_task(self, queryset):
    try:
        logger.info('Starting Amazon search task')
        amazon = Amazon()
        if not amazon.connection:
            return
        for search_obj in queryset:
            amazon.search(search_obj)
        logger.info(
            'Saved total of {} Amazon items'.format(amazon.total_count)
        )
    except:
        logger.error(traceback.format_exc())


@shared_task(bind=True)
def list_task(self, queryset):
    try:
        logger.info('Starting Ebay list task')
        ebay = Ebay()
        if not (ebay.sandbox_connection or ebay.production_connection):
            return
        for item_obj in queryset:
            ebay.list(item_obj.ebayitem_set.all()[0])
        logger.info('Listed total of {} Ebay items'.format(ebay.total_count))
    except:
        logger.error(traceback.format_exc())
