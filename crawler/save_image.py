import json
from json import JSONDecodeError
from pathlib import Path
from bs4 import BeautifulSoup as BS

from crawler.tool import try_get, save_info, get_info_local


def get_info(args, img_id, img_path) -> dict:
    """Get image info from file or url."""
    try:
        return get_info_local(args, img_path / f"{str(img_id)}_info.json")
    except (JSONDecodeError, FileNotFoundError):
        url = f"https://www.pixiv.net/artworks/{img_id}"
        resp = try_get(args, url, headers=args.headers)

        soup = BS(resp.text, 'lxml')
        return json.loads(soup.find('meta', {'name': 'preload-data'}).get('content'))


def save_img(args, img_path: Path, img_id: int, log: str = ""):
    """Save image to the given path."""
    img_info = get_info(args, img_id, img_path)
    save_info(img_path, img_id, img_info)

    url_ori = img_info['illust'][str(img_id)]['urls']['original']
    img_page_cnt = img_info['illust'][str(img_id)]['pageCount']

    for i in range(img_page_cnt):
        if i > 0:
            url_ori = url_ori.replace(f"{str(img_id)}_p{str(i - 1)}", f"{str(img_id)}_p{str(i)}")

        img_filename = Path(url_ori).name
        if (img_path / img_filename).is_file():
            args.logger.info(f"{log}[{str(i + 1).zfill(2)}/{str(img_page_cnt).zfill(2)}] "
                             f"Image {img_filename} has already been downloaded.")
            continue

        img_down = try_get(args, url_ori, headers={
            "user-agent": args.headers['user-agent'],
            "referer": "https://www.pixiv.net/"})

        with open(img_path / img_filename, 'wb') as f:
            f.write(img_down.content)
            args.logger.info(f"{log}[{str(i + 1).zfill(2)}/{str(img_page_cnt).zfill(2)}] "
                             f"Image {img_filename} is downloaded successfully.")


def save_gif(args, img_path: Path, img_id: int, log: str = ""):
    """Save every frame of the GIF as a compressed to the given path."""
    img_info = get_info(args, img_id, img_path)
    save_info(img_path, img_id, img_info)

    url = f"https://www.pixiv.net/ajax/illust/{img_id}/ugoira_meta?lang=zh"
    resp = try_get(args, url, args.headers)

    url_ori = resp.json()["body"]["originalSrc"]
    gif_filename = Path(url_ori).name

    if (img_path / gif_filename).is_file():
        args.logger.info(f"{log}[01/01] GIF Compressed {gif_filename} has already been downloaded.")
        return

    gif_down = try_get(args, url_ori, headers={
        "user-agent": args.headers['user-agent'],
        "referer": f"https://www.pixiv.net/member_illust.php?mode=medium&illust_id={img_id}"})

    with open(img_path / gif_filename, 'wb') as f:
        f.write(gif_down.content)
        args.logger.info(f"{log}GIF Compressed {gif_filename} is downloaded successfully.")
