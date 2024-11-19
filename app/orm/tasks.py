import logging
from app.celery_config import celery_trait_app
from app.orm.postgres_injector_orm import Injector

# Set up a specific logger for task queueing logs
task_logger = logging.getLogger('nft_task_logger')

# Create a file handler for task-specific logs
task_handler = logging.FileHandler('nft_task_creation.log')  # Store logs in nft_task_creation.log
task_handler.setLevel(logging.INFO)

# Define a formatter for the task-specific logger
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
task_handler.setFormatter(formatter)

# Add the file handler to the specific task logger
task_logger.addHandler(task_handler)
task_logger.setLevel(logging.INFO)

# Disable propagation to prevent logs from going to the global logger
task_logger.propagate = False

@celery_trait_app.task()
def retrieve_missing_traits_celery(contract_address: str, token_id: str):
    injector = Injector()
    task_logger.info('Creating task. Inside task function')
    injector.retrieve_missing_traits(contract_address=contract_address, token_id = token_id)
    # Log success
    task_logger.info(f"Successfully processed NFT: contract_address={contract_address}, token_id={token_id}")
    del injector