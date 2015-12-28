__author__ = 'denislavrov'

from cor.api import Message, CORModule
import cor.comm
import struct

try:
	import netifaces
except ImportError:
	print("Netifaces not imported, cannot build a tree")


import ipaddress


def get_ipid():  # TODO ADD PARENTIP parameter here for deeper scanning
	gip, gif = netifaces.gateways()["default"][netifaces.AF_INET]
	addrs = netifaces.ifaddresses(gif)[netifaces.AF_INET]
	for addr in addrs:
		try:
			iface = ipaddress.IPv4Interface("%s/%s" % (addr["addr"], addr["netmask"]))
			if ipaddress.ip_address(gip) in iface.network:
				return struct.pack(">I", int(iface.ip))
		except KeyError:
			pass
	raise Exception("ERROR IPID WAS NOT GENERATED !!! USE MANUAL OVERRIDE !!!")


def topic_shingling(topic):
	# Parse message type tree
	parts = str(topic).split(".")
	shingles = []
	for i in range(0, len(parts)):
		shingles.append(".".join(parts[:i+1]))
	return shingles


class Manager(CORModule):

	def rx_message(self, message):

		def deliverto(to):
			for recipient in to:
				message.dst_from(recipient)
				self.poller.message_out(message)

		for shingle in topic_shingling(message.atype):
			if shingle in self.messageConsumerMap:
				deliverto(self.messageConsumerMap[shingle])
			elif shingle in self.consumes:
				self.consumes[message.atype](message)

		deliverto(self.messageConsumerMap["ALL"])

	def messagein(self, message):
		self.rx_message(message)

	def topic_advertisement(self, message):
		self.consumerset.add(message.src_ipid())
		for mtype in message.payload["consumes"]:
			try:
				self.messageConsumerMap[mtype].add(message.src_ipid())
			except KeyError:
				self.messageConsumerMap[mtype] = {message.src_ipid(), }
			self.messageConsumerMap[""].add(message.src_ipid())
		self.advertise_topics()

	def advertise_topics(self):
		topics = list(filter(lambda x: x not in ["RESPONSE", ""], self.messageConsumerMap.keys()))
		message = Message("TOPIC_ADVERTISEMENT", {"consumes": topics})
		self.messageout(message)

	def connect_to_parent(self, parent):
		if parent is not None:
			self.mid = get_ipid()
			self.connect_to_manager(parent)
			self.advertise_topics()

	def __init__(self, network_adapter=cor.comm.CallbackNetworkAdapter, parent=None, **kwargs):
		CORModule.__init__(self, **kwargs)
		self.poller = network_adapter(self, **kwargs)
		self.consumes.update({"TOPIC_ADVERTISEMENT": self.topic_advertisement})
		self.messageConsumerMap = {"": set(), "ALL": set()}
		self.consumerset = set()
		#self.connect_to_parent(parent)
		self.poller.start()
