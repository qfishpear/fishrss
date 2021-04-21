- [Gazelle Autodl Script Set](#gazelle-autodl-script-set)
  - [Functionalities](#functionalities)
  - [Installation Instructions](#installation-instructions)
  - [Configuration](#configuration)
    - [Which entries should I edit?](#which-entries-should-i-edit)
    - [Verify the config](#verify-the-config)
    - [Where to find cookie, authkey, torrent_pass](#where-to-find-cookie-authkey-torrent_pass)
    - [Where to find api_key](#where-to-find-api_key)
    - [How to comment / uncomment a piece of code](#how-to-comment--uncomment-a-piece-of-code)
  - [Filter by uploader and use tokens by torrent size `filter.py`](#filter-by-uploader-and-use-tokens-by-torrent-size-filterpy)
    - [Warning](#warning)
    - [Configuration](#configuration-1)
    - [Run](#run)
      - [Mode A：Monitor a directory](#mode-amonitor-a-directory)
      - [Mode B: Call by parameters](#mode-b-call-by-parameters)
    - [Parameters](#parameters)
    - [some pieces of log (in monitoring mode):](#some-pieces-of-log-in-monitoring-mode)
  - [Automatically ban uploaders `autoban.py`](#automatically-ban-uploaders-autobanpy)
    - [Rule of banning](#rule-of-banning)
    - [Configuration](#configuration-2)
    - [Run](#run-1)
    - [Parameters](#parameters-1)
    - [A piece of log](#a-piece-of-log)
  - [Export deluge statistics `gen_stats.py`](#export-deluge-statistics-gen_statspy)
  - [Delete unregistered torrents in deluge `remove_unregistered.py`](#delete-unregistered-torrents-in-deluge-remove_unregisteredpy)
    - [Warning](#warning-1)
    - [Functionality](#functionality)
    - [Run](#run-2)
    - [A piece of log：](#a-piece-of-log-1)
  - [Bug report and feature request](#bug-report-and-feature-request)
# Gazelle Autodl Script Set
This set of scripts aims on bringing better autodl experience in gazelle music trackers.

Redacted, Orpheus and Dicmusic are now supported.

## Functionalities
* Filter by uploader. You can customize some filter conditions including a ban-list of uploaders. No restriction on BT client.
* Spend tokens wisely. The filter will spend tokens if the torrent size is within a configured range. No restriction on BT client.
* Autoban. Automatically ban an uploader if your ratio is too low. Only deluge is supported.
* Export deluge statistics.
* Delete unregistered torrents in deluge, along with their files.

## Installation Instructions

Only python3 is supported. To see if your python3 installation, type in
```
python3 --version
```
in your console and you'll see your python's version.

Install python modules (omit sudo if you're root or in Windows)
```
sudo pip3 install bencode.py ipython requests datasize deluge-client
```
if you don't have root privilege, you can use `--user`
```
pip3 install bencode.py ipython requests datasize deluge-client --user
```
or things like `virtualenv` (google it)

Then download this repo:
```
git clone https://github.com/qfishpear/fishrss.git
cd fishrss/
```

## Configuration

make a copy of `config.py.en.example` into `config.py`
```
cp config.py.en.example config.py
```
and edit `config.py` according to the instructions in it. Make sure all files and directories in config have been already created by yourself.

Relative path is tolerable, but if you're going to run in crontab or something like that, absolute path is highly recommended

If you're using Windows, use `/` instead of `\` as the separator of path.

### Which entries should I edit?

Different entries in config are required in different scripts. Not all of them are required if you're not going to use every scripts in this repo. However, the following ones are required to be edited in all scripts. (`None` is also regarded as edited)

* For Redacted, in `CONFIG["red"]`, `"api_cache_dir"`，`"authkey"`, `"torrent_pass"` are required, and one of `"cookies"`和`"api_key"`are required. If you don't edit `"cookies"`, leave it commented.
* For Orpheus, in `CONFIG["ops"]`, `"api_cache_dir"`，`"authkey"`, `"torrent_pass"` are required, and one of `"cookies"`和`"api_key"`are required. If you don't edit `"cookies"`, leave it commented.
* For Dicmusic, in `CONFIG["dic"]`, `"api_cache_dir"`，`"cookies"`, `"authkey"`, `"torrent_pass"` are required.

If you're going to use scripts besides `filter.py`, it's highly recommended to fill `api_cache_dir` and create the corresponding directory. Otherwise, same api requests will be sent to server repeatedly if you run the scripts multiple times. Some JSON files should be created as API cache during running.

The entries required in each script will be explained correspondingly.

### Verify the config
To see if you edit it correctly, run
```
python3 check_config.py
```
If everything is fine, it should print as below. However, it's not guaranteed to be correct even if the check is passed.
```
2021-04-20 16:01:43,835 - INFO - dic querying action=index
2021-04-20 16:01:44,616 - INFO - dic logged in successfully, username：fishpear uid: 1132
2021-04-20 16:01:44,616 - INFO - red querying action=index
2021-04-20 16:01:44,781 - INFO - red logged in successfully, username：fishpear uid: 50065
2021-04-20 16:01:44,783 - INFO - ops querying action=index
2021-04-20 16:01:45,099 - INFO - ops logged in successfully, username：fishpear uid: 21482
2021-04-20 16:01:45,116 - INFO - deluge is correctly configured
```

### Where to find cookie, authkey, torrent_pass
You can refer to [README.rss.md](https://github.com/qfishpear/fishrss/blob/main/README.rss.md) in the repo.

### Where to find api_key
red：open your profile and follow:
![1.png](https://i.loli.net/2021/04/22/WNk4ZXz7vi1DneP.png)
ops：almost the same as red (and even easier)

### How to comment / uncomment a piece of code
In python, commenting means adding `#` in front of a line.

In sublime and other mainstream text editors, select the piece of code that you want to comment / uncomment and press shortcut `ctrl+/`

## Filter by uploader and use tokens by torrent size `filter.py`

In a word, this script monitors new torrent files in `source_dir`, save the ones that fullfills given conditions to `dest_dir`, and spend the tokens according to the torrent size limit.

### Warning
* Filtering will slightly increase latency comparing to the raw irssi-autodl and might have influence on the behavior.
* It won't check if your tokens are used up. If tokens are used up, it will still let the torrent downloaded. So keep an eye on how many tokens are left.

### Configuration

* All entries in `CONFIG["filter"]`：`"source_dir"`, `"dest_dir"`, `"default_behavior"`
* For dic/red/ops, fill the following entries in `CONFIG["dic"/"red"/"ops"]` correspondingly:
* all entries in `"filter_config"`: `"name"`, `"banlist"`, `"media"`, `"format"`, `"sizelim"`
* `"token_thresh"`

### Run

#### Mode A：Monitor a directory
Just run
```
python3 filter.py
```
It will monitor new .torrent files in `source_dir`, save the ones that fullfill given conditions to `dest_dir`, and spend the tokens according to the torrent size limit.

To ease your anxiety a blank screen, it will print a line of "tick" every minute.

If `config.py` is changed, the `filter.py` should be restarted. Press `ctrl-C` to shut it down and run again.

Example: the directories to enter in config.py, autodl and deluge:
![2.JPG](https://i.loli.net/2021/04/22/KZlzXAj8eTEtObu.jpg)
![2.JPG](https://i.loli.net/2021/04/20/xMldRSFw1A4qs8u.jpg)
![3.JPG](https://i.loli.net/2021/04/20/x6TZYJGXidgSjOQ.jpg)

#### Mode B: Call by parameters

Example
```
python3 filter.py --file ./1.torrent
python3 filter.py --url https://redacted.ch/torrents.php?action=download\&id=xxxx\&authkey=xxxx\&torrent_pass=xxx
```

Notice: the login check will be skipped to reduce latency. It's recommended to run `check_config.py` first in order to make sure things are correct.

If you want to use it with irssi-autodl, edit the Preference->Action like this:

![1.JPG](https://i.loli.net/2021/04/21/g9dPteW3ciMmKUj.jpg)

The above entry should be the absolute path to python3. The under entry should be: 
```
"/absolute/path/to/filter.py" --file "$(TorrentPathName)"
```
Below is also fine but with slightly more latency:
```
"/absolute/path/to/filter.py" --url $(TorrentUrl)
```
All paths in `config.py` should be absolute if `filter.py` is used in this way.

### Parameters
~~~~
usage: filter.py [-h] [--url URL] [--file FILE] [--skip-api] [--no-tick] [--chromeheaders] [--force-accept] [--deluge]

optional arguments:
  -h, --help       show this help message and exit
  --url URL        Download url of a torrent. If an url is provided, the code will only run once for the provided url and exits.
  --file FILE      path of a torrent file. If a file is provided, the code will only run once for the provided file and exits.
  --skip-api       If set, the site api call will be skipped. Notice: the api-only information will be unavailable: uploader, media and format. Therefore,
                   their filter config must be None otherwise there won't be any torrent filtered out.
  --no-tick        If not set, every minute there will be a "tick" shown in the log, in order to save people with "black screen anxiety"
  --chromeheaders  If set, torrent download requests will be sent with chrome's headers instead ofthe default headers of Requests. It can bypass site's
                   downloading limit of non-browser downloading of torrents. This is slightly against the rule of api usage, so add this only if necessary
  --force-accept   If set, always accept a torrent regardless of filter's setting
  --deluge         push torrents to deluge by deluge api directly
~~~~
Notice: if you just want the "wisely-use-token" functionality and want a lower latency, add `--skip-api` and `--force-accept` like:
```
python3 filter.py --skip-api --force-accept
```
or
```
"/absolute/path/to/filter.py" --file "$(TorrentPathName)" --skip-api --force-accept
```
in irssi-autodl.

The latter one should ideally have negligible latency increment comparing to "save to watch folder" directly in irssi-autodl. If you add option `--deluge`, it might be even faster.

### some pieces of log (in monitoring mode):
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

## Automatically ban uploaders `autoban.py`
This script read the statistics from deluge, add the uploaders who fullfill given conditions to file `CONFIG["red"/"ops"/"dic]["filter_config"]["banlist"]`

### Rule of banning

Here is the entries in `config["red"/"ops"/"dic"]["autoban"]`

* Only consider torrents with progress more than `autoban["ignore"]["min_progress"]` and added no more than `autoban["ignore"]["max_time_added"]` seconds
* For each entry in `autoban["ratio"]`: if an uploader has uploaded no less than `"count"` torrents and your ratio is under "ratiolim"`, it will be added to banlist.

### Configuration

* If you want autoban for red/ops/dic, `CONFIG["red"/"ops"/"dic"]["filter_config"]["banlist"]` should be a file.
* All entries in `CONFIG["deluge"]`: `"ip"`, `"port"`, `"username"`, `"password"`. Here `ip` and `port` should be consistent with connection manager. `username` and `password` are the ones for logging into deluge's webui, if you're not asked to enter username and password, they can be arbitrary (but I'm not confident of this) <br>
![5.JPG](https://i.loli.net/2021/04/16/ZBVay3rjhCPK6Ui.jpg)
* All entries in `config["red"/"ops"/"dic"]["autoban"]`

### Run
For first run, add `--init`
```
python3 autoban.py --init
```
Afterwards, just 
```
python3 autoban.py
```
for each run. 

The script only runs once, i.e. bans once. For contineously running, use crontab/watch.

Example of using watch: run every 2 minutes
```
watch -n 120 python3 autoban.py
```

Notice: `autoban.py` will send API request and might be slow at the first run because of the limitation of API frequency.

### Parameters
~~~~
usage: autoban.py [-h] [--stats] [--init] [--site {dic,red,ops}]

optional arguments:
  -h, --help            show this help message and exit
  --init                run as initialization. if not set, the autoban logic will ONLY ban an uploader if one of his uploaded torrents is active. Here
                        "active" is defined by being uploaded in an hour or not completed.
  --site {dic,red,ops}  if set, only update the banlist of the specified site.
  --stats               show stats of all the uploaders
~~~~
`--stats` can be used if you have question on the ban logic. A piece of log:
```
2021-04-17 09:56:00,777 - INFO - uploader: xxxxxxxxx #torrents: 3 ratio: 1.030 0.678GB/0.658GB
2021-04-17 09:56:00,777 - INFO - uploader: xxxxxxxxx #torrents: 1 ratio: 0.506 0.218GB/0.430GB
2021-04-17 09:56:00,777 - INFO - uploader: xxxxxxxxx #torrents: 13 ratio: 0.842 0.658GB/0.781GB
2021-04-17 09:56:00,778 - INFO - uploader: xxxxxxxxx #torrents: 67 ratio: 0.924 7.557GB/8.180GB
```

### A piece of log
```
2021-04-14 11:10:17,372 - INFO - autoban: deluge is connected: True
2021-04-14 11:10:19,876 - INFO - new user banned: ********* #torrents: 1 ratio: 0.000 0.000GB/0.141GB
2021-04-14 11:10:19,876 - INFO - related torrents: megane panda (眼鏡熊猫) - Natsu No Machi EP (夏の街EP) (2015) [WEB] [FLAC] ratio: 0.000 0.0MB/144.7MB
2021-04-14 11:10:19,877 - INFO - 39 user banned in total
```

## Export deluge statistics `gen_stats.py`

If deluge and API are correctly configured, just run
```
python3 gen_stats.py > stats.txt
```
will get a table in text file `stats.txt`. It not only contains information in deluge, but also information from API.

It uses `tab` as separator, so you can copy-paste the content in to excel and do data analysis

Notice: `gen_stats.py` will send API request and might be slow at the first run because of the limitation of API frequency.

## Delete unregistered torrents in deluge `remove_unregistered.py`

### Warning

This script will delete torrents and **files** permanently in deluge, make sure you know its functionality before use it.

### Functionality

delete all the uncompleted torrents in deluge with "Unregistered torrent" in "Tracker Status", along with the **files**.

Notice: it's not limited to torrents of red/dic/ops.
### Run

If deluge and API are correctly configured, just run
```
python3 remove_unregistered.py
```
The script only runs once, i.e. deletes once. For contineously running, use crontab/watch.

### A piece of log：
```
2021-04-14 11:02:13,526 - INFO - remove_unregistered: deluge is connected: True
2021-04-14 11:02:13,582 - INFO - removing torrent "Atomic Kitten - Feels So Good (2002) [7243 5433722 2]" reason: "xxxxxxxx.xxxx: Error: Unregistered torrent"
2021-04-14 11:02:13,974 - INFO - removing torrent "VA-Clap-(COUD_11)-12INCH_VINYL-FLAC-199X-YARD" reason: "flacsfor.me: Error: Unregistered torrent"
2021-04-14 11:02:14,533 - INFO - removing torrent "Headnodic - Tuesday (2002) - WEB FLAC" reason: "flacsfor.me: Error: Unregistered torrent"
```

## Bug report and feature request

Bug reports are welcomed:
* Please send the log file (`filter.log` by default) and screenshots to help analysis.

Feature requests are welcomed:
* Just don't request a filtering condition in `filter.py` if it can be done by irssi-autodl itself.