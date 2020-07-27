import time
import networkx as netw
import unicodedata
from sys import exit

def deviceInformation(data):
	global switch
	global MACaddress
	global hostPorts
	switchDPID = ""
	for i in data:
		if(i['ipv4']):
			ip = i['ipv4'][0].encode('ascii','ignore')
			mac = i['mac'][0].encode('ascii','ignore')
			MACaddress[ip] = mac
			for j in i['attachmentPoint']:
				for key in j:
					temp = key.encode('ascii','ignore')
					if(temp=="switchDPID"):
						switchDPID = j[key].encode('ascii','ignore')
						switch[ip] = switchDPID
					elif(temp=="port"):
						portNumber = j[key]
						switchShort = switchDPID.split(":")[7]
						hostPorts[ip+ "::" + switchShort] = str(portNumber)


#function for finding route to a switch
def RouteFind():
	pathKey = ""
	nodes = []
	source = int(switch[h2].split(":",7)[7],16)
	destination = int(switch[h1].split(":",7)[7],16)

	print source
	print destination
	
	for currentPath in netw.all_shortest_paths(G, source=source, target=destination, weight=None):
		for node in currentPath:

			temp= ""
			if node < 17:
				pathKey = pathKey + "0" + str(hex(node)).split("x",1)[1] + "::"
				temp= "00:00:00:00:00:00:00:0" + str(hex(node)).split("x",1)[1]
			else:
				pathKey = pathKey + str(hex(node)).split("x",1)[1] + "::"
				temp= "00:00:00:00:00:00:00:" + str(hex(node)).split("x",1)[1]
			nodes.append(temp)

		pathKey=pathKey.strip("::")
		path[pathKey] = nodes
		pathKey = ""
		nodes = []

	print path



def LinkRate(data,key):
	global cost
	port = linkPorts[key]
	port = port.split("::")[0]
	for j in data:
		if j['port']==port:
			cost = cost + (int)(j['bps'])


# Method To Compute Link Cost

def FindLink():
	global portKey
	global cost

	for key in path:
		start = switch[h2]
		source = switch[h2]
		srcID = source.split(":")[7]
		mid = path[key][1].split(":")[7]
		for link in path[key]:
			temp = link.split(":")[7]

			if srcID==temp:
				continue
			else:
				portKey = srcID + "::" + temp
				srcID = temp
				source = link
		portKey = start.split(":")[7] + "::" + mid + "::" + switch[h1].split(":")[7]
		finalrate[portKey] = cost
		cost = 0
		portKey = ""


def ValOfFlow(PresentNode, flowCount, PortIN, PortOUT):
	flow = {
		'switch':"00:00:00:00:00:00:00:" + PresentNode,
	    "name":"flow" + str(flowCount),
	    "cookie":"0",
	    "priority":"32768",
	    "in_port":PortIN,
		"eth_type": "0x0800",
		"ipv4_source": h2,
		"ipv4_destination": h1,
		"eth_source": MACaddress[h2],
		"eth_destination": MACaddress[h1],
	    "active":"true",
	    "actions":"output=" + PortOUT
	}

	flowCount = flowCount + 1

	flow = {
		'switch':"00:00:00:00:00:00:00:" + PresentNode,
	    "name":"flow" + str(flowCount),
	    "cookie":"0",
	    "priority":"32768",
	    "in_port":PortOUT,
		"eth_type": "0x0800",
		"ipv4_source": h1,
		"ipv4_destination": h2,
		"eth_source": MACaddress[h1],
		"eth_destination": MACaddress[h2],
	    "active":"true",
	    "actions":"output=" + PortIN
	}



def NewPath():

	flowCount = 1

	shortestPath = min(finalrate, key=finalrate.get)
	print "\n\nShortest Path: ",shortestPath


	PresentNode = shortestPath.split("::",2)[0]
	nextNode = shortestPath.split("::")[1]

	# Finding Port
	port = linkPorts[PresentNode+"::"+nextNode]
	PortOUT = port.split("::")[0]
	PortIN = hostPorts[h2+"::"+switch[h2].split(":")[7]]

	ValOfFlow(PresentNode,flowCount,PortIN,PortOUT)

	flowCount = flowCount + 2
	bestPath = path[shortestPath]
	previousNode = PresentNode

	for PresentNode in range(0,len(bestPath)):
		if previousNode == bestPath[PresentNode].split(":")[7]:
			continue
		else:
			port = linkPorts[bestPath[PresentNode].split(":")[7]+"::"+previousNode]
			PortIN = port.split("::")[0]
			PortOUT = ""
			if(PresentNode+1<len(bestPath) and bestPath[PresentNode]==bestPath[PresentNode+1]):
				PresentNode = PresentNode + 1
				continue
			elif(PresentNode+1<len(bestPath)):
				port = linkPorts[bestPath[PresentNode].split(":")[7]+"::"+bestPath[PresentNode+1].split(":")[7]]
				PortOUT = port.split("::")[0]
			elif(bestPath[PresentNode]==bestPath[-1]):
				PortOUT = str(hostPorts[h1+"::"+switch[h1].split(":")[7]])

			ValOfFlow(bestPath[PresentNode].split(":")[7],flowCount,str(PortIN),str(PortOUT))
			flowCount = flowCount + 2
			previousNode = bestPath[PresentNode].split(":")[7]

# Method To Perform Load Balancing
def loadbalance():

	RouteFind()
	FindLink()
	NewPath()

# Stores H1 and H2 from user
global h1,h2,h3

h1 = ""
h2 = ""

print "Enter Host 1: "
h1 = int(input())
print "\nEnter Host 2: "
h2 = int(input())
print "\nEnter Host 3 (Host adjacent to H2)"
h3 = int(input())

h1 = "10.0.0." + str(h1)
h2 = "10.0.0." + str(h2)
h3 = "10.0.0." + str(h3)


while True:

	# H3-H4 swtich details
	switch = {}

	# Mac address of H3 And H4
	MACaddress = {}

	# Stores Host Switch Ports
	hostPorts = {}

	# Stores Switch To Switch Path
	path = {}

	# Switch Links
	switchLinks = {}

	# Stores Link Ports
	linkPorts = {}

	# Stores Final Link Rates
	finalrate = {}

	# Store Port Key For Finding Link Rates
	portKey = ""

	# Initiating a new Graph
	G = netw.Graph()

	try:

		loadbalance()

		print "Switch H4 is: ",switch[h3], "\tSwitch H3 is: ", switch[h2]
		print "\n\nSwitch H1: ", switch[h1]
		print "\nIP & MAC\n\n", MACaddress
		# Link Ports
		print "\nLink Ports (source::destination - source PORT::destination PORT)\n\n", linkPorts
		# Alternative Path found
		print "\nPaths (source TO destination)\n\n",path
		time.sleep(45)

	except KeyboardInterrupt:
		break
		exit()
