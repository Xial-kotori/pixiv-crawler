import json
import time
from json import JSONDecodeError

from crawler.save_image import save_img, save_gif
from crawler.tool import try_get, save_info, get_info_local
from pathlib import Path


def download_bookmark(args):
    """Download all works in the bookmark of the user given by user id."""
    if not args.user_id.isdigit():
        args.logger.error(f"User id \"{args.user_id}\" is Invalid.")
        return

    url = f"https://www.pixiv.net/ajax/user/{args.user_id}/illusts/" \
          f"bookmarks?tag=&offset=0&limit=48&rest=show&lang=zh"
    resp = try_get(args, url, args.headers)

    tot_img = resp.json()["body"]["total"]
    num_img = 0

    for offset in range(0, tot_img, 48):
        url = f"https://www.pixiv.net/ajax/user/{args.user_id}/illusts/" \
              f"bookmarks?tag=&offset={offset}&limit=48&rest=show&lang=zh"
        resp = try_get(args, url, args.headers)

        works = resp.json()["body"]["works"]
        for img in works:
            num_img += 1
            log = f"[{num_img}/{tot_img}] "
            if not img["isBookmarkable"]:
                args.logger.warning(f"{log}Work {img['id']} is Deleted or Private.")
                continue

            img_path = (Path(args.path) / "bookmark" / args.user_id / img["id"]).resolve()
            if img["illustType"] == 2:
                save_gif(args, img_path, img['id'], log)
            else:
                save_img(args, img_path, img['id'], log)


def download_user(args):
    """Download all works of given user to given path"""
    if not args.user_id.isdigit():
        args.logger.error(f"User id \"{args.user_id}\" is Invalid.")
        return

    path = (Path(args.path) / "user" / args.user_id).resolve()

    try:
        user_info = get_info_local(args, path / f"{args.user_id}_info.json")
    except (JSONDecodeError, FileNotFoundError):
        url = f"https://www.pixiv.net/ajax/user/{args.user_id}/profile/all?lang=zh"
        resp = try_get(args, url, headers=args.headers)
        user_info = resp.json()['body']
        save_info(path, args.user_id, user_info)

    img_ids = []
    if len(user_info['illusts']) > 0:
        img_ids += user_info['illusts'].keys()
    if (len(user_info['manga'])) > 0:
        img_ids += list(user_info['manga'].keys())
    for num in range(len(img_ids)):
        save_img(args, path / str(img_ids[num]), img_ids[num], f"[{num + 1}/{len(img_ids)}] ")

    ser_ids = list(user_info['mangaSeries'])
    for num in range(len(ser_ids)):
        args.series_id = ser_ids[num]['id']
        download_series(args, path / "Series" / str(ser_ids[num]['id']), f"[{num + 1}/{len(ser_ids)}] ")


def download_series(args, ser_path: Path = "", log: str = ""):
    """Download all works in the given series to ser_path."""
    if not args.series_id.isdigit():
        args.logger.error(f"Series id \"{args.series_id}\" is Invalid.")
        return
    if not args.user_id.isdigit():
        args.logger.error(f"User id \"{args.user_id}\" is Invalid.")
        return

    if ser_path == "":
        ser_path = (Path(args.path) / "MangaSeries" / args.series_id).resolve()

    referer = f"https://www.pixiv.net/user/{args.user_id}/series/{args.series_id}"
    url = f"https://www.pixiv.net/ajax/series/{args.series_id}?p=1&lang=zh"
    resp = try_get(args, url, {**args.headers, **{"referer": referer}})
    resp_info = resp.json()["body"]
    tot_img = resp_info["page"]["total"]

    try:
        ser_info = get_info_local(args, ser_path / f"{args.series_id}_info.json")
    except (JSONDecodeError, FileNotFoundError):
        ser_info = resp.json()["body"]
        save_info(ser_path, args.series_id, ser_info)

    for num_img in range(tot_img):
        if num_img != 0 and num_img % 12 == 0:
            url = f"https://www.pixiv.net/ajax/series/{args.series_id}?p={num_img // 12 + 1}&lang=zh"
            resp = try_get(args, url, {**args.headers, **{"referer": referer}})
            resp_info = resp.json()["body"]

        num_in_page = num_img % 12
        works = resp_info['page']['series']
        img_id = works[num_in_page]['workId']
        if works[num_in_page] not in ser_info['page']['series']:
            ser_info['page']['series'].append(works[num_in_page])
            save_info(ser_path, args.series_id, ser_info)
        zfill_length = max(2, len(str(tot_img)))
        save_img(args, ser_path / str(img_id), img_id,
                 f"{log}[{str(num_img + 1).zfill(zfill_length)}/{str(tot_img).zfill(zfill_length)}] ")
