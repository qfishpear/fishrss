# rss脚本

## 功能简述
* 访问api `https://海豚/ajax.php?action=notifications`来获取r种的种子id，访问api需要cookie鉴权
* 根据种子id和设定的`AUTHKEY`和`TORRENT_PASS`来生成种子链接并下载
* 下载前会检查种子的体积，如果体积大于设定的大小`FL_THRESHOLD`则生成的种子链接中会添加`&usetoken=1`以使用token
* 下载下来的种子会存在设定的文件夹`DOWNLOAD_DIR`内，你的bt客户端应当监控这个目录以实现自动下载，本脚本没有其他任何和bt客户端交互的逻辑
* 程序会记录已经下载过的种子链接在文件`DOWNLOADED_URLS`里，不会重复下载
* 以上功能运行一次代码只会跑一遍，如需持续监控rss请自行配置定时运行，如crontab/watch

## 安装依赖
只支持python3
```
pip3 install bencode.py requests
```

## 填写信息
### COOKIES
首先是cookie，注意我这里要求填写的是已经解码为key-value形式的cookie，即你需要填写cookie里`PHPSESSID`和`session`的值，而非编码后放在一起的那个字符串
```
COOKIES = {"PHPSESSID": "xxxxxxxxxxxxxxxx",
           "session"  : "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}
```
怎么找到网站上的cookie有多种方式，这里推荐一个chrome插件editthiscookie
```
https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg?hl=zh-CN
```
安装完此插件之后，打开任意海豚的网页，点击editthiscookie的图标，然后按照下图方式复制cookie
![](https://i.loli.net/2021/04/13/hcXIKgVbr5mHuED.png)

### AUTHKEY, TORRENT_PASS
这个你去网站里复制一下下载链接即可，里面有
```
AUTHKEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TORRENT_PASS = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### FL_THRESHOLD
逻辑：如果体积大于设定的大小`FL_THRESHOLD`则生成的种子链接中会添加`&usetoken=1`以使用token，单位bytes
```
FL_THRESHOLD = 100 * 1024**3 # 100GB
```
建议先填个大的值，运行一遍代码，再填你实际需要的体积限制，这个是因为如果之前rss列表里有种子，那么你可能会在上面浪费令牌，而跑过一遍之后这些种子都已经被记录过了，就不会重复下载了

### DOWNLOAD_DIR, DOWNLOADED_URLS
DOWNLOAD_DIR 应当填写为你bt客户端监控下载的目录，DOWNLOADED_URLS可以不用改
```
DOWNLOAD_DIR = "./watch/"
DOWNLOADED_URLS = "./downloaded_urls.txt"
```

## 运行代码
```
python3 rss.py
```
正确运行时的部分log（隐私已略去）：
```
2021-04-13 10:38:27,382 - INFO - Starting new HTTPS connection (1): xxxxxxxx.xxxx
2021-04-13 10:38:28,474 - INFO - downloaded file doesn't exist, create new one: ./downloaded_urls.txt
2021-04-13 10:38:28,474 - INFO - torrent directory doesn't exist, create new one: ./watch/
2021-04-13 10:38:28,474 - INFO - 50 torrents in rss result
2021-04-13 10:38:28,475 - INFO - download https://xxxxxxxx.xxxx/torrents.php?action=download&id=49132&authkey=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx&torrent_pass=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
2021-04-13 10:38:28,476 - INFO - Starting new HTTPS connection (1): xxxxxxxx.xxxx
2021-04-13 10:38:29,563 - INFO - hash=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
2021-04-13 10:38:29,565 - INFO - download https://xxxxxxxx.xxxx/torrents.php?action=download&id=49131&authkey=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx&torrent_pass=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
2021-04-13 10:38:29,566 - INFO - Starting new HTTPS connection (1): xxxxxxxx.xxxx
2021-04-13 10:38:30,631 - INFO - hash=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
2021-04-13 10:38:30,632 - INFO - download https://xxxxxxxx.xxxx/torrents.php?action=download&id=49130&authkey=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx&torrent_pass=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
2021-04-13 10:38:32,073 - INFO - 3 torrents added
```
此时watch文件夹里有：
```
fishpear@sea:~/rss/tmp/watch$ ls
Proc Fiskal - Lothian Buses (2021) [24B-44.1Khz].torrent
Raphael Saadiq - The Way I See It.torrent
Taylor Swift - Fearless - Taylor's Version (2021) {Target Limited Edition} [FLAC].torrent
```
downloaded_urls.txt里有（隐私已略去）：
```
fishpear@sea:~/rss/tmp$ cat downloaded_urls.txt
downloaded urls:
https://xxxxxxxx.xxxx/torrents.php?action=download&id=49132&authkey=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx&torrent_pass=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
https://xxxxxxxx.xxxx/torrents.php?action=download&id=49131&authkey=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx&torrent_pass=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
https://xxxxxxxx.xxxx/torrents.php?action=download&id=49130&authkey=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx&torrent_pass=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## 定时运行
首先老生常谈crontab显然是可以用的，用法自己查，但是坏处就是只能精确到分钟。

那我想每30秒r一次怎么搞呢？ 其实linux有个很简单的命令：watch，以下命令表示30秒运行一次
```
watch -n 30 python3 rss.py
```
注意，你这个时间间隔不能设的太小不然没有意义，因为海豚服务器本身就很卡请爱护服务器，另外api的话有2秒一次的限制不能高于这个限制不然会被z酱打屁股（大雾）。