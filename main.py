import json
import requests
from bs4 import BeautifulSoup as BS
import time
import os


def try_get(url: str, headers, proxies):
    ret = None
    for _i in range(10):
        try:
            ret = requests.get(url, headers=headers, proxies=proxies)
        except Exception:
            time.sleep(1)
            continue
        else:
            break
    return ret


def save_image(img_id, user_id, tot_img, num, mode: str, settings, order=""):
    img_url = f"https://www.pixiv.net/artworks/{img_id}"
    img_resp = try_get(img_url, headers=settings["headers"], proxies=settings["proxies"])
    if img_resp.status_code != 200:
        return

    img_soup = BS(img_resp.text, 'lxml')
    img_info = json.loads(img_soup.find('meta', {'name': 'preload-data'}).get('content'))
    img_ori = img_info['illust'][str(img_id)]['urls']['original']

    img_page_cnt = img_info['illust'][str(img_id)]['pageCount']
    save_name = img_info['illust'][str(img_id)]['illustTitle']

    for i in range(img_page_cnt):
        if i > 0:
            img_ori = img_ori.replace(img_id + '_p' + str(i - 1), img_id + '_p' + str(i))

        time.sleep(1)
        img_down = try_get(img_ori, headers={
            "user-agent": settings['headers']['user-agent'],
            "referer": "https://www.pixiv.net/"}, proxies=settings["proxies"])
        if img_down.status_code != 200:
            break

        path = f'./download/{mode}/{user_id}/{order}{save_name}_{img_id}'
        img_file = f'{img_id}_p{i}.jpg'

        if not os.path.exists(path):
            os.makedirs(path)
        with open(f'{path}/{img_file}', 'wb') as f:
            f.write(img_down.content)
            print(f'{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())} '
                  f'Saved Successfully: {img_file}'
                  f'  \t[{num + 1}/{tot_img}]\t[{i + 1}/{img_page_cnt}]')


def save_ser(ser_id, user_id, ser_tot, num, ser_title):
    ser_url = f"https://www.pixiv.net/ajax/series/{ser_id}?p={num // 12 + 1}&lang=zh"
    ser_resp = try_get(ser_url, settings['headers'], settings['proxies'])
    for num in range(num, ser_tot):
        if num % 12 == 0:
            ser_url = f"https://www.pixiv.net/ajax/series/{ser_id}?p={num // 12 + 1}&lang=zh"
            ser_resp = try_get(ser_url, settings['headers'], settings['proxies'])
        wk_ids = ser_resp.json()['body']['page']['series']
        i = num % 12
        save_image(wk_ids[i]['workId'], user_id, ser_tot, num, "user", settings,
                   f"{ser_title}_{ser_id}/{str(wk_ids[i]['order']).zfill(len(str(ser_tot)))}.")


def download_bk(user_id, settings):
    bk_url = f"https://www.pixiv.net/ajax/user/{user_id}/illusts/bookmarks?tag=&offset=0&limit=48&rest=show&lang=zh"
    resp = try_get(bk_url, headers=settings["headers"], proxies=settings["proxies"])

    tot_img = resp.json()["body"]["total"]
    saved_tot = settings['start']

    for ot in range(saved_tot, tot_img, 48):
        bk_url = \
            f"https://www.pixiv.net/ajax/user/{user_id}/illusts/bookmarks?tag=&offset={ot}&limit=48&rest=show&lang=zh"
        resp = try_get(bk_url, headers=settings["headers"], proxies=settings["proxies"])

        works = resp.json()["body"]["works"]
        for img in works:
            save_image(img['id'], user_id, tot_img, saved_tot, "bookmark", settings)
            settings['start'] = saved_tot
            with open("settings.json", 'w') as f:
                json.dump(settings, f)
            saved_tot += 1


def download_user(user_id, settings):
    wk_url = f"https://www.pixiv.net/ajax/user/{user_id}/profile/all?lang=zh"
    resp = try_get(wk_url, headers=settings['headers'], proxies=settings['proxies'])

    saved_tot = settings['start']

    img_ids = list(resp.json()['body']['illusts'].keys()) + list(resp.json()['body']['manga'].keys())
    for saved_tot in range(saved_tot, len(img_ids)):
        save_image(img_ids[saved_tot], user_id, len(img_ids), saved_tot, "user", settings)
        settings['start'] = saved_tot
        with open("settings.json", 'w') as f:
            json.dump(settings, f)

    ser_start = settings['ser_start']
    ser_img = list(resp.json()['body']['mangaSeries'])
    for ser_num in range(ser_start['global'], len(ser_img)):
        ser_id = ser_img[ser_num]['id']
        ser_tot = ser_img[ser_num]['total']
        ser_title = ser_img[ser_num]['title']

        save_ser(ser_id, user_id, ser_tot, ser_start['detail'], ser_title)

        ser_start['global'] = ser_num
        ser_start['detail'] = 0
        with open("settings.json", 'w') as f:
            json.dump(settings, f)
        # ser_url = f"https://www.pixiv.net/ajax/series/{ser_id}?p={(ser_start['detail'] // 12) + 1}&lang=zh"


if __name__ == '__main__':
    with open("settings.json") as f:
        settings = json.load(f)

    user_id = settings.get("user_id")

    mode = "user"
    if mode == "bookmark":
        download_bk(user_id, settings)
    elif mode == "user":
        download_user(user_id, settings)
