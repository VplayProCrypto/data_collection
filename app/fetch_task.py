import schedule
import time

from orm.initialize_functions import add_all_collections

def main():
    file_path = 'games.json'
    max_workers = 4
    schedule.every(5).minutes.do(add_all_collections, file_path, max_workers)

    while True:
        print('pending')
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
