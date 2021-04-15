# gazelle r种增强脚本
本脚本集合主要目的是增强gazelle站里r种刷流的体验

目前只支持海豚和red

## 功能
有以下主要功能
* 种子过滤。对irssi或者别的方式得到的种子进行个性化过滤，目前支持按体积/发行类别/格式来过滤，并支持根据拉黑列表过滤发布者，对bt客户端没有要求。
* 智能使用令牌。根据体积限制对符合要求的种子使用令牌
* 自动拉黑。自动拉黑低分享率种子的发布者，仅针对red，仅支持deluge
* deluge数据导出，方便分析刷流情况
* deluge删除网站上被删种的种子（unregistered torrents）

## 依赖
仅支持python3，安装依赖：
```
pip3 install bencode.py ipython requests datasize deluge-client
```

## 种子过滤

警告：种子过滤本身有延迟，所以如果发种人irssi发种或发光速种的话可能导致ratio颗粒无收，配置前请考虑清楚。

首先你需要将`config.py.example`复制一份为`config.py`
```
cp config.py.example config.py
```
然后按照`config.py`里面的提示填写，并创建好所有已填写的文件/文件夹

然后运行
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
### 原理
种子里的comment信息中有种子的torrentid，根据这个id调用网站api查询完整的信息，然后进行过滤

由于调用api需要时间所以会比纯irssi有更多延迟：在我seedhost机器上，海豚会增加1秒左右的延迟，red会增加至少0.5秒左右的延迟，因此对于要r光速种的情况不适用此脚本

通过检查deluge客户端获取种子的ratio，对比api得到的发布者信息进行自动拉黑

## 自动拉黑
同样需要编辑`config.py`中相关的部分，设定拉黑条件，然后运行
```
python3 autoban.py
```
这个只会运行一次，要持续拉黑请自己设定crontab/watch

注意，`autoban.py`运行时会去请求已配置信息的网站获取种子信息，受限于api频率限制第一次运行可能会比较慢

部分log节选（隐私已去除）
```
2021-04-14 11:10:17,372 - INFO - autoban: deluge is connected: True
2021-04-14 11:10:19,876 - INFO - new user banned: ********* #torrents: 1 ratio: 0.000 0.000GB/0.141GB
2021-04-14 11:10:19,876 - INFO - related torrents: megane panda (眼鏡熊猫) - Natsu No Machi EP (夏の街EP) (2015) [WEB] [FLAC] ratio: 0.000 0.0MB/144.7MB
2021-04-14 11:10:19,877 - INFO - 39 user banned in total
```

## deluge数据导出
当你配置好`config.py`中deluge的信息和网站api后，直接运行
```
python3 gen_stats.py > stats.txt
```
你就会在文本文件`stats.txt`中得到一个数据表格，里面不仅包含deluge的信息，还有种子从网站api内获取的信息

这个表格是用tab分割的，所以你只要把文件内容全选复制到excel里即可进行你需要的数据分析

注意，`gen_stats.py`运行时会去请求已配置信息的网站获取种子信息，受限于api频率限制第一次运行可能会比较慢

## deluge删除网站上被删种的种子

警告，此脚本会删除deluge内的种子和**文件**，请确认功能后使用！

功能：删除所有deluge里"Tracker Status"中含有"Unregistered torrent"字样的种子，以及文件

当配置好`config.py`中和deluge相关的部分后，直接运行
```
python3 remove_unregistered.py
```

部分log节选：
```
2021-04-14 11:02:13,526 - INFO - remove_unregistered: deluge is connected: True
2021-04-14 11:02:13,582 - INFO - removing torrent "Atomic Kitten - Feels So Good (2002) [7243 5433722 2]" reason: "xxxxxxxx.xxxx: Error: Unregistered torrent"
2021-04-14 11:02:13,974 - INFO - removing torrent "VA-Clap-(COUD_11)-12INCH_VINYL-FLAC-199X-YARD" reason: "flacsfor.me: Error: Unregistered torrent"
2021-04-14 11:02:14,533 - INFO - removing torrent "Headnodic - Tuesday (2002) - WEB FLAC" reason: "flacsfor.me: Error: Unregistered torrent"
```

## 向我报bug、提需求

欢迎向我报bug：
* 请提供log文件（默认为`filter.log`）和相关截图以便分析问题所在

欢迎向我提需求：
* 所有涉及到筛选的逻辑（选种，ban人，使用令牌）我写的比较简略，如果有其他需求可以告诉我，不过选种部分的筛选逻辑其实许多完全可以在irssi里筛过了，所以irssi能完成的筛选逻辑就不要提需求了
* 数据导出更多字段，有什么字段你觉得有必要导出的可以告诉我
