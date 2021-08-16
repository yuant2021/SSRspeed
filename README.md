<h1 align="center">
    <br>SSRSpeed 二次魔改版 
</h1>
<p align="center">
Batch speed measuring tool based on Shadowsocks(R) and V2Ray
</p>
<p align="center">
  <a href="https://github.com/yuant2007/SSRspeed/tags"><img src="https://img.shields.io/github/tag/yuant2007/SSRspeed.svg"></a>
  <a href="https://github.com/yuant2007/SSRspeed/releases"><img src="https://img.shields.io/github/release/yuant2007/SSRspeed.svg"></a>
  <a href="https://github.com/yuant2007/SSRspeed/blob/master/LICENSE"><img src="https://img.shields.io/github/license/yuant2007/SSRspeed.svg"></a>
</p>

## 特性
- 支持单线程/起速
- 支持导出为json,png等格式
- 支持分析NetFlix,Dazn,HBO Asia,AbemaTV等流媒体支持情况
- 支持自动输出节点复用信息

## 要求
#### 见 **requirements.txt**
### Linux 依赖
- [libsodium](https://github.com/jedisct1/libsodium)
- [Shadowsocks-libev](https://github.com/shadowsocks/shadowsocks-libev)
- [Simple-Obfs](https://github.com/shadowsocks/simple-obfs)

## 支持平台
### 已测试
1. Windows 11 on amd64 + Python3.9
2. Debian 10 on WSL2 + Python3.7

**理论所有能运行在任何支持Python, Shadowsocks, ShadowsocksR, V2Ray的平台**

## 开发者

- <del>Removed as requested by the developer</del>
- Modify by [Yuant](https://github.com/yuant2007)

## 入门
~~~~bash
pip install -r requirements.txt
~~~~

~~~~text
$ python3 main.py
Usage: main.py [options] arg1 arg2...

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -c GUICONFIG, --config=GUICONFIG
                        Load configurations from file.
  -u URL, --url=URL     Load ssr config from subscription url.
  -m TEST_METHOD, --method=TEST_METHOD
                        Select test method in [speedtestnet, fast, socket,
                        stasync].
  -r SR                 Select speed result in [a,b].
  -M TEST_MODE, --mode=TEST_MODE
                        Select test mode in [all,wps,pingonly].
  --include             Filter nodes by group and remarks using keyword.
  --include-remark      Filter nodes by remarks using keyword.
  --include-group       Filter nodes by group name using keyword.
  --exclude             Exclude nodes by group and remarks using keyword.
  --exclude-group       Exclude nodes by group using keyword.
  --exclude-remark      Exclude nodes by remarks using keyword.
  --use-ssr-cs          Replace the ShadowsocksR-libev with the
                        ShadowsocksR-C# (Only Windows).
  -g GROUP_OVERRIDE     Manually set group.
  -y, --yes             Skip node list confirmation before test.
  -C RESULT_COLOR, --color=RESULT_COLOR
                        Set the colors when exporting images..
  -s SORT_METHOD, --sort=SORT_METHOD
                        Select sort method in
                        [speed,rspeed,ping,rping],default not sorted.
  -i IMPORT_FILE, --import=IMPORT_FILE
                        Import test result from json file and export it.
  --skip-requirements-check
                        Skip requirements check.
  --debug               Run program in debug mode.
  --paolu               如题
~~~~

### 示例
~~~~bash
python3 main.py -yu https://get.exl.ink/api/v1/client/subscribe?xxxxxx --sort=spped
~~~~

**WebAPI已被砍**
