# Pixiv Crawler

## 前言

某天发现 Pixiv 上自己收藏的某张图被原画师删了，于是想把自己的收藏都下载下来

但是

人类总是懒惰的，于是写了这么个爬虫帮我下载

## 简介

用来爬取 Pixiv 上指定的收藏夹，漫画系列或用户作品中的所有图片，（顺便还会爬个 json 下来，用来支持断点续传（？）

## 环境

python 版本用的 3.8

依赖可以用 `pip install -r requirements.txt` 安装

## 食用方法

首先在 `settings.json` 中设置 user-agent，cookie，和 proxies，示例见附录

在项目目录下使用命令行输入 `python main.py --options` 进行食用

选项说明：
```
usage: main.py [-h] [--user_id USER_ID] [--series_id SERIES_ID] [--mode {bookmark,user,series}] [--path PATH] [--sleep_time SLEEP_TIME] [--proxy_pool PROXY_POOL] [--clear]

optional arguments:
  -h, --help            show this help message and exit
  --user_id USER_ID     User ID to download bookmark, series or works.
  --series_id SERIES_ID
                        ID of MangaSeries to download.
  --mode {bookmark,user,series}
                        Crawler mode.
  --path PATH           Path to Save images.
  --sleep_time SLEEP_TIME
                        Sleep time between each get.
  --proxy_pool PROXY_POOL
                        Use proxy_pool from the given url.
  --clear
```

人话：

一共三个模式：（默认为 `bookmark`）

+ `bookmark` 模式，下载给定 user id 的用户的收藏夹中所有图
+ `user` 模式，下载给定 user id 的用户的所有作品（插画，漫画，漫画系列（其实漫画系列会重复
+ `series` 模式，下载给定 series id 的漫画系列

注意： series 模式下也需要指定该漫画系列作者的 id

其他选项：

+ `--path PATH` 存图的路径，默认为当前目录下的 `download` 文件夹
+ `--sleep_time SLEEP_TIME` 每两个网络请求之间的间隔时间，单位为秒(s)，默认为 `1.0`
+ `--proxy_pool PROXY_POOL` IP 池，为一个 url 链接，应满足通过 `GET` 请求时能返回一个 json 文件，格式要求见附录。
+ `--clear` 添加此选项后会删掉爬取过程中生成的所有 `json` 文件

## 附录

`settings.json` 样例：

```json
{
  "headers": {
    "user-agent": "Mozilla/5.0 (Linux; Android 10; SM-A205U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.69 Mobile Safari/537.36.",
    "cookie": "abaaba1145141919810..."
  },
  "proxies": {
    "https": "127.0.0.1:114514",
    "http": "127.0.0.1:114514"
  }
}
```

`PROXY_POOL` 返回样例：

```json
{
  "proxy": "114.51.41.91:9810"
}
```