# coding:utf-8

from config import config
from ..utils.port_checker import check_port
from ..utils.geo_ip import domain2ip, parseLocation, IPLoc
from ..client_launcher import ShadowsocksClient, ShadowsocksRClient, V2RayClient
from .test_methods import SpeedTestMethods
import logging
import copy
import socket
import socks
import time
import pynat
import requests
import json

logger = logging.getLogger("Sub")


LOCAL_ADDRESS = config["localAddress"]
LOCAL_PORT = config["localPort"]
HEADERS_BROWSER = {
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 Safari/537.36"
}
HEADERS_DALVIK = {
    'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 9; ALP-AL00 Build/HUAWEIALP-AL00)"
}


class SpeedTest(object):
    def __init__(self, parser, method="SOCKET", use_ssr_cs=False):
        self.__configs = parser.nodes
        self.__use_ssr_cs = use_ssr_cs
        self.__testMethod = method
        self.__results = []
        self.__current = {}
        self.__baseResult = {
            "group": "N/A",
            "remarks": "N/A",
            "loss": 1,
            "speed1": 0,
            "speed2": 0,
            "speed3": 0,
            "ping": 1,
            "gPingLoss": 1,
            "gPing": 0,
            "dspeed": -1,
            "maxDSpeed": -1,
            "trafficUsed": 0,
            "geoIP": {
                "inbound": {
                    "address": "N/A",
                    "info": "N/A"
                },
                "outbound": {
                    "address": "N/A",
                    "info": "N/A"
                }
            },
            "rawSocketSpeed": [],
            "rawTcpPingStatus": [],
            "rawGooglePingStatus": [],
            "webPageSimulation": {
                "results": []
            },
            "ntt": {
                "type": "",
                "internal_ip": "",
                "internal_port": 0,
                "public_ip": "",
                "public_port": 0
            },
            "media": {
                "NetFlix": False,
                "AbemaTV": False,
                "iQyi": False,
                "TVB": False,
                "NetFlixR": "N/A",
                "HBO_Asia": "N/A",
                "YoutubePR": "N/A",
                "DAZNR": "N/A",
                "DisneyPlusR": "N/A",
                "Tiktok": "N/A",
                "SteamC": "N/A",
                "HotStarR": "N/A",

            }
        }

    def __getMediaInfo_Netflix(self):
        proxy = {"http": "socks5://"+str(LOCAL_ADDRESS)+":"+str(
            LOCAL_PORT), "https": "socks5://"+str(LOCAL_ADDRESS)+":"+str(LOCAL_PORT)}
        response = requests.get(
            "https://www.netflix.com/title/81215567", headers=HEADERS_BROWSER, proxies=proxy)
        logger.info("NetFlix Returned HTTP "+str(response.status_code)+".")
        if(response.status_code == 404):
            return (True, 'N/A')
        elif(response.status_code == 403):
            return (False, 'N/A')
        elif(response.status_code == 200):
            logger.info("NetFlix Region:["+response.url[24:26].upper()+"].")
            return (True, response.url[24:26].upper())
        else:
            return (False, 'N/A')

    def __getMediaInfo_AbemaTV(self):
        proxy = {"http": "socks5://"+str(LOCAL_ADDRESS)+":"+str(
            LOCAL_PORT), "https": "socks5://"+str(LOCAL_ADDRESS)+":"+str(LOCAL_PORT)}
        try:
            response = requests.get("https://api.abema.io/v1/ip/check?device=android",
                                    headers=HEADERS_DALVIK, proxies=proxy, timeout=10)
            logger.info("AbemaTV Returned HTTP "+str(response.status_code)+".")
            if(json.loads(response.text)["isoCountryCode"] == "JP"):
                return True
            else:
                return False
        except:
            logger.info("AbemaTV Connection Error!")
            return False

    def __getMediaInfo_TVB(self):
        proxy = {"http": "socks5://"+str(LOCAL_ADDRESS)+":"+str(
            LOCAL_PORT), "https": "socks5://"+str(LOCAL_ADDRESS)+":"+str(LOCAL_PORT)}
        temphead = {
            "Accept": "application/json;pk=BCpkADawqM2Gpjj8SlY2mj4FgJJMfUpxTNtHWXOItY1PvamzxGstJbsgc-zFOHkCVcKeeOhPUd9MNHEGJoVy1By1Hrlh9rOXArC5M5MTcChJGU6maC8qhQ4Y8W-QYtvi8Nq34bUb9IOvoKBLeNF4D9Avskfe9rtMoEjj6ImXu_i4oIhYS0dx7x1AgHvtAaZFFhq3LBGtR-ZcsSqxNzVg-4PRUI9zcytQkk_YJXndNSfhVdmYmnxkgx1XXisGv1FG5GOmEK4jZ_Ih0riX5icFnHrgniADr4bA2G7TYh4OeGBrYLyFN_BDOvq3nFGrXVWrTLhaYyjxOr4rZqJPKK2ybmMsq466Ke1ZtE-wNQ",
            "Origin": "https://www.encoretvb.com"
        }
        try:
            response = requests.get(
                "https://edge.api.brightcove.com/playback/v1/accounts/5324042807001/videos/6005570109001", headers=temphead, proxies=proxy)
            logger.info("TVB Returned HTTP "+str(response.status_code)+".")
            logger.info("error_subcode="+json.loads(response.text)
                        [0]["error_subcode"])
            if(json.loads(response.text)[0]["error_subcode"] == "CLIENT_GEO"):
                return False
            else:
                return True
        except:
            return False

    def __getMediaInfo_HBO_Asia(self):
        proxy = {"http": "socks5://"+str(LOCAL_ADDRESS)+":"+str(
            LOCAL_PORT), "https": "socks5://"+str(LOCAL_ADDRESS)+":"+str(LOCAL_PORT)}
        try:
            response = requests.get(
                "https://api2.hbogoasia.com/v1/geog?lang=undefined&version=0&bundleId=www.hbogoasia.com", headers=HEADERS_BROWSER, proxies=proxy)
            logger.info("HBO Asia Returned HTTP "+str(response.status_code)+".")
            logger.info("HBO Asia territory="+str(json.loads(response.text)["territory"]))
            if(not json.loads(response.text)["territory"]):
                return "N/A"
            else:
                return json.loads(response.text)["territory"]
        except:
            return "N/A"

    def __getMediaInfo_DAZN(self):
        proxy = {"http": "socks5://"+str(LOCAL_ADDRESS)+":"+str(
            LOCAL_PORT), "https": "socks5://"+str(LOCAL_ADDRESS)+":"+str(LOCAL_PORT)}
        temphead = {
            "Content-Type": "application/json"
        }
        tempdata = '{"LandingPageKey":"generic","Languages":"zh-CN,zh,en","Platform":"web","PlatformAttributes":{},"Manufacturer":"","PromoCode":"","Version":"2"}'
        try:
            response = requests.post(
                "https://startup.core.indazn.com/misl/v5/Startup", headers=temphead, data=tempdata,proxies=proxy)
            logger.info("DAZN Returned HTTP "+str(response.status_code)+".")
            logger.info("DAZN isAllowed="+str(json.loads(response.text)["Region"]["isAllowed"]))
            if(json.loads(response.text)["Region"]["isAllowed"]):
                logger.info("DAZN GeolocatedCountry="+str(json.loads(response.text)["Region"]["GeolocatedCountry"].upper()))
                return json.loads(response.text)["Region"]["GeolocatedCountry"].upper()
            else:
                return "N/A"
        except:
            return "N/A"


    def __getBaseResult(self):
        return copy.deepcopy(self.__baseResult)

    def __get_next_config(self):
        try:
            return self.__configs.pop(0)
        except IndexError:
            return None

    def __get_client(self, client_type: str):
        if client_type == "Shadowsocks":
            return ShadowsocksClient()
        elif client_type == "ShadowsocksR":
            client = ShadowsocksRClient()
            if self.__use_ssr_cs:
                client.useSsrCSharp = True
            return client
        elif client_type == "V2Ray":
            return V2RayClient()
        else:
            return None

    def resetStatus(self):
        self.__results = []
        self.__current = {}

    def getResult(self):
        return self.__results

    def getCurrent(self):
        return self.__current

    def __geoIPInbound(self, config):
        inboundIP = domain2ip(config["server"])
        inboundInfo = IPLoc(inboundIP)
        inboundGeo = "{} {}, {}".format(
            inboundInfo.get("country", "N/A"),
            inboundInfo.get("city", "Unknown City"),
            inboundInfo.get("organization", "N/A")
        )
        logger.info(
            "Node inbound IP : {}, Geo : {}".format(
                inboundIP,
                inboundGeo
            )
        )
        return (inboundIP, inboundGeo, inboundInfo.get("country_code", "N/A"))

    def __geoIPOutbound(self):
        outboundInfo = IPLoc()
        outboundIP = outboundInfo.get("ip", "N/A")
        outboundGeo = "{} {}, {}".format(
            outboundInfo.get("country", "N/A"),
            outboundInfo.get("city", "Unknown City"),
            outboundInfo.get("organization", "N/A")
        )
        logger.info(
            "Node outbound IP : {}, Geo : {}".format(
                outboundIP,
                outboundGeo
            )
        )
        return (outboundIP, outboundGeo, outboundInfo.get("country_code", "N/A"))

    def __tcpPing(self, server, port):
        res = {
            "loss": self.__baseResult["loss"],
            "ping": self.__baseResult["ping"],
            "rawTcpPingStatus": self.__baseResult["rawTcpPingStatus"],
            "gPing": self.__baseResult["gPing"],
            "gPingLoss": self.__baseResult["gPingLoss"],
            "rawGooglePingStatus": self.__baseResult["rawGooglePingStatus"]
        }

        st = SpeedTestMethods()
        latencyTest = st.tcpPing(server, port)
        res["loss"] = 1 - latencyTest[1]
        res["ping"] = latencyTest[0]
        res["rawTcpPingStatus"] = latencyTest[2]
        logger.debug(latencyTest)
        time.sleep(1)
        if (latencyTest[0] > 0):
            try:
                res["gPing"] = 1
            except:
                logger.exception("")
                pass
        return res

    def __nat_type_test(self):

        s = socks.socksocket(socket.AF_INET, socket.SOCK_DGRAM)
        s.set_proxy(socks.PROXY_TYPE_SOCKS5, LOCAL_ADDRESS, LOCAL_PORT)
        sport = config["ntt"]["internal_port"]
        try:
            logger.info("Performing UDP NAT Type Test")
            t, eip, eport, sip = pynat.get_ip_info(
                source_ip=config["ntt"]["internal_ip"],
                source_port=sport,
                include_internal=True,
                sock=s
            )
            return t, eip, eport, sip, sport
        except:
            logger.exception("\n")
            return None, None, None, None, None
        finally:
            s.close()

    def __start_test(self, test_mode="FULL"):
        self.__results = []
        total_nodes = len(self.__configs)
        done_nodes = 0
        node = self.__get_next_config()
        while node:
            done_nodes += 1
            try:
                cfg = node.config
                logger.info(
                    "Starting test {group} - {remarks} [{cur}/{tol}]".format(
                        group=cfg["group"],
                        remarks=cfg["remarks"],
                        cur=done_nodes,
                        tol=total_nodes
                    )
                )
                client = self.__get_client(node.node_type)
                if not client:
                    logger.warn(f"Unknown Node Type: {node.node_type}")
                    node = self.__get_next_config()
                    continue
                _item = self.__getBaseResult()
                _item["group"] = cfg["group"]
                _item["remarks"] = cfg["remarks"]
                self.__current = _item
                cfg["server_port"] = int(cfg["server_port"])
                client.startClient(cfg)

                # Check client started
                time.sleep(1)
                ct = 0
                client_started = True
                while not client.check_alive():
                    ct += 1
                    if ct > 3:
                        client_started = False
                        break
                    client.startClient(cfg)
                    time.sleep(1)
                if not client_started:
                    logger.error("Failed to start client.")
                    continue
                logger.info("Client started.")

                # Check port
                ct = 0
                port_opened = True
                while True:
                    if ct >= 3:
                        port_opened = False
                        break
                    time.sleep(1)
                    try:
                        check_port(LOCAL_PORT)
                        break
                    except socket.timeout:
                        ct += 1
                        logger.error("Port {} timeout.".format(LOCAL_PORT))
                    except ConnectionRefusedError:
                        ct += 1
                        logger.error(
                            "Connection refused on port {}.".format(LOCAL_PORT))
                    except:
                        ct += 1
                        logger.exception("An error occurred:\n")
                if not port_opened:
                    logger.error("Port {} closed.".format(LOCAL_PORT))
                    continue

                inboundInfo = self.__geoIPInbound(cfg)
                _item["geoIP"]["inbound"]["address"] = inboundInfo[0]
                _item["geoIP"]["inbound"]["info"] = inboundInfo[1]
                if inboundInfo[1] == "N/A Unknown City, N/A":
                    continue
                pingResult = self.__tcpPing(cfg["server"], cfg["server_port"])
                if (isinstance(pingResult, dict)):
                    for k in pingResult.keys():
                        _item[k] = pingResult[k]
                outboundInfo = self.__geoIPOutbound()
                _item["geoIP"]["outbound"]["address"] = outboundInfo[0]
                _item["geoIP"]["outbound"]["info"] = outboundInfo[1]
                if outboundInfo[0] == "N/A":
                    continue
                if (_item["gPing"] > 0 or outboundInfo[2] == "CN"):
                    st = SpeedTestMethods()
                    if test_mode == "WPS":
                        res = st.startWpsTest()
                        _item["webPageSimulation"]["results"] = res
                        logger.info("[{}] - [{}] - Loss: [{:.2f}%] - TCP Ping: [{:.2f}] - Google Loss: [{:.2f}%] - Google Ping: [{:.2f}] - [WebPageSimulation]".format
                                    (
                                        _item["group"],
                                        _item["remarks"],
                                        _item["loss"] * 100,
                                        int(_item["ping"] * 1000),
                                        _item["gPingLoss"] * 100,
                                        int(_item["gPing"] * 1000)
                                    )
                                    )
                    elif test_mode == "PING":
                        nat_info = ""
                        if config["ntt"]["enabled"]:
                            t, eip, eport, sip, sport = self.__nat_type_test()
                            _item["ntt"]["type"] = t
                            _item["ntt"]["internal_ip"] = sip
                            _item["ntt"]["internal_port"] = sport
                            _item["ntt"]["public_ip"] = eip
                            _item["ntt"]["public_port"] = eport

                            if t:
                                nat_info += " - NAT Type: " + t
                                if t != pynat.BLOCKED:
                                    nat_info += " - Internal End: {}:{}".format(
                                        sip, sport)
                                    nat_info += " - Public End: {}:{}".format(
                                        eip, eport)

                        logger.info("[{}] - [{}] - Loss: [{:.2f}%] - TCP Ping: [{:.2f}] - Google Loss: [{:.2f}%] - Google Ping: [{:.2f}]{}".format
                                    (
                                        _item["group"],
                                        _item["remarks"],
                                        _item["loss"] * 100,
                                        int(_item["ping"] * 1000),
                                        _item["gPingLoss"] * 100,
                                        int(_item["gPing"] * 1000),
                                        nat_info
                                    )
                                    )

                    elif test_mode == "FULL":
                        nat_info = ""
                        logger.info("Starting Media Test.")
                        nf, nfr = self.__getMediaInfo_Netflix()
                        _item["media"]["NetFlix"] = nf
                        _item["media"]["NetFlixR"] = nfr
                        abt = self.__getMediaInfo_AbemaTV()
                        _item["media"]["AbemaTV"] = abt
                        tvb = self.__getMediaInfo_TVB()
                        _item["media"]["TVB"] = tvb
                        hboa = self.__getMediaInfo_HBO_Asia()
                        _item["media"]["HBO_Asia"] = hboa
                        dazn = self.__getMediaInfo_DAZN()
                        _item["media"]["DAZNR"] = dazn
                        if config["ntt"]["enabled"]:
                            t, eip, eport, sip, sport = self.__nat_type_test()
                            _item["ntt"]["type"] = t
                            _item["ntt"]["internal_ip"] = sip
                            _item["ntt"]["internal_port"] = sport
                            _item["ntt"]["public_ip"] = eip
                            _item["ntt"]["public_port"] = eport

                            if t:
                                nat_info += " - NAT Type: " + t
                                if t != pynat.BLOCKED:
                                    nat_info += " - Internal End: {}:{}".format(
                                        sip, sport)
                                    nat_info += " - Public End: {}:{}".format(
                                        eip, eport)

                        testRes = st.startTest(self.__testMethod)
                        if (int(testRes[0]) == 0):
                            logger.warn("Re-testing node.")
                            testRes = st.startTest(self.__testMethod)
                        _item["dspeed"] = testRes[0]
                        _item["maxDSpeed"] = testRes[1]
                        _item["speed1"] = testRes[4]
                        _item["speed2"] = testRes[5]
                        _item["speed3"] = testRes[6]
                        try:
                            _item["trafficUsed"] = testRes[3]
                            _item["rawSocketSpeed"] = testRes[2]
                        except:
                            pass

                        logger.info("[{}] - [{}] - Loss: [{:.2f}%] - TCP Ping: [{:.2f}] - Google Loss: [{:.2f}%] - Google Ping: [{:.2f}] - AvgSpeed: [{:.2f}MB/s] - MaxSpeed: [{:.2f}MB/s]{}".format
                                    (
                                        _item["group"],
                                        _item["remarks"],
                                        _item["loss"] * 100,
                                        int(_item["ping"] * 1000),
                                        _item["gPingLoss"] * 100,
                                        int(_item["gPing"] * 1000),
                                        _item["dspeed"] / 1024 / 1024,
                                        _item["maxDSpeed"] / 1024 / 1024,
                                        nat_info
                                    )
                                    )

                    else:
                        logger.error(f"Unknown Test Mode {test_mode}")
            except Exception:
                logger.exception("\n")
            finally:
                self.__results.append(_item)
                if client:
                    client.stopClient()
                node = self.__get_next_config()
                time.sleep(1)

        self.__current = {}

    def webPageSimulation(self):
        logger.info("Test mode : Web Page Simulation")
        self.__start_test("WPS")

    def tcpingOnly(self):
        logger.info("Test mode : tcp ping only.")
        self.__start_test("PING")

    def fullTest(self):
        logger.info("Test mode : speed and tcp ping.Test method : {}.".format(
            self.__testMethod))
        self.__start_test("FULL")
