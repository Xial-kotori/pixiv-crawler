import argparse
import json

from crawler.download_mode import download_bookmark, download_user, download_series
from crawler.tool import create_logger, get_proxy, clear_json

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--user_id", type=str, default="", help="User ID to download bookmark, series or works.")
    parser.add_argument("--series_id", type=str, default="", help="ID of MangaSeries to download.")

    parser.add_argument("--mode", type=str, default="bookmark", choices=["bookmark", "user", "series"],
                        help="Crawler mode.")

    parser.add_argument("--path", type=str, default="./download", help="Path to Save images.")
    parser.add_argument("--sleep_time", type=float, default=1, help="Sleep time between each get.")
    parser.add_argument("--proxy_pool", type=str, default="", help="Use proxy_pool from the given url.")
    parser.add_argument("--expire", type=float, default=24, help="Update info after how many hours.")

    parser.add_argument("--clear", action="store_true")

    args = parser.parse_args()

    with open("./settings.json") as f:
        settings = json.load(f)
        args.headers = settings["headers"]
        args.proxies = settings["proxies"]

    args.logger = create_logger()
    args.logger.info("Begin crawling ...")

    args.proxy_count = 0
    if args.proxy_pool != "":
        get_proxy(args)

    if args.mode == "bookmark":
        download_bookmark(args)
    elif args.mode == "user":
        download_user(args)
    elif args.mode == "series":
        download_series(args)

    args.logger.info("Crawl successfully.")

    if args.clear:
        args.logger.info("Begin cleaning json ...")
        clear_json(args)
        args.logger.info("Clean json successfully.")
