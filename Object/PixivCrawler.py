import json
import logging
import time
from json import JSONDecodeError
from pathlib import Path
from bs4 import BeautifulSoup as BS

import requests


class PixivCrawler:
    def __init__(self, user_id: str = "", series_id: str = "", mode: str = "", path: str = "./download",
                 sleep_time: float = 1.0, proxy_pool: str = "", expire: int = 24, clear: bool = False,
                 headers: dict = None, proxies: dict = None):
        """
        user_id: User ID to download bookmark, series or works.
        series_id: ID of MangaSeries to download.
        mode["bookmark", "user", "series"]: Crawler mode.
        path: Path to Save images.
        sleep_time: Sleep time between each get.
        proxy_time: Use proxy_pool from the given url.
        expire: Update info after how many hours.
        clear: Clear json files or not.
        """
        self.proxy_count = None
        if headers is None:
            headers = {}
        if proxies is None:
            proxies = {}
        self.user_id = user_id
        self.series_id = series_id
        self.mode = mode
        self.path = Path(path)
        self.sleep_time = sleep_time
        self.proxy_pool = proxy_pool
        self.expire = expire
        self.clear = clear
        self.headers = headers
        self.proxies = proxies

    def _creat_logger_(self):
        """Return a logger write to console and file at the same time."""
        fmt = '%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s'
        datefmt = '%Y-%m-%d %H:%M:%S'
        level = logging.INFO

        formatter = logging.Formatter(fmt, datefmt)
        logger = logging.getLogger()
        logger.setLevel(level)

        file = logging.FileHandler(Path(self.path) / "pixiv.log", encoding='utf-8')
        file.setLevel(level)
        file.setFormatter(formatter)
        logger.addHandler(file)

        console = logging.StreamHandler()
        console.setLevel(level)
        console.setFormatter(formatter)
        logger.addHandler(console)

        self.logger = logger

    def _try_get_(self, url, headers):
        """Try 10 times to get the response of the url."""
        ret = None
        i = 0
        while i < 10:
            i += 1
            if self.proxy_pool != "":
                if self.proxy_count >= 20:
                    self._get_proxy_()
                    self.proxy_count = 0
                    i = 0

            time.sleep(self.sleep_time)
            try:
                ret = requests.get(url, headers=headers, proxies=self.proxies)
                if ret.status_code != 200:
                    continue
            except Exception:
                if self.proxy_pool != "":
                    self.proxy_count += 5
                continue
            else:
                break
        return ret

    def _get_proxy_(self):
        proxy = requests.get(self.proxy_pool).json()
        if proxy.get("code", 1):
            return False
        self.proxies["http"] = proxy['proxy']
        if proxy["https"]:
            self.proxies["https"] = proxy['proxy']
        return True

    def _clear_json_(self):
        for file in Path(self.path).resolve().rglob("*.json"):
            if file == Path("settings.json").resolve():
                continue
            file.unlink()

    # region Save Image
    def get_info(self, img_id, img_path) -> dict:
        """Get image info from file or url."""
        try:
            return self.get_info_local(img_path / f"{str(img_id)}_info.json")
        except (JSONDecodeError, FileNotFoundError):
            url = f"https://www.pixiv.net/artworks/{img_id}"
            resp = self._try_get_(url, headers=self.headers)

            soup = BS(resp.text, 'lxml')
            return json.loads(soup.find('meta', {'name': 'preload-data'}).get('content'))

    def save_img(self, img_path: Path, img_id: int, log: str = ""):
        """Save image to the given path."""
        img_info = self.get_info(img_id, img_path)
        self.save_info(img_path, img_id, img_info)

        url_ori = img_info['illust'][str(img_id)]['urls']['original']
        img_page_cnt = img_info['illust'][str(img_id)]['pageCount']

        for i in range(img_page_cnt):
            if i > 0:
                url_ori = url_ori.replace(f"{str(img_id)}_p{str(i - 1)}", f"{str(img_id)}_p{str(i)}")

            img_filename = Path(url_ori).name
            if (img_path / img_filename).is_file():
                self.logger.info(f"{log}[{str(i + 1).zfill(2)}/{str(img_page_cnt).zfill(2)}] "
                                 f"Image {img_filename} has already been downloaded.")
                continue

            img_down = self._try_get_(url_ori, headers={
                "user-agent": self.headers['user-agent'],
                "referer": "https://www.pixiv.net/"})

            with open(img_path / img_filename, 'wb') as f:
                f.write(img_down.content)
                self.logger.info(f"{log}[{str(i + 1).zfill(2)}/{str(img_page_cnt).zfill(2)}] "
                                 f"Image {img_filename} is downloaded successfully.")

    def save_gif(self, img_path: Path, img_id: int, log: str = ""):
        """Save every frame of the GIF as a compressed to the given path."""
        img_info = self.get_info(img_id, img_path)
        self.save_info(img_path, img_id, img_info)

        url = f"https://www.pixiv.net/ajax/illust/{img_id}/ugoira_meta?lang=zh"
        resp = self._try_get_(url, self.headers)

        url_ori = resp.json()["body"]["originalSrc"]
        gif_filename = Path(url_ori).name

        if (img_path / gif_filename).is_file():
            self.logger.info(f"{log}[01/01] GIF Compressed {gif_filename} has already been downloaded.")
            return

        gif_down = self._try_get_(url_ori, headers={
            "user-agent": self.headers['user-agent'],
            "referer": f"https://www.pixiv.net/member_illust.php?mode=medium&illust_id={img_id}"})

        with open(img_path / gif_filename, 'wb') as f:
            f.write(gif_down.content)
            self.logger.info(f"{log}GIF Compressed {gif_filename} is downloaded successfully.")

    # endregion

    # region Info Tools
    def save_info(self, obj_path: Path, obj_id: int, obj_info: dict):
        """Save Object's info to given path."""
        if not obj_path.exists():
            obj_path.mkdir(parents=True, exist_ok=True)
        with open(obj_path / f"{str(obj_id)}_info.json", 'w') as f:
            json.dump(obj_info, f)

    def get_info_local(self, path: Path):
        """Get info from local path."""
        if (time.time() - path.stat().st_mtime) >= self.expire * 3600:
            raise FileNotFoundError
        with open(path) as f:
            return json.load(f)

    # endregion

    def start(self):
        self._creat_logger_()

        self.logger.info("Begin crawling ...")

        if self.proxy_pool != "":
            self.proxy_count = 0
            while not self._get_proxy_():
                self._get_proxy_()
        if self.mode == "bookmark":
            self.download_bookmark()
        elif self.mode == "user":
            self.download_user()
        elif self.mode == "series":
            self.download_series()

        self.logger.info("Crawl successfully.")

        if self.clear:
            self.logger.info("Begin cleaning json ...")
            self._clear_json_()
            self.logger.info("Clean json successfully.")

    # region Download Mode
    def download_bookmark(self):
        """Download all works in the bookmark of the user given by user id."""
        if not self.user_id.isdigit():
            self.logger.error(f"User id \"{self.user_id}\" is Invalid.")
            return

        url = f"https://www.pixiv.net/ajax/user/{self.user_id}/illusts/" \
              f"bookmarks?tag=&offset=0&limit=48&rest=show&lang=zh"
        resp = self._try_get_(url, self.headers)

        tot_img = resp.json()["body"]["total"]
        num_img = 0

        for offset in range(0, tot_img, 48):
            url = f"https://www.pixiv.net/ajax/user/{self.user_id}/illusts/" \
                  f"bookmarks?tag=&offset={offset}&limit=48&rest=show&lang=zh"
            resp = self._try_get_(url, self.headers)

            works = resp.json()["body"]["works"]
            for img in works:
                num_img += 1
                log = f"[{num_img}/{tot_img}] "
                if not img["isBookmarkable"]:
                    self.logger.warning(f"{log}Work {img['id']} is Deleted or Private.")
                    continue

                img_path = (Path(self.path) / "bookmark" / self.user_id / img["id"]).resolve()
                if img["illustType"] == 2:
                    self.save_gif(img_path, img['id'], log)
                else:
                    self.save_img(img_path, img['id'], log)

    def download_user(self):
        """Download all works of given user to given path"""
        if not self.user_id.isdigit():
            self.logger.error(f"User id \"{self.user_id}\" is Invalid.")
            return

        path = (Path(self.path) / "user" / self.user_id).resolve()

        try:
            user_info = self.get_info_local(path / f"{self.user_id}_info.json")
        except (JSONDecodeError, FileNotFoundError):
            url = f"https://www.pixiv.net/ajax/user/{self.user_id}/profile/all?lang=zh"
            resp = self._try_get_(url, headers=self.headers)
            user_info = resp.json()['body']
            self.save_info(path, int(self.user_id), user_info)

        img_ids = []
        if len(user_info['illusts']) > 0:
            img_ids += user_info['illusts'].keys()
        if (len(user_info['manga'])) > 0:
            img_ids += list(user_info['manga'].keys())
        for num in range(len(img_ids)):
            self.save_img(path / str(img_ids[num]), img_ids[num], f"[{num + 1}/{len(img_ids)}] ")

        ser_ids = list(user_info['mangaSeries'])
        for num in range(len(ser_ids)):
            self.series_id = ser_ids[num]['id']
            self.download_series(path / "Series" / str(ser_ids[num]['id']), f"[{num + 1}/{len(ser_ids)}] ")

    def download_series(self, ser_path: Path = "", log: str = ""):
        """Download all works in the given series to ser_path."""
        if not self.series_id.isdigit():
            self.logger.error(f"Series id \"{self.series_id}\" is Invalid.")
            return
        if not self.user_id.isdigit():
            self.logger.error(f"User id \"{self.user_id}\" is Invalid.")
            return

        if ser_path == "":
            ser_path = (Path(self.path) / "MangaSeries" / self.series_id).resolve()

        referer = f"https://www.pixiv.net/user/{self.user_id}/series/{self.series_id}"
        url = f"https://www.pixiv.net/ajax/series/{self.series_id}?p=1&lang=zh"
        resp = self._try_get_(url, {**self.headers, **{"referer": referer}})
        resp_info = resp.json()["body"]
        tot_img = resp_info["page"]["total"]

        try:
            ser_info = self.get_info_local(ser_path / f"{self.series_id}_info.json")
        except (JSONDecodeError, FileNotFoundError):
            ser_info = resp.json()["body"]
            self.save_info(ser_path, int(self.series_id), ser_info)

        for num_img in range(tot_img):
            if num_img != 0 and num_img % 12 == 0:
                url = f"https://www.pixiv.net/ajax/series/{self.series_id}?p={num_img // 12 + 1}&lang=zh"
                resp = self._try_get_(url, {**self.headers, **{"referer": referer}})
                resp_info = resp.json()["body"]

            num_in_page = num_img % 12
            works = resp_info['page']['series']
            img_id = works[num_in_page]['workId']
            if works[num_in_page] not in ser_info['page']['series']:
                ser_info['page']['series'].append(works[num_in_page])
                self.save_info(ser_path, int(self.series_id), ser_info)
            zfill_length = max(2, len(str(tot_img)))
            self.save_img(ser_path / str(img_id), img_id,
                          f"{log}[{str(num_img + 1).zfill(zfill_length)}/{str(tot_img).zfill(zfill_length)}] ")
    # endregion
