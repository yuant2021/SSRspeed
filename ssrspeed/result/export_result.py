#coding:utf-8

from PIL import Image,ImageDraw,ImageFont
import json
import os
import sys
import time
import logging
logger = logging.getLogger("Sub")
from ssrspeed.shell import cli as cli_cfg
from .upload_result import pushToServer
from .sorter import Sorter
from .exporters import ExporterWps

from config import config

import requests
import json
import time

VERSION = config["VERSION"]
options,args = cli_cfg.init(VERSION)

'''
	resultJson
		{
			"group":"GroupName",
			"remarks":"Remarks",
			"loss":0,#Data loss (0-1)
			"ping":0.014,
			"gping":0.011,
			"dspeed":12435646 #Bytes
			"maxDSpeed":12435646 #Bytes
		}
'''

class ExportResult(object):
	def __init__(self):
		self.__config = config["exportResult"]
		self.__hide_max_speed = config["exportResult"]["hide_max_speed"]
		self.__hide_ntt = not config["ntt"]["enabled"]
		self.__colors = {}
		self.__colorSpeedList = []
		self.__font = ImageFont.truetype(self.__config["font"],18)
		self.__timeUsed = "N/A"
	#	self.setColors()

	def GetGeoIP(self,ip,type):
		try:
			logger.info("Getting GeoIP:"+ip)
			response = requests.get("https://api.ip.sb/geoip/"+ip)
			res=json.loads(response.text)
			# logger.info(res)
			if(type==1):
				re=str(res['country_code'] + " AS" + str(res['asn']) + "   \t- " + res['organization'])
			if(type==2):
				if 'city' in res:
					re=str(res['country_code'] +" "+ str(res['city']) + "   \t- " + res['organization'])
				else:
					re=str(res['country_code'] +" "+ str("Unknown") + "   \t- " + res['organization'])
			logger.info(str(response.status_code)+":"+re)
			return str(re)
		except:
			logger.error("Regetting GeoIP:"+ip)
			return self.GetGeoIP(ip,type)


	def NodeAnalysis(self,result):
		realnode=0
		returntxt="\n"+result[0]["group"]+" 节点分析 生成时间:"+time.asctime(time.localtime(time.time()))+"\n"+"="*50+"\n"
		returntxt+="入口ip数量:\t"
		inip=[[]for i in range(len(result))]
		outip=[[]for i in range(len(result))]
		nodeinfo=[[]for i in range(len(result))]
		Direct=0
		DirectNodes=[]
		for i in range(0,len(result)):
			inip[i]=result[i]['geoIP']['inbound']['address']
			outip[i]=result[i]['geoIP']['outbound']['address']
			if(inip[i]=='N/A' or outip[i]=='N/A'):
				nodeinfo[i]='0'
				continue
			elif(inip[i]==outip[i]):
				Direct+=1
				DirectNodes.append(i)
			nodeinfo[i]=inip[i]+outip[i]
			realnode+=1
		# logger.info(outip)
		for ip in outip:
			if(ip=='N/A'):
				outip.remove(ip)
		for ip in inip:
			if(ip=='N/A'):
				inip.remove(ip)
		for ip in outip:
			if(ip=='N/A'):
				outip.remove(ip)
		for ip in inip:
			if(ip=='N/A'):
				inip.remove(ip)
		returntxt+="["+str(len(list(set(inip))))+"]个\n"
		returntxt+="落地ip数量:\t"
		returntxt+="["+str(len(list(set(outip))))+"]个\n"
		returntxt+="显示节点数量:\t"
		returntxt+="["+str(len(result))+"]个\n"
		returntxt+="可用节点数量:\t"
		returntxt+="["+str(realnode)+"]个\n"
		returntxt+="直连节点数量:\t"
		returntxt+="["+str(Direct)+"]个\n"
		ingeo=[[]for i in range(len(inip))]
		outgeo=[[]for i in range(len(outip))]
		# logger.info(nodeinfo)
		renode=[]
		rere=0
		for i in range(0,len(nodeinfo)):
			re=[i]
			if(nodeinfo[i]=='0'):
				continue
			else:
				for j in range(i+1,len(nodeinfo)):
					if(nodeinfo[j]=='0'):
						continue
					elif (nodeinfo[i]==nodeinfo[j]):
						re.append(j)
						nodeinfo[j]='0'
			# logger.info(nodeinfo[i])
			nodeinfo[i]='0'
			renode.append(re)
			if(len(re)>1):
				rere+=1
		# logger.info(renode)
		returntxt+="真实节点数量:\t"
		returntxt+="["+str(len(renode))+"]个\n"
		returntxt+="复用节点信息:\t"
		returntxt+="["+str(rere)+"]组["+str(realnode-len(renode))+"]个\n"
		returntxt+="\n入口分析:\n"
		inip=list(set(inip))
		outip=list(set(outip))
		logger.info("Starting to Get Inbound GeoIP")
		for i in range(0,len(inip)):
			ingeo[i]=self.GetGeoIP(inip[i],2)
		logger.info("Starting to Get Outbound GeoIP")
		for i in range(0,len(outip)):
			outgeo[i]=self.GetGeoIP(outip[i],1)
		ingeo=[x for x in ingeo if x!=[]]
		outgeo=[x for x in outgeo if x!=[]]
		# logger.info(ingeo)
		ingeo=sorted(ingeo)
		geolast='N/A'
		index=0
		ingeo
		for geo in ingeo:
			if(geo==geolast):
				index+=1
			else:
				if(index!=0):
					returntxt+="["+str(index)+"] "+geolast+"\n"
				geolast=geo
				index=1
		returntxt+="["+str(index)+"] "+geolast+"\n"
		returntxt+="\n落地分析:\n"
		outgeo=sorted(outgeo)
		geolast='N/A'
		index=0
		for geo in outgeo:
			if(geo==geolast):
				index+=1
			else:
				if(index!=0):
					returntxt+="["+str(index)+"] "+geolast+"\n"
				geolast=geo
				index=1
		returntxt+="["+str(index)+"] "+geolast+"\n"
		# logger.info(ingeo)
		returntxt+="\n直连节点:\n"
		for node in DirectNodes:
			returntxt+=result[node]['remarks']+"\n"
		returntxt+="\n复用节点:\n"
		for nodes in renode:
			if(len(nodes)==1):
				continue
			for i in nodes:
				returntxt+=result[i]['remarks']+"\n"
			returntxt+="\n"
		filename = "./results/" + time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())+"_NodesAnalysis" + ".txt"
		with open(filename,"w") as f:
			f.write(returntxt)
		return "NodesAnalysis Result image saved as"+filename
			
	def MediaAnalysis(self,result):
		returntxt="\n"+result[0]["group"]+" 流媒体分析 生成时间:"+time.asctime(time.localtime(time.time()))+"\n"+"="*50+"\n"
		nf=[]
		nfnhm=[]
		abtv=[]
		tvb=[]
		hbo=[]
		dazn=[]
		for i in range(0,len(result)):
			if(result[i]['media']['NetFlix']==True and result[i]['media']['NetFlixR']=='N/A'):
				nf.append(i)
			elif(result[i]['media']['NetFlix']==True):
				nfnhm.append(i)
			if(result[i]['media']['AbemaTV']==True):
				abtv.append(i)
			if(result[i]['media']['TVB']==True):
				tvb.append(i)
			if(result[i]['media']['HBO_Asia']!='N/A'):
				hbo.append(i)
			if(result[i]['media']['DAZNR']!='N/A'):
				dazn.append(i)
		returntxt+="支持NetFlix自制剧节点数量:\t"
		returntxt+="["+str(len(nf))+"]个\n"
		returntxt+="支持NetFlix非自制剧节点数量:\t"
		returntxt+="["+str(len(nfnhm))+"]个\n"
		returntxt+="支持AbemaTV节点数量:\t\t"
		returntxt+="["+str(len(abtv))+"]个\n"
		returntxt+="支持TVBAnywhere+节点数量:\t"
		returntxt+="["+str(len(tvb))+"]个\n"
		returntxt+="支持HBO Asia节点数量:\t\t"
		returntxt+="["+str(len(hbo))+"]个\n"
		returntxt+="支持DAZN节点数量:\t\t"
		returntxt+="["+str(len(dazn))+"]个\n"
		returntxt+="\n支持NetFlix自制剧节点:\n"
		for i in nf:
			returntxt+=result[i]['remarks']+"\n"
		returntxt+="\n支持NetFlix非自制剧节点:\n"
		for i in nfnhm:
			returntxt+="{Region:"+result[i]['media']['NetFlixR']+"} "+result[i]['remarks']+"\n"
		returntxt+="\n支持AbemaTV节点:\n"
		for i in abtv:
			returntxt+=result[i]['remarks']+"\n"
		returntxt+="\n支持TVBAnywhere+节点:\n"
		for i in tvb:
			returntxt+=result[i]['remarks']+"\n"
		returntxt+="\n支持HBO Asia节点:\n"
		for i in hbo:
			returntxt+="{Region:"+result[i]['media']['HBO_Asia']+"} "+result[i]['remarks']+"\n"
		returntxt+="\n支持DAZN节点:\n"
		for i in dazn:
			returntxt+="{Region:"+result[i]['media']['DAZNR']+"} "+result[i]['remarks']+"\n"
		filename = "./results/" + time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())+"_MediaAnalysis" + ".txt"
		with open(filename,"w") as f:
			f.write(returntxt)
		return "MediaAnalysis Result image saved as"+filename

	def setColors(self,name = "origin"):
		for color in self.__config["colors"]:
			if (color["name"] == name):
				logger.info("Set colors as {}.".format(name))
				self.__colors = color["colors"]
				self.__colorSpeedList.append(0)
				for speed in self.__colors.keys():
					try:
						self.__colorSpeedList.append(float(speed))
					except:
						continue
				self.__colorSpeedList.sort()
				return
		logger.warn("Color {} not found in config.".format(name))

	def setTimeUsed(self, timeUsed):
		self.__timeUsed = time.strftime("%H:%M:%S", time.gmtime(timeUsed))
		logger.info("Time Used : {}".format(self.__timeUsed))

	def export(self,result,split = 0,exportType = 0,sortMethod = ""):

		logger.info(self.NodeAnalysis(result))
		logger.info(self.MediaAnalysis(result))
		if (not exportType):
			self.__exportAsJson(result)
		sorter = Sorter()
		result = sorter.sortResult(result,sortMethod)
		self.__exportAsPng(result)

	def exportWpsResult(self, result, exportType = 0):
		if not exportType:
			result = self.__exportAsJson(result)
		epwps = ExporterWps(result)
		epwps.export()

	def __getMaxWidth(self,result):
		font = self.__font
		draw = ImageDraw.Draw(Image.new("RGB",(1,1),(255,255,255)))
		maxGroupWidth = 0
		maxRemarkWidth = 0
		for item in result:
			group = item["group"]
			remark = item["remarks"]
			maxGroupWidth = max(maxGroupWidth,draw.textsize(group,font=font)[0])
			maxRemarkWidth = max(maxRemarkWidth,draw.textsize(remark,font=font)[0])
		return (maxGroupWidth + 10,maxRemarkWidth + 10)
	
	'''
	def __deweighting(self,result):
		_result = []
		for r in result:
			isFound = False
			for i in range(0,len(_result)):
				_r = _result[i]
				if (_r["group"] == r["group"] and _r["remarks"] == r["remarks"]):
					isFound = True
					if (r["dspeed"] > _r["dspeed"]):
						_result[i] = r
					elif(r["ping"] < _r["ping"]):
						_result[i] = r
					break
			if (not isFound):
				_result.append(r)
		return _result
	'''

	def __getBasePos(self, width, text):
		font = self.__font
		draw = ImageDraw.Draw(Image.new("RGB",(1,1),(255,255,255)))
		textSize = draw.textsize(text, font=font)[0]
		basePos = (width - textSize) / 2
		logger.debug("Base Position {}".format(basePos))
		return basePos

	def __exportAsPng(self,result):
		if (self.__colorSpeedList == []):
			self.setColors()
	#	result = self.__deweighting(result)
		resultFont = self.__font
		generatedTime = time.localtime()
		imageHeight = len(result) * 30 + 30 
		weight = self.__getMaxWidth(result)
		groupWidth = weight[0]
		remarkWidth = weight[1]
		if (groupWidth < 60):
			groupWidth = 60
		if (remarkWidth < 60):
			remarkWidth = 90
		otherWidth = 100
	
		groupRightPosition = groupWidth
		remarkRightPosition = groupRightPosition + remarkWidth
		lossRightPosition = remarkRightPosition + otherWidth
		tcpPingRightPosition = lossRightPosition + otherWidth
		googlePingRightPosition = tcpPingRightPosition + otherWidth + 25
		dspeedRightPosition = googlePingRightPosition + otherWidth
		maxDSpeedRightPosition = dspeedRightPosition + otherWidth
		ntt_right_position = maxDSpeedRightPosition + otherWidth + 80
		imageRightPosition = dspeedRightPosition

		if not self.__hide_max_speed:
			imageRightPosition = maxDSpeedRightPosition

		if not self.__hide_ntt:
			if self.__hide_max_speed:
				maxDSpeedRightPosition = dspeedRightPosition

			ntt_right_position = imageRightPosition + otherWidth + 80
			imageRightPosition = ntt_right_position

		newImageHeight = imageHeight + 30 * 4
		resultImg = Image.new("RGB",(imageRightPosition, newImageHeight),(255,255,255))
		draw = ImageDraw.Draw(resultImg)

		
	#	draw.line((0,newImageHeight - 30 - 1,imageRightPosition,newImageHeight - 30 - 1),fill=(127,127,127),width=1)
		text = "From: "+config["exportResult"]["from"]
		draw.text((self.__getBasePos(imageRightPosition, text), 4),
			text,
			font=resultFont,
			fill=(0,0,0)
		)
		text = "By ssrspeed"
		draw.text((maxDSpeedRightPosition , 4),
			text,
			font=resultFont,
			fill=(0,0,0)
		)
		draw.line((0, 30, imageRightPosition - 1, 30),fill=(127,127,127),width=1)
		draw.line((imageRightPosition-1 , 0, imageRightPosition-1, newImageHeight - 1),fill=(127,127,127),width=1)
		draw.line((1, 0, 1, newImageHeight - 1),fill=(127,127,127),width=1)
		draw.line((groupRightPosition, 30, groupRightPosition, imageHeight + 30 - 1),fill=(127,127,127),width=1)
		draw.line((remarkRightPosition, 30, remarkRightPosition, imageHeight + 30 - 1),fill=(127,127,127),width=1)
		draw.line((lossRightPosition, 30, lossRightPosition, imageHeight + 30 - 1),fill=(127,127,127),width=1)
		draw.line((tcpPingRightPosition, 30, tcpPingRightPosition, imageHeight + 30 - 1),fill=(127,127,127),width=1)
		draw.line((googlePingRightPosition, 30, googlePingRightPosition, imageHeight + 30 - 1),fill=(127,127,127),width=1)
		draw.line((dspeedRightPosition, 30, dspeedRightPosition, imageHeight + 30 - 1),fill=(127,127,127),width=1)
		if not self.__hide_max_speed:
			draw.line((maxDSpeedRightPosition, 30, maxDSpeedRightPosition, imageHeight + 30 - 1),fill=(127,127,127),width=1)
		draw.line((imageRightPosition, 0, imageRightPosition, newImageHeight - 1),fill=(127,127,127),width=1)
	
		draw.line((0,0,imageRightPosition - 1,0),fill=(127,127,127),width=1)

		draw.text(
			(
				self.__getBasePos(groupRightPosition, "Group"), 30 + 4
			),
			"Group", font=resultFont, fill=(0,0,0)
		
		)

		draw.text(
			(
				groupRightPosition + self.__getBasePos(remarkRightPosition - groupRightPosition, "Remarks"), 30 + 4
			),
			"Remarks", font=resultFont, fill=(0,0,0)
		
		)
		draw.text(
			(
				remarkRightPosition + self.__getBasePos(lossRightPosition - remarkRightPosition, "speed1"), 30 + 4
			),
			"speed1", font=resultFont, fill=(0,0,0)
		)

		draw.text(
			(
				lossRightPosition + self.__getBasePos(tcpPingRightPosition - lossRightPosition, "speed2"), 30 + 4
			),
			"speed2", font=resultFont, fill=(0,0,0)
		)

		draw.text(
			(
				tcpPingRightPosition + self.__getBasePos(googlePingRightPosition - tcpPingRightPosition, "speed3"), 30 + 4
			),
			"speed3", font=resultFont, fill=(0,0,0)
		)

		draw.text(
			(
				googlePingRightPosition + self.__getBasePos(dspeedRightPosition - googlePingRightPosition, "AvgSpeed"), 30 + 4
			),
			"AvgSpeed", font=resultFont, fill=(0,0,0)
		)

		if not self.__hide_max_speed:
			draw.text(
				(
					dspeedRightPosition + self.__getBasePos(maxDSpeedRightPosition - dspeedRightPosition, "MaxSpeed"), 30 + 4
					),
				"MaxSpeed", font=resultFont, fill=(0,0,0)
			)

		if not self.__hide_ntt:
			draw.text(
				(
					maxDSpeedRightPosition + self.__getBasePos(ntt_right_position - maxDSpeedRightPosition, "UDP NAT Type"), 30 + 4
					),
				"UDP NAT Type", font=resultFont, fill=(0,0,0)
			)
	
		draw.line((0, 60, imageRightPosition - 1, 60),fill=(127,127,127),width=1)

		totalTraffic = 0
		onlineNode = 0
		for i in range(0,len(result)):
			totalTraffic += result[i]["trafficUsed"] if (result[i]["trafficUsed"] > 0) else 0
			if (result[i]["dspeed"] > 0):
				onlineNode += 1
			
			j = i + 1
			draw.line((0,30 * j + 60, imageRightPosition, 30 * j + 60), fill=(127,127,127), width=1)
			item = result[i]

			group = item["group"]
			draw.text((5,30 * j + 30 + 4),group,font=resultFont,fill=(0,0,0))

			remarks = item["remarks"]
			draw.text((groupRightPosition + 5,30 * j + 30 + 4),remarks,font=resultFont,fill=(0,0,0,0))
			speed1 = item["speed1"]
			draw.rectangle((remarkRightPosition + 1,30 * j + 30 + 1,lossRightPosition - 1,30 * j + 60 -1),self.__getColor(speed1))
			speed1 = self.__parseSpeed(speed1)
			pos = remarkRightPosition + self.__getBasePos(lossRightPosition - remarkRightPosition, speed1)
			draw.text((pos, 30 * j + 30 + 4),speed1,font=resultFont,fill=(0,0,0))

			speed2 = item["speed2"]
			draw.rectangle((lossRightPosition + 1,30 * j + 30 + 1,tcpPingRightPosition - 1,30 * j + 60 -1),self.__getColor(speed2))
			speed2 = self.__parseSpeed(speed2)
			pos = lossRightPosition + self.__getBasePos(tcpPingRightPosition - lossRightPosition,speed2)
			draw.text((pos, 30 * j + 30 + 4),speed2,font=resultFont,fill=(0,0,0))

			speed3 = item["speed3"]
			draw.rectangle((tcpPingRightPosition + 1,30 * j + 30 + 1,googlePingRightPosition - 1,30 * j + 60 -1),self.__getColor(speed3))
			speed3 = self.__parseSpeed(speed3)
			pos = tcpPingRightPosition + self.__getBasePos(googlePingRightPosition - tcpPingRightPosition,speed3)
			draw.text((pos, 30 * j + 30 + 4),speed3,font=resultFont,fill=(0,0,0))

			speed = item["dspeed"]
			if (speed == -1):
				pos = googlePingRightPosition + self.__getBasePos(dspeedRightPosition - googlePingRightPosition, "N/A")
				draw.text((pos, 30 * j + 30 + 1),"N/A",font=resultFont,fill=(0,0,0))
			else:
				draw.rectangle((googlePingRightPosition + 1,30 * j + 30 + 1,dspeedRightPosition - 1,30 * j + 60 -1),self.__getColor(speed))
				speed = self.__parseSpeed(speed)
				pos = googlePingRightPosition + self.__getBasePos(dspeedRightPosition - googlePingRightPosition, speed)
				draw.text((pos, 30 * j + 30 + 1), speed,font=resultFont,fill=(0,0,0))

			if not self.__hide_max_speed:
				maxSpeed = item["maxDSpeed"]
				if (maxSpeed == -1):
					pos = dspeedRightPosition + self.__getBasePos(maxDSpeedRightPosition - dspeedRightPosition, "N/A")
					draw.text((pos, 30 * j + 30 + 1),"N/A",font=resultFont,fill=(0,0,0))
				else:
					draw.rectangle((dspeedRightPosition + 1,30 * j + 30 + 1,maxDSpeedRightPosition - 1,30 * j + 60 -1),self.__getColor(maxSpeed))
					maxSpeed = self.__parseSpeed(maxSpeed)
					pos = dspeedRightPosition + self.__getBasePos(maxDSpeedRightPosition - dspeedRightPosition, maxSpeed)
					draw.text((pos, 30 * j + 30 + 1), maxSpeed,font=resultFont,fill=(0,0,0))

			if not self.__hide_ntt:
				nat_type = item["ntt"]["type"]
				if not nat_type:
					pos = maxDSpeedRightPosition + self.__getBasePos(ntt_right_position - maxDSpeedRightPosition, "Unknown")
					draw.text((pos, 30 * j + 30 + 1),"Unknown",font=resultFont,fill=(0,0,0))
				else:
					pos = maxDSpeedRightPosition + self.__getBasePos(ntt_right_position - maxDSpeedRightPosition, nat_type)
					draw.text((pos, 30 * j + 30 + 1), nat_type,font=resultFont,fill=(0,0,0))
		
		files = []
		if (totalTraffic < 0):
			trafficUsed = "N/A"
		else:
			trafficUsed = self.__parseTraffic(totalTraffic)

		draw.text((5, imageHeight + 30 + 4),
			"Traffic used : {}. Time used: {}. Online Node(s) : [{}/{}]".format(
				trafficUsed,
				self.__timeUsed,
				onlineNode,
				len(result)
			),
			font=resultFont,
			fill=(0,0,0)
		)
	#	draw.line((0,newImageHeight - 30 * 3 - 1,imageRightPosition,newImageHeight - 30 * 3 - 1),fill=(127,127,127),width=1)
		text = "结果说明：普通快速模式，节点测试3秒，取1秒 2秒 3秒的节点速度，以及均速和最高速度"
		if (options.sr == "a"):
			text = "结果说明：起速测试模式，节点测试1.5秒，取0.5秒 1秒 1.5秒的节点速度，以及均速和最高速度"
		draw.text((5,imageHeight + 30 * 2 + 4),
			text,
			font=resultFont,
			fill=(0,0,0)
		)
		draw.text((5,imageHeight + 30 * 3 + 4),
			"开源地址:https://github.com/yuant2007/SSRspeed",
			font=resultFont,
			fill=(0,0,0)
		)
		draw.line((0,newImageHeight - 30 - 1,imageRightPosition,newImageHeight - 30 - 1),fill=(127,127,127),width=1)
		'''
		draw.line((0,newImageHeight - 30 - 1,imageRightPosition,newImageHeight - 30 - 1),fill=(127,127,127),width=1)
		draw.text((5,imageHeight + 30 * 2 + 4),
			"By SSRSpeed {}.".format(
				config["VERSION"]
			),
			font=resultFont,
			fill=(0,0,0)
		)
		'''
		
		draw.line((0,newImageHeight - 1,imageRightPosition,newImageHeight - 1),fill=(127,127,127),width=1)
		filename = "./results/" + time.strftime("%Y-%m-%d-%H-%M-%S", generatedTime) + ".png"
		resultImg.save(filename)
		files.append(filename)
		logger.info("Result image saved as %s" % filename)
		
		for _file in files:
			if (not self.__config["uploadResult"]):
				break
			pushToServer(_file)

	def __parseTraffic(self,traffic):
		traffic = traffic / 1024 / 1024
		if (traffic < 1):
			return("%.2f KB" % (traffic * 1024))
		gbTraffic = traffic / 1024
		if (gbTraffic < 1):
			return("%.2f MB" % traffic)
		return ("%.2f GB" % gbTraffic)

	def __parseSpeed(self,speed):
		speed = speed / 1024 / 1024
		if (speed < 1):
			return("%.2fKB" % (speed * 1024))
		else:
			return("%.2fMB" % speed)

	def __newMixColor(self,lc,rc,rt):
	#	print("RGB1 : {}, RGB2 : {}, RT : {}".format(lc,rc,rt))
		return (
			int(lc[0]*(1-rt)+rc[0]*rt),
			int(lc[1]*(1-rt)+rc[1]*rt),
			int(lc[2]*(1-rt)+rc[2]*rt)
		)

	def __getColor(self,data):
		if (self.__colorSpeedList == []):
			return (255,255,255)
		rt = 1
		curSpeed = self.__colorSpeedList[len(self.__colorSpeedList)-1]
		backSpeed = 0
		if (data >= curSpeed  * 1024 * 1024):
			return (self.__colors[str(curSpeed)][0],self.__colors[str(curSpeed)][1],self.__colors[str(curSpeed)][2])
		for i in range (0,len(self.__colorSpeedList)):
			curSpeed = self.__colorSpeedList[i] * 1024 * 1024
			if (i > 0):
				backSpeed = self.__colorSpeedList[i-1]
			backSpeedStr = str(backSpeed)
		#	print("{} {}".format(data/1024/1024,backSpeed))
			if (data < curSpeed):
				rgb1 = self.__colors[backSpeedStr] if backSpeed > 0 else (255,255,255)
				rgb2 = self.__colors[str(self.__colorSpeedList[i])]
				rt = (data - backSpeed * 1024 * 1024)/(curSpeed - backSpeed * 1024 * 1024)
				logger.debug("Speed : {}, RGB1 : {}, RGB2 : {}, RT : {}".format(data/1024/1024,rgb1,rgb2,rt))
				return self.__newMixColor(rgb1,rgb2,rt)
		return (255,255,255)


	def __exportAsJson(self,result):
	#	result = self.__deweighting(result)
		filename = "./results/" + time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()) + ".json"
		with open(filename,"w+",encoding="utf-8") as f:
			f.writelines(json.dumps(result,sort_keys=True,indent=4,separators=(',',':')))
		logger.info("Result exported as %s" % filename)
		return result

