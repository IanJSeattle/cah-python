import time
import logging

logger = logging.getLogger(__name__)

def logtime(func):
	def wrapper(*args, **kwargs):
		start = time.time()
		func(*args, **kwargs)
		end = time.time()
		logger.info('{}: {} sec'.format(func, end - start))
	return wrapper
