import traceback

from celery import shared_task
from celery.utils.log import get_task_logger

from .utils import Amazon

logger = get_task_logger(__name__)


@shared_task(bind=True)
def search_task(self, queryset):
    logger.info('Starting Amazon search task')
    try:
        amazon = Amazon()
        amazon.search(queryset)
    except:
        logger.error(traceback.format_exc())
