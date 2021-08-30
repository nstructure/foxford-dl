import requests, m3u8, shutil, time, sys
import concurrent.futures, subprocess

from tqdm import tqdm
from pathlib import Path
from urllib3.util.retry import Retry
from ._utils import TimeoutHTTPAdapter
from ._const import REFRESH_API, HEADERS, CONTENT


class Session(object):
    def __init__(self):
        self._refresh_token = None
        self._access_token = None
        self._access_token_expiration = 0

        self._session = requests.Session()
        retries = Retry(total=3, backoff_factor=4, status_forcelist=[429, 500, 502, 503, 504])
        self._session.mount("https://", adapter=TimeoutHTTPAdapter(max_retries=retries))
        self._session.headers.update(HEADERS)

        self._executor = concurrent.futures.ThreadPoolExecutor()
    
    def _revoke_access_token(self):
        if time.time() > self._access_token_expiration:
            res = self._session.post(
                REFRESH_API,
                headers={
                    'Authorization': self._refresh_token
                }
            )
            self._access_token = res.json().get('access_token')
            self._access_token_expiration = time.time() + 270

class PresentationDownloader(Session):
    def __init__(self) -> None:
        super().__init__()
        self._file_id = None
        self._webinar_scope = None
        
    
    def download(self, filepath):
        if not self._file_id or not self._webinar_scope:
            return
        filepath = Path(filepath).with_suffix('.pdf')
        filepath.parent.mkdir(parents=True, exist_ok=True)

        self._revoke_access_token()
        headers = {'Authorization': f'Bearer {self._access_token}'}

        res = self._session.get(
            CONTENT.format(scope=self._webinar_scope, filename=self._file_id),
            headers=headers,
            stream=True
        )
        
        if res.status_code == 200:
            with open(filepath, 'wb') as f:
                shutil.copyfileobj(res.raw, f)
            return filepath
        else:
            print("Не удалось скачать презентацию")
        

class StreamDownloader(Session):
    def __init__(self):
        super().__init__()
        self._video = None
        self._audio = None

        self._is_kinescope = None

    def _fetch_playlist(self, url):
        headers = {}
        if not self._is_kinescope:
            self._revoke_access_token()
            headers = {'Authorization': f'Bearer {self._access_token}'}

        res = self._session.get(
            url,
            headers=headers
        )

        playlist = m3u8.loads(res.text, uri=url)
        playlist = [segment.absolute_uri for segment in playlist.segments]

        return playlist
    
    def _dump_segment(self, segment_url, temp_dir):
        headers = {}
        if not self._is_kinescope:
            self._revoke_access_token()
            headers = {'Authorization': f'Bearer {self._access_token}'}
    
        filename = segment_url[segment_url.rfind('/')+1:]
        filepath = Path(f'{temp_dir}/{filename}')

        res = self._session.get(
            segment_url,
            stream=True,
            headers=headers
        )

        if res.status_code == 200:
            with open(filepath, 'wb') as f:
                shutil.copyfileobj(res.raw, f)
            return filepath
        else:
            print(f'Не удалось скачать сегмент {filename}')

    def _start_dumping(self, playlist: list, temp_dir, desc='Stream'):
        futures = []
        results = []

        with tqdm(
            desc=desc,
            total=len(playlist),
            bar_format='{desc}: {percentage:3.0f}%|{bar}| [{n_fmt}/{total_fmt}]'
        ) as progress:

            for segment in playlist:
                future = self._executor.submit(self._dump_segment, segment, temp_dir)
                future.add_done_callback(lambda p: progress.update())
                futures.append(future)
            
            results = [future.result() for future in futures]

        return results
    
    def _concat_segments(self, files: list, filepath):
        with open(filepath, 'wb') as outfile:
            for file in files:
                with open(file, 'rb') as readfile:
                    shutil.copyfileobj(readfile, outfile)

    def _merge_video_audio(self, inputs, output_filepath):
    
        def flatten(l):
            rt = []
            for i in l:
                if isinstance(i, list): rt.extend(flatten(i))
                else: rt.append(i)
            return rt

        args = []
        for i in inputs:
            args.extend(['-i', str(i)])

        command = [
            'ffmpeg',
            args,
            '-c',
            'copy',
            f'{output_filepath}',
            '-y'
        ]

        result = -1
        try:
            ffmpeg = subprocess.Popen(
                flatten(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            ffmpeg.communicate(timeout=180)
            result = ffmpeg.poll()
            ffmpeg.kill()
        except Exception:
            sys.stdout.write('[ffmpeg] не удалось запустить')
        return result

    def download(self, filepath='./test.mp4', temp_dir='./temp'):
        filepath = Path(filepath).with_suffix('.mp4')
        temp_dir = Path(temp_dir)

        video_filename = f'{filepath.stem}.ts'
        audio_filename = f'{filepath.stem}_audio.ts'
        
        video_filepath = temp_dir / video_filename
        audio_filepath = temp_dir / audio_filename

        filepath.parent.mkdir(parents=True, exist_ok=True)

        if temp_dir.is_dir(): shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        inputs = []
        try:
            if self._video:
                playlist = self._fetch_playlist(self._video)
                paths = self._start_dumping(playlist, temp_dir, 'Видео')
                self._concat_segments(paths, video_filepath)
                inputs.append(video_filepath)

            if self._audio:
                playlist = self._fetch_playlist(self._audio)
                paths = self._start_dumping(playlist, temp_dir, 'Аудио')
                self._concat_segments(paths, audio_filepath)
                inputs.append(audio_filepath)

            print(' > Слияние, transmuxing потоков...')
            merge_status = self._merge_video_audio(inputs, filepath)
            if merge_status != 0:
                sys.stdout.write('[ffmpeg] command error')
                for input in inputs:
                    shutil.move(input, filepath.parent)
            print(' > Скачивание завершено')
        except Exception:
            print(f'Не удалось скачать stream')
        
        self._executor.shutdown(wait=False)

        shutil.rmtree(temp_dir)
