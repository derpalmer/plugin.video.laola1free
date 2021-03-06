﻿# -*- coding: utf-8 -*-

import urllib2
import re
import string
import random
import time
from urlparse import urljoin
from bs4 import BeautifulSoup
import logger

class StreamError(Exception):
	def __init__(self, message):
		self.message = message

class Stream:
	def __init__(self, url, settings, min_bandwidth = 0, max_bandwidth = 999999999):
		self.min_bandwidth = min_bandwidth
		self.max_bandwidth = max_bandwidth
		self.settings = settings

		logger.info('Get videoplayer url from "{}"', url)
		url = self.get_videoplayer_url(url)
		logger.debug('Get stream details url from "{}"', url)
		url = self.get_details_url(url)
		logger.debug('Get playlist url from "{}"', url)
		self.url = self.get_playlist_url(url)
		logger.debug('Playlist url is "{}"', self.url)

	def get_soup(self, url):
		proxy = urllib2.ProxyHandler({'http': self.settings.proxyserver(), 'https': self.settings.proxyserver()})
		opener = urllib2.build_opener(proxy)
		urllib2.install_opener(opener)
		source = urllib2.urlopen(url)
		soup = BeautifulSoup(source, 'html.parser')
		soup.current_url = source.geturl()
		return soup

	def get_videoplayer_url(self, url):
		soup = self.get_soup(url)

		# TODO some more info maybe?
		self.title = soup.select('title')[0].get_text().strip().encode('utf-8')

		iframes = soup.select('iframe[src*=player]')

		if len(iframes) != 1:
			raise StreamError(self.find_error_reason(soup))

		return urljoin(soup.current_url, iframes[0]['src'])

	def find_error_reason(self, soup):
		countdown = soup.select('.live_countdown')
		print countdown
		if countdown and countdown[0]['data-nstreamstart']:
			# 2016-3-19-20-30-00
			date = countdown[0]['data-nstreamstart'].encode('utf-8')
			datetime = time.strptime(date, '%Y-%m-%d-%H-%M-%S')
			date = '[B]' + time.strftime('%a, %H:%M', datetime) + '[/B]'
			return 'Stream not yet started![CR]Stream start: ' + date

		return 'Videoplayer not found!'

	def get_details_url(self, url):
		source = urllib2.urlopen(url)
		content = source.read()
		source.close()

		streamid = re.compile('streamid: "(.+?)"', re.DOTALL).findall(content)[0]
		partnerid = re.compile('partnerid: "(.+?)"', re.DOTALL).findall(content)[0]
		portalid = re.compile('portalid: "(.+?)"', re.DOTALL).findall(content)[0]
		sprache = re.compile('sprache: "(.+?)"', re.DOTALL).findall(content)[0]
		auth = re.compile('auth = "(.+?)"', re.DOTALL).findall(content)[0]
		timestamp = ''.join(re.compile('<!--.*?([0-9]{4})-([0-9]{2})-([0-9]{2}) ([0-9]{2}):([0-9]{2}):([0-9]{2}).*?-->', re.DOTALL).findall(content)[0])

		hdvideourl = 'http://www.laola1.tv/server/hd_video.php?play='+streamid+'&partner='+partnerid+'&portal='+portalid+'&v5ident=&lang='+sprache

		logger.debug('hd_video url is "{}"', hdvideourl)
		soup = self.get_soup(hdvideourl)

		return soup.videoplayer.url.text +'&timestamp='+timestamp+'&auth='+auth

	def char_gen(self, size=1, chars=string.ascii_uppercase):
		return ''.join(random.choice(chars) for x in range(size))

	def get_playlist_url(self, url):
		soup = self.get_soup(url)

		auth = soup.data.token['auth']
		url = soup.data.token['url']

		baseurl = url.replace('/z/', '/i/')
		return urljoin(baseurl, 'master.m3u8?hdnea=' + auth + '&g=' + self.char_gen(12) + '&hdcore=3.8.0')

	def get_title(self):
		return self.title

	def get_url(self):
		return self.url

	def get_playlist(self):
		streamurl = self.get_url()
		source = urllib2.urlopen(streamurl)
		master = source.read()
		source.close()

		playlist = '#EXTM3U\n'

		for header, bandwidth, url in re.compile('(BANDWIDTH=(.+?),.+?)\n(.+?)\n', re.DOTALL).findall(master):
			bandwidth = int(bandwidth)
			if self.min_bandwidth < bandwidth and bandwidth <= self.max_bandwidth:
				playlist += header + '\n' + urljoin(streamurl, url) + '\n'

		return playlist
