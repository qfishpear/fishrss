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

## 安装依赖

本脚本仅支持python3，所以你首先需要安装一个python3的环境，这个怎么搞自行上网搜索，正确安装在之后你打开命令行输入
```
python3 --version
```
之后应该能看到python安装的版本信息

之后安装本程序依赖的包（win用户/root用户省略sudo）：
```
sudo pip3 install bencode.py ipython requests datasize deluge-client
```

## 填写配置信息

首先你需要将`config.py.example`复制一份为`config.py`
```
cp config.py.example config.py
```
然后按照`config.py`里面的提示填写，并创建好所有已填写的文件/文件夹。

所有路径可以填写相对路径，但是如果要crontab等方式运行，填写绝对路径更为保险

### 我应该填写哪些信息

不同的脚本对于配置中需要的信息不一样，如果你不需要全套的脚本则不需要全部填写，但以下信息是必须的（填为None也视为一种填写）：

* 如果要使用海豚，至少需要填写`CONFIG["dic"]`里的`"api_cache_dir"`, `"authkey"`, `"torrent_pass"`, `"cookies"`
* 如果要使用red，至少需要填写`CONFIG["red"]`里的`"api_cache_dir"`, `"authkey"`, `"torrent_pass"`, 而`"cookies"`和`"api_key"`两个要填至少一个，如果不填写`"cookies"`，请保持它被注释掉的状态

除了种子过滤以外如果要使用其他脚本，强烈建议填写`api_cache_dir`并创建对应文件夹，否则多次运行会反反复复向网站发同样的请求导致运行特别慢。脚本运行后此文件夹下应当生成了若干个json文件，是保存的网站api的缓存。

各个脚本所需要的信息我会在对应项目下说明。

### 如何获取cookie, authkey, torrent_pass
请参考本repo内[README.rss.md](https://github.com/qfishpear/fishrss/blob/main/README.rss.md)内的相关内容

### 如何获取api_key
这个是只有red才有的，打开你的个人设置，然后看下图：
![4.png](https://i.loli.net/2021/04/16/1Hzdi3YZpVXBtc9.png)

### 怎么编辑配置文件

对于完全不知道python的小白，你需要一个正常的文本编辑器，这里推荐sublime: 
```
https://www.sublimetext.com/
```
用sublime打开配置文件`config.py`，正常来说会识别这是一个python文件，如果没有，请点击右下角

![1.JPG](https://i.loli.net/2021/04/16/WMzGr3hAan5kc4m.jpg)

并手动选择python

![2.JPG](https://i.loli.net/2021/04/16/7JHglirA2sMzemW.jpg)

这样sublime就会对代码进行语法高亮，对于你填的格式错误会给予提示

在sublime里把某个选项填为None之后应该是这样显示的，不需要加引号：

![3.JPG](https://i.loli.net/2021/04/16/vuaDwFWLEdfVOrp.jpg)
### 怎么对一段代码添加注释/去除注释
python里，注释的意思是在一行代码前面添加井号#

在sublime里，如果要注释掉一段代码，或者取消一整段代码的注释，请选中这一段代码并按快捷键`ctrl+/`，其中`/`是问号那个键

## 种子过滤`filter.py`
简单来说本脚本的功能是监控`source_dir`内的种子，将满足设定条件的种子转存到`dest_dir`中，并根据种子体积限制使用令牌。

### 警告
* 种子过滤本身有延迟，所以如果发种人irssi发种或发光速种的话可能导致ratio颗粒无收，使用前请考虑清楚。
* 本脚本自动使用token的逻辑不会检查你是否还有token，当你网站token已用光之后，r种依然会继续，此时你将会进入不用令牌r种的状态，请做好心理准备。

### 填写配置信息

* `CONFIG["filter"]`下的所有信息：`"source_dir"`, `"dest_dir"`, `"default_behavior"`
* 对于海豚/red，分别填写对应`CONFIG["dic"或"red"]`的以下内容：
* `"filter_config"`下的所有信息：`"name"`, `"banlist"`, `"media"`, `"format"`, `"sizelim"`
* `"token_thresh"`

### 运行

直接运行
```
python3 filter.py
```
即可，这个脚本会持续监控指定文件夹，然后将满足过滤条件的种子保存到另一个指定文件夹下。监控文件夹下的种子被检查后会被删除。为了缓解黑屏焦虑症，这个脚本每分钟会输出一行"tick"

### 部分log节选
隐私已去除
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

## 自动拉黑`autoban.py`
本脚本会读取deluge里种子的信息，将满足设定条件的发种人添加到`CONFIG["red"]["filter_config"]["banlist"]`文件内

### 拉黑规则

以下为`config["red"]["autoban"]`下的内容：

* 只统计种子完成度大于`autoban["ignore"]["min_progress"]`，且距离发种时间少于`autoban["ignore"]["max_time_added"]`的种子
* 对于`autoban["ratio"]`下的任意一个条目：如果某发种人发种数量不少于`"count"`且总ratio低于`"ratiolim"`，则ban掉此发种人

### 填写配置信息

* `CONFIG["red"]["filter_config"]["banlist"]`必须已经填写
* `CONFIG["deluge"]`下的所有信息：`"ip"`, `"port"`, `"username"`, `"password"`。其中ip和port应当和connection manager下的信息一致。username和password是deluge登陆webui所输的账号和密码，如果你登录的时候不需要输，可能可以随便填（关于这一点我也不是很确定）。
![5.JPG](https://i.loli.net/2021/04/16/ZBVay3rjhCPK6Ui.jpg)
* `config["red"]["autoban"]`下的所有信息

### 运行
```
python3 autoban.py
```
这个只会运行一次，要持续拉黑请自己设定定时运行，如crontab/watch/Windows定时任务等，以watch为例：

样例：每2分钟运行一次
```
watch -n 120 python3 autoban.py
```

注意，`autoban.py`运行时会去请求已配置信息的网站获取种子信息，受限于api频率限制第一次运行可能会比较慢

### 部分log节选
隐私已去除
```
2021-04-14 11:10:17,372 - INFO - autoban: deluge is connected: True
2021-04-14 11:10:19,876 - INFO - new user banned: ********* #torrents: 1 ratio: 0.000 0.000GB/0.141GB
2021-04-14 11:10:19,876 - INFO - related torrents: megane panda (眼鏡熊猫) - Natsu No Machi EP (夏の街EP) (2015) [WEB] [FLAC] ratio: 0.000 0.0MB/144.7MB
2021-04-14 11:10:19,877 - INFO - 39 user banned in total
```

## deluge数据导出
当你配置好自动拉黑里所说的中deluge的信息和网站api后，直接运行
```
python3 gen_stats.py > stats.txt
```
你就会在文本文件`stats.txt`中得到一个数据表格，里面不仅包含deluge的信息，还有种子从网站api内获取的信息

这个表格是用tab分割的，所以你只要把文件内容全选复制到excel里即可进行你需要的数据分析

注意，`gen_stats.py`运行时会去请求已配置信息的网站获取种子信息，受限于api频率限制第一次运行可能会比较慢

## deluge删除网站上被删种的种子

### 警告
此脚本会删除deluge内的种子和**文件**，请确认功能后使用！

### 功能
删除所有deluge里还未下完的、且"Tracker Status"中含有"Unregistered torrent"字样的种子，**以及文件**。

注意，如果red/dic之外的种子里的tracker回复了这条信息一样会被删除。

### 运行

当配置好自动拉黑中所说的和deluge相关的部分后，直接运行
```
python3 remove_unregistered.py
```
这个只会运行一次，要持续拉黑请自己设定定时运行

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
