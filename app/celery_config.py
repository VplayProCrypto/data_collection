from celery import Celery

# celery_app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

celery_app = Celery(
    'tasks',
    broker='sqla+postgresql://postgres:postgres@localhost/celerydb',  # PostgreSQL as broker
    backend='db+postgresql://postgres:postgres@localhost/celerydb',   # PostgreSQL as backend
    include = ['orm.initialize_functions']
)

# celery_app.conf.update(
#     result_expires=3600,
#     timezone='UTC',
# )

celery_app.conf.beat_schedule = {
    'fetch-every-5-minutes': {
        'task': 'orm.initialize_functions.add_all_collections',
        'schedule': 300.0,  # 5 minutes
        'args': ('games.json',),
    },
}

celery_app.conf.timezone = 'UTC'