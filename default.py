﻿# -*- coding: utf-8 -*-

from resources.lib.handlers import *
import resources.lib.logger
import urlparse
import xbmcaddon

addonhandle = int(sys.argv[1])
addonbaseurl = sys.argv[0]

addonname = addonbaseurl[9:-1]
addon = xbmcaddon.Addon(id=addonname)

logger.addon_debug_enabled = addon.getSetting('debug') == 'true'
logger.notice('Debug logging enabled: ' + str(logger.addon_debug_enabled))

logger.info('Starting addon with {}', sys.argv)
try:
	logger.info('Python version: {}.{}.{}', sys.version_info[0], sys.version_info[1], sys.version_info[2])
except:
	logger.warn('Python version info could not be loaded')

parameters = urlparse.parse_qs(sys.argv[2][1:])

languages = ['en', 'de']
locations = ['int', 'de', 'at']

language = languages[int(addon.getSetting('language'))]
location = locations[int(addon.getSetting('location'))]

baseurl = 'http://www.laola1.tv/' + language + '-' + location + '/'

type = parameters.get('type', ['channel'])[0]

handler = None
if type == 'channel':
	handler = ChannelHandler(addonhandle, addonname, addonbaseurl, parameters, baseurl)
elif type == 'live-block':
	handler = LiveBlockHandler(addonhandle, addonname, addonbaseurl, parameters, baseurl)
elif type == 'block':
	handler = BlockHandler(addonhandle, addonname, addonbaseurl, parameters, baseurl)
elif type == 'video':
	handler = VideoHandler(addonhandle, addonname, addonbaseurl, parameters, baseurl)

handler.handle()
handler.finish()
