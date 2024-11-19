from celery import Celery
from app.keys import rabbitMQ_broker_url, timescale_url

# celery_app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

# celery_app = Celery(
#     'tasks',
#     broker='sqla+postgresql://postgres:postgres@localhost/celerydb',  # PostgreSQL as broker
#     backend='db+postgresql://postgres:postgres@localhost/celerydb',   # PostgreSQL as backend
#     include = ['orm.initialize_functions']
# )
celery_trait_app = Celery(
    'app.celery_config',
    broker=rabbitMQ_broker_url,  # RabbitMQ as broker
    backend=f'db+{timescale_url}',   # PostgreSQL as backend
    include=['app.orm.tasks']
)

celery_trait_app.conf.update(
    result_backend = f'db+{timescale_url}',
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    result_expire = 86400,
    task_acks_late=True,
)

# celery_trait_app.autodiscover_tasks(['app.orm'])
# celery_app.conf.update(
#     result_expires=3600,
#     timezone='UTC',
# )

# celery_app.conf.beat_schedule = {
#     'fetch-every-5-minutes': {
#         'task': 'orm.initialize_functions.add_all_collections',
#         'schedule': 300.0,  # 5 minutes
#         'args': ('games.json',),
#     },
# }

# celery_app.conf.timezone = 'UTC'