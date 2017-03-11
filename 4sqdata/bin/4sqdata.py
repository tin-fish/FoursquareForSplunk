#!/usr/bin/python
import json, urllib2, time, sys
import xml.dom.minidom, xml.sax.saxutils
import logging
import os
import os.path
myRunningDir = os.path.dirname(os.path.join(os.getcwd(), __file__))
logging.root
logging.root.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s %(message)s')
handler = logging.StreamHandler(stream=sys.stderr)
handler.setFormatter(formatter)
logging.root.addHandler(handler)
def splunkSquare(pkey,key,val,result):
	if pkey != "":
		pkey=pkey+"_"
	if pkey=="" and key=="createdAt":
		x=0
	elif type(val) is unicode:
		result=result+","+pkey+key+"=\""+val.encode('utf8', 'replace')+"\""
	elif type(val) in [bool,int,float]:
		result=result+","+pkey+key+"=\""+str(val)+"\""
	elif type(val) is dict:
		for subkey in val.keys():
			result=splunkSquare(pkey+key,subkey,val[subkey],result)
	elif type(val) is list:
		c=0
		for subval in val:
			result=splunkSquare(pkey+key,str(c),subval,result)
			c=c+1
	return result
def retrievecheckin(startPoint,token):
	logging.info("Running retrievecheckin function")
	finishPoint=startPoint
	logging.info("Working startpoint of "+str(startPoint))
	url="https://api.foursquare.com/v2/users/self/checkins?oauth_token="+token+"&v=20160509&afterTimestamp="+str(startPoint)+"&limit=250&sort=oldestfirst"
	logging.info("Making the API call...")
	data=json.load(urllib2.urlopen(url))
	logging.info("Foursquare totes responded!!!")
	for checkin in data["response"]["checkins"]["items"]:
		Time=checkin["createdAt"]
		result=str(Time)+",datatype=\"checkin\""
		for key in checkin.keys():
			result = splunkSquare("",key,checkin[key],result)
		print result
		finishPoint=Time
	return(finishPoint)
def runFoursquareApp(token):
	logging.info("Running main body of script")
	try:
		m=open(myRunningDir+'/4sqdata.dat','r')
		marker=int(m.read())
		m.close()
	except:
		logging.warn("Did not find a dat file, assuming this is the very first time...")
		marker=0
	stop=time.time()
	while marker<stop:
		logging.info("Running from marker "+str(marker))
		(pointer)=retrievecheckin(marker,token)
		if pointer==marker:break
		marker=pointer+1
	logging.info("Finishing cycle, writing to dat file")
	m=open(myRunningDir+'/4sqdata.dat','w')
	m.write(str(marker))
	m.close()
# Empty introspection routine
def do_scheme():
	SCHEME = """<scheme>
		<title>4sqdata</title>
		<description>Get your foursquare checkin data!</description>
		<use_external_validation>true</use_external_validation>
		<streaming_mode>plain</streaming_mode>
		<use_single_instance>true</use_single_instance>
		<endpoint>
			<args>
				<arg name="my4sqAPItoken">
					<title>Foursquare Developer Token</title>
					<description>You need to request an API developer token from the Foursquare developer website.</description>
				</arg>
			</args>
		</endpoint>
	</scheme>"""
# Empty validation routine. This routine is optional.
def validate_arguments(): 
	pass
# Routine to get the value of an input
def get_token(): 
	try:
		logging.info("Seeking out configuration from modular input stanza")
		config_str = sys.stdin.read()
		logging.info(config_str)
		doc = xml.dom.minidom.parseString(config_str)
		logging.info("parsed configuration as xml")
		root = doc.documentElement
		conf_node = root.getElementsByTagName("configuration")[0]
		if conf_node:
			stanza = conf_node.getElementsByTagName("stanza")[0]
			if stanza:
				stanza_name = stanza.getAttribute("name")
				if stanza_name:
					params = stanza.getElementsByTagName("param")
					for param in params:
						param_name = param.getAttribute("name")
						if param_name:
							logging.info("Reading param:"+param_name)
						if param_name and param.firstChild and param.firstChild.nodeType == param.firstChild.TEXT_NODE and param_name == "my4sqAPItoken": 
							return param.firstChild.data
	except Exception, e:
		raise Exception, "Error getting Splunk configuration via STDIN: %s" % str(e)
	return ""
# Script must implement these args: scheme, validate-arguments
if __name__ == '__main__':
	if len(sys.argv) > 1:
		if sys.argv[1] == "--scheme":
			do_scheme()
		elif sys.argv[1] == "--validate-arguments":
			validate_arguments()
		else:
			pass
	else:
		token=get_token()
		runFoursquareApp(token)
	sys.exit(0)
