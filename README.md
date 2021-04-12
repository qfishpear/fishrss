# irssi增强脚本和自动拉黑脚本
本脚本主要目的是对irssi拿到的种子进行额外的过滤以及智能使用令牌，目前仅适用于dic和red，对bt客户端没有要求
自动拉黑脚本仅支持red(dic懒得写了，反正应该用不到)且仅支持deluge客户端
所有涉及到筛选的逻辑（选种，ban人，使用令牌）可用的逻辑我写的比较简略，如果大家有建议或者需求可以告诉我我加进去，当然，选种部分的筛选逻辑其实许多完全可以在irssi里筛过了，其实我写的有点多余哈哈。

## 功能
有以下主要功能
* 对irssi或者别的方式得到的种子进行个性化过滤，目前支持按体积/发行类别/格式来过滤，并支持根据拉黑列表过滤发布者，
* 根据体积限制对符合要求的种子使用令牌
* 自动拉黑低分享率种子的发布者(仅针对red)

## 原理
种子里的comment信息中有种子的torrentid，根据这个id调用网站api查询完整的信息，然后进行过滤，由于调用api需要时间所以会比纯irssi有更多延迟

通过检查deluge客户端获取种子的ratio，对比api得到的发布者信息进行自动拉黑

## 依赖
仅支持python3，安装依赖：
```
pip3 install bencode.py ipython requests datasize deluge-client ipython
```

## 种子过滤
首先你需要将config.py.example复制一份为config.py然后按照里面的提示填写，并创建好所有已填写的文件/文件夹，然后运行
```
python3 filter.py
```
即可，这个过滤脚本会持续监控指定文件夹，然后将满足过滤条件的种子保存到另一个指定文件夹下。监控文件夹下的种子被检查后会被删除。为了缓解黑屏焦虑症，这个脚本每分钟会输出一行"tick"

部分log节选（隐私已去除）：
```
2021-04-12 18:28:37,392 - INFO - api and filter of RED are set
2021-04-12 18:28:37,392 - INFO - api and filter of DIC are set
......
2021-04-12 19:04:14,717 - INFO - new torrent from red: xxxxxxxxxxxxxxxxx
2021-04-12 19:04:14,718 - INFO - red querying action=torrent&id=xxxxxxxxxxxxxxxxx
2021-04-12 19:04:15,465 - INFO - redfilter: checking
2021-04-12 19:04:15,465 - INFO - uploader: xxxxxxxxxxxxxxxxx media: CD format: FLAC releasetype: 9 size: 114.9MB
2021-04-12 19:04:15,465 - INFO - reject: banned user
2021-04-12 19:04:22,676 - INFO - tick
2021-04-12 19:04:52,522 - INFO - new torrent from red: xxxxxxxxxxxxxxxxx
2021-04-12 19:04:52,523 - INFO - red querying action=torrent&id=xxxxxxxxxxxxxxxxx
2021-04-12 19:04:53,428 - INFO - redfilter: checking
2021-04-12 19:04:53,428 - INFO - uploader: xxxxxxxxxxxxxxxxx media: CD format: FLAC releasetype: 1 FLAC size: 224.7MB
2021-04-12 19:04:53,429 - INFO - accept
2021-04-12 19:05:23,673 - INFO - tick
2021-04-12 19:06:23,760 - INFO - tick
2021-04-12 19:07:23,858 - INFO - tick
2021-04-12 19:08:23,944 - INFO - tick
2021-04-12 19:09:24,031 - INFO - tick
```

## 自动拉黑
同样需要编辑config.py中相关的部分，设定拉黑条件，然后运行
```
python3 autoban.py
```
这个只会运行一次，要持续拉黑请自己设定crontab/watch

部分log节选（隐私已去除）
```
2021-04-12 15:47:42,277 - INFO - is connected: True
2021-04-12 15:47:42,651 - INFO - new user banned: xxxxx #torrents: 1 ratio: 0.044 0.008GB/0.187GB
2021-04-12 15:47:42,651 - INFO - 15 user banned in total
```