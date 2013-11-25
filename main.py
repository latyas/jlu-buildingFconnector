import sys
import socket
import ping
import socket
import urllib2
import platform
import time
import os,subprocess
import sqlite3

ERROR = {
	'logined':'This ip has logined.',
	'unavailable':'IP is unavailable, getting again',
	'dropped':'Packets dropped, reseting ip',
	'vpn_not_connect':'vpn connection was not established.'
}

def set_network_windows(ip,mac):
	device_id = 'DEV_8139'
	mac = mac
	network_card_id = '0001'
	connection_name = "1015"

	import win32api, win32con
	key = win32api.RegOpenKey(win32con.HKEY_LOCAL_MACHINE,r'SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002bE10318}\%s' % network_card_id,0, win32con.KEY_ALL_ACCESS)
	win32api.RegSetValueEx(key,'networkaddress',0,win32con.REG_SZ,mac)
	print 'restarting network'
	subprocess.call('netsh interface ip set address %s static %s 255.255.255.0 %s 1' % (connection_name,ip,get_gateway(ip)))
	print 'started.'

def set_network_linux(ip,mac):
	network_card_id = 'eth0'

	# delete default gateway for now
	current_ip = socket.gethostbyname_ex(socket.gethostname())[2][0]
	current_gateway = get_gateway(current_ip)
	print 'Delete old gateway ',current_gateway
	subprocess.call(['route','del','default','gw',current_gateway])

	current_ip = ip
	current_gateway = get_gateway(current_ip)
	print 'Add new gateway ',current_gateway
	subprocess.call(['route','add','default','gw',current_gateway])

	print 'Setting new ip and mac',ip,mac
	# set ip and mac
	subprocess.call(['ifconfig','eth0',ip,'netmask','255.255.255.0','hw','ether',get_linux_mac(mac)])

	print 'Restarting Network'
	subprocess.call(['service','network','restart'])
def get_linux_mac(mac):
	foo = ''
	for i,j in enumerate(mac):
		foo += j
		if (i+1) % 2 == 0:
			foo += ':'
	return foo[:-1]
def connect_vpn(vpn,username='',password=''):
	if platform.system() == 'Windows':
		subprocess.call(['rasdial',vpn,username,password])
	else:
		subprocess.call(['nmcli','con','up','id',vpn])

def disconnect_vpn(vpn):
	if platform.system() == 'Windows':
		if 'Connected' in subprocess.check_output(["rasdial"]):
			subprocess.call(['rasdial',vpn,'/disconnect'])
		else:
			print ERROR['vpn_not_connect']
	else:
		subprocess.call(['nmcli','con','down','id',vpn])

def check_after_set():
	keyword = 'time='
	auth_rul = 'http://10.100.61.3'
	context = urllib2.urlopen(auth_rul).read()
	if keyword in context:
		return True

def check_connection(ip):
	ping_count = ping.count_ping(ip)
	if ping_count > 0:
		return True

	check_ports = [135,139,445,61440]
	timeout = 0.2 #second

	for i in check_ports:
		try:
			socket.create_connection((ip,ports),timeout)
			return false
		except:
			pass

def get_gateway(ip):
	foo = ip.split('.')
	foo[3] = '254'
	gateway = foo[0] + '.' + foo[1] + '.' + foo[2] + '.' + foo[3]
	return gateway
def check_state():
	gateway = get_gateway(socket.gethostbyname_ex(socket.gethostname())[2][0])
	if ping.count_ping(gateway,0.2,10) < 8:
		print ERROR['dropped']
	return True

def get_an_ip(cursor,area):
	sql = 'SELECT * FROM jlu where netarea = \"' + area + '\" ORDER BY RANDOM() LIMIT 1;'
	inquery = cursor.execute(sql).fetchall()
	ip, mac = inquery[0][8],inquery[0][9]
	print 'choose:',
	print inquery[0][2]
	print ip,mac
	return (ip,mac)

if __name__ == '__main__':
	vpn = 'dormitory'
	vpn_username = 'vpnusername'
	vpn_password = 'vpnpassword'
	db = sqlite3.connect('data.db')
	cursor = db.cursor()

	while True:
		# check ip first
		if check_state():
			disconnect_vpn(vpn)
			# get ip from database
			ip, mac = get_an_ip(cursor, '\xE5\xA4\xA7\xE5\xAD\xA6\xE5\x9F\x8E\xE4\xBA\x8C\xE5\x85\xAC\xE5\xAF\x93')
			# set ip
			if platform.system() == 'Windows':
				set_network_windows(ip,mac)
			else:
				set_network_linux(ip,mac)
			# check if ip is available
			if ping.count_ping('10.100.61.3',0.5,2) == 0:
				print ERROR['unavailable']
				continue
			# if target has logon
			if check_after_set():
				print ERROR['logined']
				continue
			# success
			connect_vpn(vpn,vpn_username,vpn_password)
		time.sleep(5000)
		print
