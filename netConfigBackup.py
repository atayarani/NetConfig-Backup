#!/usr/bin/python
###Import Block###
from getpass import getpass,getuser
from time import sleep,time
from os import path,makedirs,listdir,remove,rmdir
from sys import exit
from datetime import datetime
from subprocess import *
from socket import gethostbyname,gethostname
from configobj import ConfigObj
import shutil

import logging,string

###clear old download dirs###
def clear_old_dir(expRate):
        def get_immediate_subdirectories(dir):
            return [name for name in listdir(dir)
                    if path.isdir(path.join(dir, name))]

        basedir = "/tftpboot/"
        dirs = get_immediate_subdirectories(basedir)
        for dir in dirs:
                dir = basedir + dir
                mtime = path.getmtime(dir)
                mtime = int(mtime)
                today = time()
                delta = (today - mtime)
                print(dir)

                if delta > expRate:
			shutil.rmtree(dir)

###Function for Config Import###
def get_config(list,cmd,user_pass,en_pass,ip):
	username="admin"
	for item in list:
		if not path.exists("%s/%s" % (smb_rdir,item)):
			#Pre-run that removes SSH host key first
			Popen(["ssh-keygen","-R",item],stdin=None,stdout=open('/dev/null', 'w'),stderr=open('/dev/null','w'))
			sleep(10)

			p=Popen([cmd, item, user_pass, en_pass, username,ip], stdin=None, stdout=PIPE)
			sleep(30)
			p.stdout.close()
			p.wait()

			if path.exists("%s/%s" % (basedir,item)):
				Popen(["cp", "%s/%s" % (basedir,item), "%s" % smb_rdir]).wait()
				Popen(["rm","-f", "%s/%s" % (basedir,item)]).wait()
				if path.exists("%s/%s" % (smb_rdir,item)):
					logging.info("%s remote transfer complete\n" % item)
					print("%s remote transfer complete\n" % item)
				else:
					logging.error("%s remote transfer failed\n" % item)
			else:
				logging.error("%s local download failed" % item)


		else:
			logging.warning("%s/%s already exists...skipping" % (smb_rdir,item))

def getDevices(model):
        try:
		FILE = eval(config['devicelist'])
        except:
                FILE = config['devicelist']

        infile = open("%s" % FILE)
        result = []
        for line in infile:
                if string.find(line,'#') == -1:
                        fields = line.split(':')
                        if len(fields) >= 2:
                                name = fields[0].rstrip("\r\n")
                                type = fields[1].rstrip("\r\n")

                                if type.lower() == model:
                                        result.append(name)
        return result
###End Functions###

config=ConfigObj("config.ini")
smb_config=config['smb']


###Set TFTP IP###
tftpIP="%s" % gethostbyname(gethostname())

###Get YYYYMMDD date and establish local basedir###
now = datetime.now()
date = now.strftime("%Y%m%d")
tftpdir= "/tftpboot/"
basedir = tftpdir + date

###Before Anything else, remove expired config downloads###
try:
	clear_old_dir(1209600) ##This set the expiration rate @ 2 weeks
except:
        print "Cleanup failed"

###Configure Samba###
try:
	smb_user = eval(smb_config['user'])
except:
	smb_user = smb_config['user']

try:
	smb_dom = smb_config['domain']
except:
        print "Setting Domain failed"
        exit(1)

try:
        smb_password = eval(smb_config['password'])
except:
        print "Setting Password Failed"
        exit(1)

try:
	smb_share = smb_config['share']
except:
        print "Setting Share Failed"
        exit(1)

try:
        smb_mount = smb_config['mount']
except:
        print "Setting Mount Point Failed"
        exit(1)

try:
	smb_rdir = eval(smb_config['remote_dir'])
except:
	smb_rdir = smb_config['remote_dir']

###Mount Share###
Popen(["sudo","mount", "-t", "cifs", "-o", "username=%s,domain=%s,password=%s" % (smb_user,smb_dom,smb_password), "%s" % smb_share, "%s" % smb_mount])


###Prompt for device passwords###
pass_config=config['passwords']
try:
	netdev_user_pass = eval(pass_config['user'])
except:
	netdev_user_pass = pass_config['user']

try:
        netdev_en_pass = eval(pass_config['enable'])
except:
        netdev_en_pass = pass_config['enable']

try:
        voipdev_en_pass = eval(pass_config['voip'])
except:
        voipdev_en_pass = pass_config['voip']

try:
        san_pass = eval(pass_config['san'])
except:
        san_pass = pass_config['san']

###Expect Scripts###
exp_path = "/usr/local/bin/"
##Cisco##
ios_cmd = exp_path + "getIOS.exp"
fos_cmd = exp_path + "getFOS.exp"
nxos_cmd = exp_path + "getNXOS.exp"
nxos_san_cmd = exp_path + "getNXOS-SAN.exp"
iosxe_cmd = exp_path + "getIOSXE.exp"

##Force10##
ftos_cmd = exp_path + "getFTOS.exp"
sftos_cmd = exp_path + "getSFTOS.exp"

##Others##
ent_cmd = exp_path + "getEnt.exp"
dell_cmd = exp_path + "getDell.exp"
dellv2_cmd = exp_path + "getDellv2.exp"

###Device List By OS###
##Cisco
ios = getDevices("ios")
iosxe = getDevices("iosxe")
fos = getDevices("fos")
nxos = getDevices("nxos")
nxos_san = getDevices("ciscosan")
voip = getDevices("voip")

##Force10
sftos = getDevices("sftos")
ftos = getDevices("ftos")

##Enterasys
ent = getDevices("ent")

##Dell
dell = getDevices("dell")
dellv2 = getDevices("dellv2")

###Create TFTP Path###
if not path.exists(basedir):
	Popen(["mkdir", basedir])
	Popen(["sudo", "chown", "nobody", basedir])

###Create Remote Path###
if not path.exists(smb_rdir):
	makedirs(smb_rdir)

###Configure Logging###
LOG = "%s/runlog.txt" % smb_rdir
logging.basicConfig(filename=LOG,level=logging.INFO,filemode='w',format="%(asctime)s - %(levelname)s - %(message)s")

###Config Import###
##Cisco##
get_config(ios,ios_cmd,netdev_user_pass,netdev_en_pass,tftpIP)
get_config(fos,fos_cmd,netdev_user_pass,netdev_en_pass,tftpIP)
get_config(nxos,nxos_cmd,netdev_user_pass,netdev_en_pass,tftpIP)
get_config(nxos_san,nxos_san_cmd,san_pass,netdev_en_pass,tftpIP)
get_config(voip,ios_cmd,netdev_user_pass,voipdev_en_pass,tftpIP)
get_config(iosxe,iosxe_cmd,netdev_user_pass,netdev_en_pass,tftpIP)
##Force10##
get_config(ftos,ftos_cmd,netdev_user_pass,netdev_en_pass,tftpIP)
#get_config(sftos,sftos_cmd,netdev_user_pass,netdev_en_pass,tftpIP)
##Others##
get_config(ent,ent_cmd,netdev_user_pass,netdev_en_pass,tftpIP)
get_config(dell,dell_cmd,netdev_user_pass,netdev_en_pass,tftpIP)
get_config(dellv2,dellv2_cmd,netdev_user_pass,netdev_en_pass,tftpIP)
