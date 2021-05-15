- [Gazelle Autodl Script Set](#gazelle-autodl-script-set)
  - [Functionalities](#functionalities)
  - [Installation Instructions](#installation-instructions)
  - [Configuration](#configuration)
    - [Which entries should I edit?](#which-entries-should-i-edit)
    - [Verify the config](#verify-the-config)
    - [Where to find cookies](#where-to-find-cookies)
    - [Where to find authkey, torrent_pass](#where-to-find-authkey-torrent_pass)
    - [Where to find api_key](#where-to-find-api_key)
    - [How to comment / uncomment a piece of code](#how-to-comment--uncomment-a-piece-of-code)
  - [Filter by uploader and use tokens by torrent size `filter.py`](#filter-by-uploader-and-use-tokens-by-torrent-size-filterpy)
    - [Warning](#warning)
    - [Configuration Required](#configuration-required)
    - [Run](#run)
      - [Mode A: Monitor a directory](#mode-a-monitor-a-directory)
      - [Mode B: Call by parameters](#mode-b-call-by-parameters)
    - [Parameters](#parameters)
    - [some pieces of log (in monitoring mode):](#some-pieces-of-log-in-monitoring-mode)
  - [Automatically ban uploaders `autoban.py`](#automatically-ban-uploaders-autobanpy)
    - [Rule of banning](#rule-of-banning)
    - [Configuration Required](#configuration-required-1)
    - [Run](#run-1)
    - [Parameters](#parameters-1)
    - [A piece of log](#a-piece-of-log)
  - [Export deluge statistics `gen_stats.py`](#export-deluge-statistics-gen_statspy)
  - [Delete unregistered torrents in deluge `remove_unregistered.py`](#delete-unregistered-torrents-in-deluge-remove_unregisteredpy)
    - [Warning](#warning-1)
    - [Functionality](#functionality)
    - [Run](#run-2)
    - [A piece of log：](#a-piece-of-log-1)
  - [Crossseeding `reseed.py`](#crossseeding-reseedpy)
    - [Configuration Required](#configuration-required-2)
    - [Run](#run-3)
      - [Mode A: scan all subdirectories](#mode-a-scan-all-subdirectories)
      - [Mode B: scan one directory](#mode-b-scan-one-directory)
      - [Mode C: crossseed multiple torrent files under a directory](#mode-c-crossseed-multiple-torrent-files-under-a-directory)
      - [Mode D: crossseed single torrent file](#mode-d-crossseed-single-torrent-file)
    - [Results](#results)
    - [Parameters](#parameters-2)
    - [a piece of log](#a-piece-of-log-2)
  - [Bug report and feature request](#bug-report-and-feature-request)
# Gazelle Autodl Script Set
This set of scripts aims on bringing better autodl experience in gazelle music trackers.

Redacted, Orpheus and Dicmusic are now supported.

## Functionalities
* Filter by uploader. You can customize some filter conditions including a ban-list of uploaders. No restriction on BT client.
* Spend tokens wisely. The filter will spend tokens if the torrent size is within a configured range. No restriction on BT client. RED/OPS is not supported in this feature because of its rule.
* Autoban. Automatically ban an uploader if your ratio is too low. Only deluge is supported.
* Export deluge statistics.
* Delete unregistered torrents in deluge, along with their files.
* Cross-seed. Scan files in a directory and download the "crossseedable" torrents.

## Installation Instructions

Only python3 is supported. To see if your python3 is correctly installed, type in
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

* For Redacted, in `CONFIG["red"]`, `"api_cache_dir"`，`"authkey"`, `"torrent_pass"` are required, and one of `"cookies"` and `"api_key"` are required. If you don't edit `"cookies"`, leave it commented.
* For Orpheus, in `CONFIG["ops"]`, `"api_cache_dir"`，`"authkey"`, `"torrent_pass"` are required, and one of `"cookies"` and `"api_key"` are required. If you don't edit `"cookies"`, leave it commented.
* For Dicmusic, in `CONFIG["dic"]`, `"api_cache_dir"`，`"cookies"`, `"authkey"`, `"torrent_pass"` are required.

If you're going to use other scripts besides `filter.py`, it's highly recommended to fill `api_cache_dir` and create the corresponding directory. Otherwise, same api requests will be sent to server repeatedly if you run the scripts multiple times, which makes it really slow. Some JSON files should be created in that folder as API cache during running.

The entries required in each script will be explained correspondingly.

### Verify the config
To see if you've edited it correctly, run
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

### Where to find cookies
There are multiple ways. I personally recommend using the "editthiscookie" plugin of chrome
```
https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg
```
Open an arbitrary page of red, and copy like this:
![1.png](https://i.loli.net/2021/04/22/1yoz6rNGcBHU4TF.png)

### Where to find authkey, torrent_pass
Copy the downloading link "DL" of an arbitrary torrent, and you can find them in the link.

### Where to find api_key
red：open your profile and follow:
![1.png](https://i.loli.net/2021/04/22/WNk4ZXz7vi1DneP.png)
ops：almost the same as red (and even easier)

### How to comment / uncomment a piece of code
In python, commenting means adding `#` in front of a line.

In sublime and other mainstream text editors, select the piece of code that you want to comment / uncomment and press shortcut `ctrl+/`

## Filter by uploader and use tokens by torrent size `filter.py`

In a word, this script monitors new torrent files in `source_dir`, saves the ones that satisfy given conditions to `dest_dir`, and then spends the tokens according to the torrent size limit.

### Warning
* Filtering will slightly increase latency comparing to the raw irssi-autodl and might have influence on the racing performance.
* It won't check if your tokens are used up. If tokens are used up, it will still leave the torrent downloaded. So keep an eye on how many tokens are left if you're short in buffer.

### Configuration Required

* All entries in `CONFIG["filter"]`：`"source_dir"`, `"dest_dir"`, `"default_behavior"`
* For dic/red/ops, fill the following entries in `CONFIG["dic"/"red"/"ops"]` correspondingly:
* all entries in `"filter_config"`: `"name"`, `"banlist"`, `"whitelist"`, `"media"`, `"format"`, `"sizelim"`
* `"token_thresh"` (only for dic)

### Run

#### Mode A: Monitor a directory
Just run
```
python3 filter.py
```
It will monitor new .torrent files in `source_dir`, saves the ones that satisfy given conditions to `dest_dir`, and spends the tokens according to the torrent size limit.

To ease the anxiety of a blank screen, it will print a line of "tick" every minute.

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
usage: filter.py [-h] [--url URL] [--file FILE] [--skip-api] [--no-tick] [--force-accept] [--deluge]

optional arguments:
  -h, --help      show this help message and exit
  --url URL       Download url of a torrent. If an url is provided, the code will only run once for the provided url
                  and exits.
  --file FILE     path of a torrent file. If a file is provided, the code will only run once for the provided file and
                  exits.
  --skip-api      If set, the site api call will be skipped. Notice: the api-only information will be unavailable:
                  uploader, media and format. Therefore, their filter config must be None otherwise there won't be any
                  torrent filtered out.
  --no-tick       If not set, every minute there will be a "tick" shown in the log, in order to save people with
                  "black screen anxiety"
  --force-accept  If set, always accept a torrent regardless of filter's setting
  --deluge        push torrents to deluge by its api directly instead of saving to CONFIG["filter"]["dest_dir"]
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
This script read the statistics from deluge, add the uploaders who fullfill given conditions to file `CONFIG["red"/"ops"/"dic]["filter_config"]["banlist"]`.

`autoban.py` runs independently of `filter.py` and only interacts with it by the banlist file.

### Rule of banning

Here is the entries in `config["red"/"ops"/"dic"]["autoban"]`

* Only consider torrents with progress more than `autoban["ignore"]["min_progress"]` and added no more than `autoban["ignore"]["max_time_added"]` seconds ago.
* For each entry in `autoban["ratio"]`: if an uploader has uploaded no less than `"count"` torrents and your ratio is under "ratiolim"`, it will be added to banlist.

### Configuration Required

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

It uses `tab` as separator, so you can copy-paste the content into excel and analysis the data afterwards

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

## Crossseeding `reseed.py`

This script scans all sub-directories under a given directory and searchs in the tracker for torrents that can be crossseeded.

It can also scan torrents under a given directory to see if it can be crossseeded in another tracker.

Notice: The automatical way of searching can't be as perfect. Therefore it does NOT promise all found torrents can be correctly crossseeded, NOR does it promise all missed directories can not be crossseeded. A minority of torrents might have their files/directories renamed and other unexpected problems. Make sure your BT client does NOT automatically start when you add the scanned torrents.

### Configuration Required

No extra entries in `config.py` needed to fill, except [the mandatory ones](#which-entries-should-i-edit)

However, if you have some irrelevant files/directories in your music directory, for example, `.DS_Store` in macOS, they will influence the scanning process. Add the files/directories you want to ignore to the `IGNORED_PATH` list in `reseed.py`.

### Run

If you terminated the script during running, the next time you run it, it will skip the sub-directories it scanned before. If you don't want to skip them, delete the `scan_history.txt` under the directory given by `--result-dir`.

The directory given by `--result-dir` should be created before running the script.

#### Mode A: scan all subdirectories
For example, if all your music files are downloaded to `~/downloads` and you're trying to crossseed in RED and store the results in folder `~/results`, run:
```
python3 reseed.py --site red --dir ~/downloads --result-dir ~/results
```

#### Mode B: scan one directory

Use `--single-dir` to crossseed for a single directory. 

For example: if there are music files in `~/downloads/Masashi Sada (さだまさし) - さだ丼～新自分風土記III～ (2021) [24-96]/`, run:
```
python3 reseed.py --site dic --single-dir ~/downloads/Masashi\ Sada\ \(さだまさし\)\ -\ さだ丼～新自分風土記III～\ \(2021\)\ \[24-96\]/ --result-dir ~/results
```
Take care of the escape characters are required when coming up with spaces and some other characters. It's recommended to enter the directory names by `TAB`

#### Mode C: crossseed multiple torrent files under a directory

Use `--torrent-dir` to try to crossseed multiple .torrent files:

For example: if there are .torrent files in `~/torrents`, run:
```
python3 reseed.py --site red --torrent-dir ~/torrents --result-dir ~/results
```

#### Mode D: crossseed single torrent file
Use `--single-torrent` to try to crossseed one .torrent files:

For example: if there is a torrent `~/torrents/The Call - Collected - 2019 (CD - FLAC - Lossless).torrent`, run:
```
python3 reseed.py --site red --single-torrent ~/torrents/The\ Call\ -\ Collected\ -\ 2019\ \(CD\ -\ FLAC\ -\ Lossless\).torrent --result-dir ~/results
```

### Results

The following things will be generated under the directory given by `--result-dir`:
* `torrent/`, a directory storing all the downloaded .torrent files. All .torrent files will be named by "name-of-crossseeding-directory.torrent". This way of naming may be helpful if the name of directory was changed by the uploader.
* `result_mapping.txt`, the result of crossseeding. Each line contains a (directory / .torrent file) name and a torrent ID, seperated by a TAB (\t). If no torrent is found for crossseeding, the torrent ID would be -1.
* `result_url.txt`, each line contains a download link of "crossseedable" torrents.
* `result_url_undownloaded.txt`. Due to some tracker's limitation of downloading with scripts, some torrents will fail to download. The links of these torrents will be store in this file and you can manually download them.
* `scan_history.txt`, each line contains the absolute path to a directory that has been scanned before. The crossseeding script will ignore the directories written in this file.

### Parameters
```
usage: reseed.py [-h] (--dir DIR | --single-dir SINGLE_DIR) --site {dic,red,ops,snake} --result-dir RESULT_DIR
                 [--api-frequency API_FREQUENCY] [--no-download]

scan a directory to find torrents that can be cross-seeded on given tracker

optional arguments:
  -h, --help            show this help message and exit
  --dir DIR             folder for batch cross-seeding
  --single-dir SINGLE_DIR
                        folder for just one cross-seeding
  --torrent-dir TORRENT_DIR
                        folder containing .torrent files for cross-seeding
  --single-torrent SINGLE_TORRENT
                        one .torrent file for cross-seeding
  --site {dic,red,ops,snake}
                        the tracker to scan for cross-seeding.
  --result-dir RESULT_DIR
                        folder for saving scanned results
  --api-frequency API_FREQUENCY
                        if set, override the default api calling frequency. Unit: number of api call per 10 seconds (must be integer)
  --no-download         if set, don't download the .torrent files. Only the id of torrents are saved
```

### a piece of log
```
fishpear@sea:~/rss$ python3 reseed.py --site dic --dir ~/downloads --result-dir ~/results
2021-04-25 16:22:16,799 - INFO - file automatically created: /home7/fishpear/results/scan_history.txt
2021-04-25 16:22:16,799 - INFO - file automatically created: /home7/fishpear/results/result_url.txt
2021-04-25 16:22:16,799 - INFO - file automatically created: /home7/fishpear/results/result_mapping.txt
2021-04-25 16:22:16,800 - INFO - directory automatically created: /home7/fishpear/results/torrents/
2021-04-25 16:22:16,800 - INFO - file automatically created: /home7/fishpear/results/result_url_undownloaded.txt
2021-04-25 16:22:16,800 - INFO - dic querying action=index
2021-04-25 16:22:17,588 - INFO - dic logged in successfully, username：fishpear uid: 1132
2021-04-25 16:22:17,632 - INFO - 1797/1797 unscanned folders found in /home7/fishpear/downloads, start scanning for cross-seeding dic
2021-04-25 16:22:17,632 - INFO - 1/1797 /home7/fishpear/downloads/Eliane Radigue - Backward
2021-04-25 16:22:17,632 - INFO - dic querying filelist=3+Songs+Of+Milarepa+1+2+Remastered+2021+flac&action=browse
2021-04-25 16:22:18,329 - INFO - not found
...
2021-04-25 16:22:19,711 - INFO - 4/1797 /home7/fishpear/downloads/55 Schubert and Boccherini String Quintets
2021-04-25 16:22:19,711 - INFO - dic querying filelist=03+Quintet+in+C+Major+for+Two+Violins+Viola+and+Two+Cellos+D+956+III+Scherzo+Presto+Trio+Andante+sostenuto+flac&action=browse
2021-04-25 16:22:20,406 - INFO - found, torrentid=49506
2021-04-25 16:22:21,517 - INFO - saving to /home7/fishpear/results/torrents/55 Schubert and Boccherini String Quintets.torrent
...
```

## Bug report and feature request

Bug reports are welcomed:
* Please send the log file (`filter.log` by default) and screenshots to help analysis.

Feature requests are welcomed:
* Just don't request a filtering condition in `filter.py` if it can be done by irssi-autodl itself.