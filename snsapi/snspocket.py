# -*- coding: utf-8 -*-

'''
snspocket: the container class for snsapi's

'''

# === system imports ===
try:
    import json
except ImportError:
    import simplejson as json
from os.path import abspath

# === snsapi modules ===
import snstype
import utils
from utils import JsonObject
from utils import console_output
from snslog import SNSLog
logger = SNSLog
import plugin

# === 3rd party modules ===

class SNSPocket(dict):
    """The container class for snsapi's"""
    def __init__(self):
        super(SNSPocket, self).__init__()
        self.jsonconf = {}

    def __iter__(self):
        """
        By default, the iterator only return opened channels.
        """
        l = []
        for c in self.itervalues():
            if c.jsonconf['open'] == 'yes':
                l.append(c.jsonconf['channel_name'])
        return iter(l)

    def add(self, jsonconf):
        logger.debug(json.dumps(jsonconf))
        cname = jsonconf['channel_name']
        if cname in self:
            raise errors.SNSPocketDuplicateName
        p = getattr(plugin, jsonconf['platform'])
        c = getattr(p, p._entry_class_)
        if c:
            self[cname] = c(jsonconf)
            #TODO:
            #    This is a work around to store rich 
            #    channel information in the snsapi 
            #    class. The snsapi class should be 
            #    upgrade so that jsonconf is its 
            #    default entrance to access all 
            #    config matters. The current hard 
            #    code attributes are not friendly to
            #    upgrades. Say you have to write one
            #    more assignment if there is one more 
            #    config entry. e.g.
            #    self.open = channel['open']
            self[cname].jsonconf = jsonconf
        else:
            raise errors.NoSuchPlatform

    def read_config(self, \
            fn_channel = 'conf/channel.json',\
            fn_pocket = 'conf/pocket.json'):
        """
        Read configs:
        * channel.conf
        * pocket.conf
        """
        try:
            with open(abspath(fn_channel), "r") as fp:
                allinfo = json.load(fp)
                for site in allinfo:
                    self.add(site)
        except IOError:
            raise errors.NoConfigFile

        try:
            with open(abspath(fn_pocket), "r") as fp:
                allinfo = json.load(fp)
                self.jsonconf = allinfo
        except IOError:
            raise errors.NoConfigFile

        logger.info("read configs done")

    def save_config(self, \
            fn_channel = 'conf/channel.json',\
            fn_pocket = 'conf/pocket.json'):
        """
        Save configs: reverse of read_config

        Configs can be modified during execution. snsapi components 
        communicate with upper layer using Python objects. Pocket 
        will be the unified place to handle file transactions.  
        
        """

        conf_channel = []
        for c in self.itervalues():
            conf_channel.append(c.jsonconf)

        conf_pocket = self.jsonconf

        try:
            json.dump(conf_channel, open(fn_channel, "w"), indent = 2)
            json.dump(conf_pocket, open(fn_pocket, "w"), indent = 2)
        except:
            raise errors.SNSPocketSaveConfigError

        logger.info("save configs done")
        
    def list_channel(self, verbose = False):
        console_output("\n")
        console_output("Current channels:")
        for cname in self.iterkeys():
            c = self[cname].jsonconf
            console_output("   * %s: %s %s" % \
                    (c['channel_name'],c['platform'],c['open']))
            if verbose:
                console_output("    %s" % json.dumps(c))
        console_output("\n")

    def auth(self, channel = None):
        """docstring for auth"""
        if channel:
            self[c].auth()
        else:
            for c in self.itervalues():
                c.auth()

    def home_timeline(self, count = 20, channel = None):
        """
        Route to home_timeline method of snsapi. 
        
        :param channel:
            The channel name. Use None to read all channels
        """
        status_list = snstype.StatusList()
        if channel:
            status_list.extend(self[channel].home_timeline(count))
        else:
            for c in self.itervalues():
                if c.jsonconf['open'] == "yes":
                    status_list.extend(c.home_timeline(count))

        logger.info("Read %d statuses", len(status_list))
        return status_list

    def update(self, text, channel = None):
        """
        Route to update method of snsapi. 
        
        :param channel:
            The channel name. Use None to update all channels
        """
        re = {}
        if channel:
            re[channel] = self[channel].update(text)
        else:
            for c in self.itervalues():
                if c.jsonconf['open'] == "yes":
                    re[c.jsonconf['channel_name']] = c.update(text)

        logger.info("Update status '%s'. Result:%s", text, re)
        return re

    def reply(self, statusID, text, channel = None):
        """
        Route to reply method of snsapi. 
        
        :param channel:
            The channel name. Use None to automatically select
            one compatible channel. 
        """
        re = {}
        if channel:
            re = self[channel].reply(statusID, text)
        else:
            for c in self.itervalues():
                if c.jsonconf['open'] == "yes":
                    if c.jsonconf['platform'] == statusID.platform:
                        re = c.reply(statusID, text)
                        break

        logger.info("Reply to status '%s' with text '%s'. Result: %s",\
                statusID, text, re)
        return re