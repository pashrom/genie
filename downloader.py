import logging
import os
import time
from multiprocessing import Pool, cpu_count

import click
import requests
import tqdm
from requests import ConnectionError

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 1
RETRY_TIMEOUT = 10


class Downloader:
    def __init__(self, folder_path=None):
        self.folder_path = folder_path or self.get_output_folder()
        self.urls = self.get_urls()

    @staticmethod
    def get_urls():
        with open('urls.txt', 'r') as f:
            return f.read().replace('\n', ' ').split()

    @staticmethod
    def get_output_folder():
        default_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'output')
        os.makedirs(default_folder, exist_ok=True)
        return default_folder

    def get_file(self, url):
        for attempt in range(MAX_ATTEMPTS):
            try:
                r = requests.get(url)
                if r.status_code == 200:
                    file_name = url.split("/")[-1]
                    file_path = os.path.join(self.folder_path, file_name)
                    with open(file_path, 'wb') as f:
                        f.write(r.content)
                else:
                    logger.warning(f'Download failed for {url}, server responded with status code {r.status_code}: {r.reason}')
                break
            except ConnectionError as e:
                logger.warning(f'Attempt {attempt + 1} failed for {url} with error: {e}, will retry in {RETRY_TIMEOUT}s')
                time.sleep(RETRY_TIMEOUT)
        else:
            logger.error(f'Failed for {url} after {MAX_ATTEMPTS} attempts')

    def get_files(self):
        pool = Pool(cpu_count() - 1)
        try:
            for _ in tqdm.tqdm(pool.imap_unordered(self.get_file, self.urls), total=len(self.urls)):
                pass
        except KeyboardInterrupt:
            logger.info('Aborted by user')
            pool.terminate()


@click.command()
@click.argument('folder_path', required=False)
def main(folder_path=None):
    Downloader(folder_path).get_files()


if __name__ == '__main__':
    main()

