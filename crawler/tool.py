import json
from pathlib import Path

import requests
import logging
import time


def try_get(args, url: str, headers) -> requests.Response:
    """Try 10 times to get the response of the url."""
    ret = None
    i = 0
    while i < 10:
        i += 1
        if args.proxy_pool != "":
            if args.proxy_count >= 20:
                get_proxy(args)
                args.proxy_count = 0
                i = 0

        time.sleep(args.sleep_time)
        try:
            ret = requests.get(url, headers=headers, proxies=args.proxies)
            print(args.proxies)
            if ret.status_code != 200:
                continue
        except Exception:
            args.proxy_count += 5
            continue
        else:
            break
    return ret


def create_logger() -> logging.Logger:
    """Return a logger write to console and file at the same time."""
    fmt = '%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s'
    datefmt = '%Y-%m-%d %H:%M:%S'
    level = logging.INFO

    formatter = logging.Formatter(fmt, datefmt)
    logger = logging.getLogger()
    logger.setLevel(level)

    file = logging.FileHandler("pixiv.log", encoding='utf-8')
    file.setLevel(level)
    file.setFormatter(formatter)
    logger.addHandler(file)

    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(formatter)
    logger.addHandler(console)

    return logger


def save_info(obj_path: Path, obj_id: int, obj_info: dict):
    """Save Object's info to given path."""
    if not obj_path.exists():
        obj_path.mkdir(parents=True, exist_ok=True)
    with open(obj_path / f"{str(obj_id)}_info.json", 'w') as f:
        json.dump(obj_info, f)


def get_proxy(args):
    proxy = requests.get(args.proxy_pool).json()
    args.proxies = {
        'https': proxy['proxy'],
        'http': proxy['proxy']
    }
    return


def clear_json(args):
    for file in Path(args.path).resolve().rglob("*.json"):
        if file == Path("settings.json").resolve():
            continue
        file.unlink()
