"""
Main Celery App file

"""
from raven.contrib.celery import register_signal, register_logger_signal
import celery
import logging
import raven

from api_background import celeryconfig

# class Celery(celery.Celery):
#     def on_configure(self):
#         if config.sentry_dns:
#             client = raven.Client(config.sentry_dns)
#             # register a custom filter to filter out duplicate logs
#             register_logger_signal(client)
#             # hook into the Celery error handler
#             register_signal(client)

logging.getLogger().setLevel(logging.INFO)
app = celery.Celery()
app.conf.task_default_queue = 'api_background'
app.config_from_object(celeryconfig)

import api_background.export_data

if __name__ == "__main__":
    app.start()
# @task
# def cleanup_downloads():
#     folder = '/var/www/meerkat_api/api_background/api_background/exported_data'
#     downloads = os.listdir(folder)
#     oldest = time.time() - 3600
#     for download in downloads:
#         path = '{}/{}'.format(folder, download)
#         if os.stat(path).st_mtime < oldest:
#             try:
#                 shutil.rmtree(path)
#             except NotADirectoryError:
#                 pass
