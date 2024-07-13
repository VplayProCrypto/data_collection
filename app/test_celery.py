from celery_config import celery_app
celery_app.send_task('orm.initialize_functions.add_all_collections', args=['games.json'])
