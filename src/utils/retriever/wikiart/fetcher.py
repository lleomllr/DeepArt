"""WikiArt Retriever.

Author: Lucas David -- <ld492@drexel.edu>
License: MIT License (c) 2016

"""
import json
import os
import shutil
import time
import urllib.error
import urllib.request
import re
import csv
import requests

from . import settings, base
from .base import Logger


class WikiArtFetcher:
    """WikiArt Fetcher.

    Fetcher for data in WikiArt.org.
    """

    def __init__(self, commit=True, override=False, padder=None):
        self.commit = commit
        self.override = override
        self.padder = padder or base.RequestPadder()
        self.artists = None
        self.painting_groups = None

    def prepare(self):
        """Prepare for data extraction."""
        os.makedirs(settings.BASE_FOLDER, exist_ok=True)
        os.makedirs(os.path.join(settings.BASE_FOLDER, 'meta'), exist_ok=True)
        os.makedirs(os.path.join(settings.BASE_FOLDER, 'images'), exist_ok=True)
        return self

    def check(self, only='all'):
        """Check if fetched data is intact."""
        Logger.info('Checking downloaded data...')

        base_dir = settings.BASE_FOLDER
        meta_dir = os.path.join(base_dir, 'meta')
        imgs_dir = os.path.join(base_dir, 'images')

        if only in ('artists', 'all'):
            if not os.path.exists(os.path.join(meta_dir, 'artists.json')):
                Logger.warning('artists.json is missing.')

        if only in ('paintings', 'all'):
            for artist in self.artists:
                filename = os.path.join(meta_dir, artist['url'] + '.json')
                if not os.path.exists(filename):
                    Logger.warning('%s\'s paintings file is missing.' % artist['url'])

            for group in self.painting_groups:
                for painting in group:
                    filename = os.path.join(imgs_dir,
                                            str(painting['contentId']) +
                                            settings.SAVE_IMAGES_IN_FORMAT)
                    if not os.path.exists(filename):
                        Logger.warning('painting %i is missing.' % painting['contentId'])
        return self

    def getauthentication(self):
        """Fetch a session key from WikiArt."""
        params = {}
        params['accessCode'] = input('Please enter the Access code from https://www.wikiart.org/en/App/GetApi :')
        params['secretCode'] = input("Enter the Secret code :")
        url = 'https://www.wikiart.org/en/Api/2/login'

        try:
            response = requests.get(url,
                                    params=params,
                                    timeout=settings.METADATA_REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            return data['SessionKey']
        except Exception as error:
            Logger.write('Error %s' % str(error))

    def fetch_all(self):
        """Fetch Everything from WikiArt."""
        return (self.fetch_artists()
                    .fetch_all_paintings()
                    .copy_everything())

    def fetch_artists(self):
        """Retrieve Artists from WikiArt."""
        Logger.info('Fetching artists...', end=' ', flush=True)

        path = os.path.join(settings.BASE_FOLDER, 'meta', 'artists.json')
        if os.path.exists(path) and not self.override:
            with open(path, encoding='utf-8') as f:
                self.artists = json.load(f)
            Logger.info('skipped')
            return self

        elapsed = time.time()

        try:
            url = '/'.join((settings.BASE_URL, 'Artist/AlphabetJson'))
            params = {'v': 'new', 'inPublicDomain': 'true'}
            response = requests.get(url,
                                    timeout=settings.METADATA_REQUEST_TIMEOUT,
                                    params=params)
            response.raise_for_status()
            self.artists = response.json()

            if self.commit:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(self.artists, f, indent=4, ensure_ascii=False)

            Logger.write('Done (%.2f sec)' % (time.time() - elapsed))
        except Exception as error:
            Logger.write('Error %s' % str(error))
        return self

    def fetch_artist(self, artist_name):
        """Fetch Paintings Metadata for One Artist."""
        Logger.write(f'\nFetching paintings of artist: {artist_name} (this may take a while...)')
        if not self.artists:
            raise RuntimeError('No artists defined. Cannot continue.')

        self.painting_groups = []
        for artist in self.artists:
            if re.search(artist_name.lower(), artist['artistName'].lower()):
                self.painting_groups.append(self.fetch_paintings(artist))

        if not self.painting_groups:
            raise ValueError(f'Artist name "{artist_name}" not found. Cannot continue.')
        return self

    def fetch_all_paintings(self):
        """Fetch Paintings Metadata for Every Artist."""
        Logger.write('\nFetching paintings for every artist:')
        if not self.artists:
            raise RuntimeError('No artists defined. Cannot continue.')

        self.painting_groups = []
        show_progress_at = max(1, int(.1 * len(self.artists)))

        for i, artist in enumerate(self.artists):
            self.painting_groups.append(self.fetch_paintings(artist))
            if i % show_progress_at == 0:
                Logger.info('%i%% done' % (100 * (i + 1) // len(self.artists)))
        return self

    def fetch_paintings(self, artist):
        """Retrieve and Save Paintings Info from WikiArt."""
        Logger.write('|- %s\'s paintings' % artist['artistName'], end='', flush=True)
        elapsed = time.time()

        meta_folder = os.path.join(settings.BASE_FOLDER, 'meta')
        url = '/'.join((settings.BASE_URL, 'Painting', 'PaintingsByArtist'))
        params = {'artistUrl': artist['url'], 'json': 2}
        filename = os.path.join(meta_folder, artist['url'] + '.json')

        if os.path.exists(filename) and not self.override:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            Logger.write(' (s)')
            return data

        try:
            response = requests.get(url, params=params,
                                    timeout=settings.METADATA_REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            for painting in data:
                details_url = '/'.join((settings.BASE_URL, 'Painting', 'ImageJson',
                                        str(painting['contentId'])))
                self.padder.request_start()
                response = requests.get(details_url,
                                        timeout=settings.METADATA_REQUEST_TIMEOUT)
                self.padder.request_finished()

                if response.ok:
                    painting.update(response.json())

                Logger.write('.', end='', flush=True)

            if self.commit:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)

            Logger.write(' Done (%.2f sec)' % (time.time() - elapsed))
            return data

        except (IOError, urllib.error.HTTPError) as e:
            Logger.write(' Failed (%s)' % str(e))
            return []

    def copy_everything(self):
        """Download A Copy of Every Single Painting."""
        Logger.write('\nCopying paintings:')
        if not self.painting_groups:
            raise ValueError('Painting groups not found. Cannot continue.')

        for group in self.painting_groups:
            for painting in group:
                self.download_hard_copy(painting)
        return self

    def download_hard_copy(self, painting):
        """Download A Copy of A Painting with organized structure."""
        Logger.write('|- %s' % painting.get('url', painting.get('contentId')),
                     end=' ', flush=True)
        elapsed = time.time()
        url = painting['image']
        url = ''.join(url.split('!')[:-1])  # Remove "!Large.jpg"

        # Get metadata
        style = painting.get('style', 'unknownStyle') or 'unknownStyle'
        artist = painting.get('artistName', painting.get('artistUrl', 'unknownArtist')) or 'unknownArtist'
        title = painting.get('title', str(painting['contentId'])) or str(painting['contentId'])

        def safe(s):
            return ''.join(c for c in s if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')

        style = safe(style)
        artist = safe(artist)
        title = safe(title)
        if len(title) > 100:
            title = title[:100]

        filename = os.path.join(settings.BASE_FOLDER, 'dataset', style, artist, f"{title}.jpg")

        # Vérifier si présent dans le dataset 'raw'
        raw_path = os.path.join('raw', style, artist, f"{title}.jpg")
        if os.path.exists(raw_path):
            Logger.write('(already in raw dataset)')
            return self

        if os.path.exists(filename) and not self.override:
            Logger.write('(s)')
            return self

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        # Initialiser le CSV si nécessaire
        csv_path = os.path.join(settings.BASE_FOLDER, 'metadata.csv')
        if not os.path.exists(csv_path):
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['path', 'style', 'artist', 'title'])

        try:
            self.padder.request_start()
            response = requests.get(url, stream=True,
                                    timeout=settings.PAINTINGS_REQUEST_TIMEOUT)
            self.padder.request_finished()
            response.raise_for_status()

            with open(filename, 'wb') as f:
                response.raw.decode_content = True
                shutil.copyfileobj(response.raw, f)

            Logger.write(f'(saved {style}/{artist}/{title}.jpg)')

            # Ajouter au CSV
            with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([filename, style, artist, title])

        except Exception as error:
            Logger.write(f'Error: {error}')
            if os.path.exists(filename):
                os.remove(filename)

        return self
