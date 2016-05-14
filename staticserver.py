import os
import sys
import subprocess
import urllib2
import datetime
import re

from email.Utils import formatdate
from twisted.web import server, resource
from twisted.web.server import Site
from twisted.web.static import File
from twisted.internet import reactor
from mutagen.mp4 import MP4
from mutagen.mp3 import MP3


audiobooks_path = "/audiobooks"
#audiobooks_path = "/home/hdo/audiobooks"

# prepare files

medialist = []
        
# create feed.xml

#if len(medialist) == 0:
#    print "no media files found!"
#    sys.exit(1)


def url_encode(url):
    return urllib2.quote(url)

def url_decode(url):
    return urllib2.unquote(url)

def generate_feed_xml(host_info, udir, rpath):

    cover_file = os.path.join(udir, 'folder.jpg')
    info_file = os.path.join(udir, 'info.txt')

    medialist = []

    for item in sorted(os.listdir(udir)):
        full_path = os.path.join(udir, item)
        if item.endswith('.m4b') or item.endswith('.m4a'):
            fsize = os.path.getsize(full_path)
            audio = MP4(full_path)
            # set default title, album, title
            title = item
            album = "n.a."
            artist = "n.a."
            if audio.has_key('\xa9nam'):
                title = audio['\xa9nam'][0]
            if audio.has_key('\xa9alb'):
                album = audio['\xa9alb'][0]
            if audio.has_key('\xa9ART'):
                artist = audio['\xa9ART'][0]
            content_type = "audio/m4a"
            #print "%s : %s : %s" % (item,  album, title)
            medialist.append((item, fsize, artist, album, title, content_type))

        if item.endswith('.mp3'):
            fsize = os.path.getsize(full_path)
            audio = MP3(full_path)
            title = audio['TIT2'][0]
            album = audio['TALB'][0]
            artist = audio['TPE1'][0]
            content_type = "audio/mpeg"
            #print "%s : %s : %s" % (item,  album, title)
            medialist.append((item, fsize, artist, album, title, content_type))

    feed_buffer = []
            
    if len(medialist) == 0:
        print "no media files found!"
    else:
        description = ""
        if os.path.exists(info_file):
            for line in open(info_file):
                description = description + line.strip()
                  
        has_cover = os.path.exists(cover_file)


        dt = datetime.datetime(2015, 01, 26, 10, 0, 0)
        pubdate = dt.strftime('%a, %d %b %Y %H:%M:%S CEST')
        ddelta = datetime.timedelta(days=1, minutes=1)
        
                          

        feed_buffer.append('<rss xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" version="2.0">\n')
        feed_buffer.append('  <channel>\n')
        feed_buffer.append('    <title>%s</title> \n' % medialist[0][3].encode('utf8'))
        feed_buffer.append('    <description>%s - %s</description> \n' % (medialist[0][2].encode('utf8'), medialist[0][3].encode('utf8')))
        feed_buffer.append('    <itunes:author>%s</itunes:author> \n' % medialist[0][2].encode('utf8'))
        feed_buffer.append('    <language>de-de</language> \n')
        feed_buffer.append('    <pubDate>%s</pubDate> \n' % pubdate)
        feed_buffer.append('    <lastBuildDate>%s</lastBuildDate> \n' % pubdate)

        dname = os.path.dirname(rpath)
        #if dname.startswith('/'):
        #    dname = dname[1:]
        if has_cover:        
            href_cover = "http://%s/repo/%s/folder.jpg" % (host_info, url_encode(dname))
            feed_buffer.append('    <itunes:image href="%s"/> \n' % href_cover)

        counter = 0
        
        
        for (item, fsize, artist, album, title, content_type) in medialist:        
            counter = counter + 1
            dt = dt + ddelta            
            pubdate = dt.strftime('%a, %d %b %Y %H:%M:%S CEST')

            feed_buffer.append('<item>\n')
            feed_buffer.append('          <itunes:author>%s</itunes:author>\n' % artist.encode('utf8'))
            feed_buffer.append('          <title>%s</title>\n' % title.encode('utf8'))
            use_description = "%s - %s" % (artist.encode('utf8'), title.encode('utf8'))
            if len(description) > 0:
                use_description = description        
            feed_buffer.append('          <description>%s</description>\n' % use_description)
            feed_buffer.append('          <pubDate>%s</pubDate>\n' % (pubdate))
            
            mtype = "application/octet-stream"
            if item.endswith('.m4b'):
                mtype = "audio/aac"
            elif item.endswith('.mp3'):
                mtype = "audio/mp3"
            
            href_audio = "http://%s/repo/%s/%s" % (host_info, url_encode(dname), url_encode(item))
            # dirty hack
            href_audio = href_audio.replace("repo//","repo/")
            print "href_audio: %s" % href_audio
            feed_buffer.append('          <enclosure length="%d" url="%s" type="%s"/>\n' % (fsize, href_audio, content_type))
            feed_buffer.append('</item>\n')
            

        feed_buffer.append('    </channel>\n')
        feed_buffer.append('</rss>\n')

        feed_string = " ".join(feed_buffer)
        return feed_string
    
 
class Home(resource.Resource):
    isLeaf = False
 
    def getChild(self, name, request):
        print "name: %s" % name
        return self
#        if name == '':        
#            return self
#        return resource.Resource.getChild(self, name, request)
 
    def render_GET(self, request):
        #print "uri: %s" % request.uri
        print "host: %s" % request.getHost()
        print "request.path: %s" % request.path

        host_info = request.getHeader('host')

        decoded_url = urllib2.unquote(request.path)

        rpath = decoded_url[1:]        
        print "rpath: %s" % rpath

        upath = audiobooks_path
        if len(rpath) > 0:
            upath = os.path.join(upath, rpath)
            print upath
        
        print "upath: %s" % upath
        
        if rpath.endswith('feed.xml'):
            udir = os.path.dirname(upath)
            print "udir: %s" % udir
            if os.path.exists(udir):
                request.setHeader("Content-Type", "application/xml")
                data = generate_feed_xml(host_info, udir, rpath)
            else:
                data = "Error 401"
        elif os.path.exists(upath):
        
            # check whether folder has playable files

            file_list = sorted(os.listdir(upath))
            has_audiobook = False

            for item in file_list:
                if item.endswith('.mp3'):
                    has_audiobook = True
                if item.endswith('.m4b'):
                    has_audiobook = True
                if item.endswith('.m4a'):
                    has_audiobook = True

            data = "<ul>"

            if has_audiobook:
                item = "feed.xml"
                link = os.path.join(rpath, item)
                encoded_link = urllib2.quote(link)                
                print encoded_link
                data = data + '<li><a href="/%s">%s</a></li>' % (encoded_link, item)                

            for item in file_list:

                # hide hidden files
                if item.startswith('.'):
                    continue

                title = item
                link = os.path.join(rpath, item)
                encoded_link = urllib2.quote(link)                
                #print "link: %s -> %s" % (link, encoded_link)
                full_path = os.path.join(upath, item)
                if os.path.isdir(full_path):
                    data = data + '<li><a href="/%s">%s</a></li>' % (encoded_link, item)
                else:
                    data = data + '<li>%s</li>' % (item)                

            data = data + "</ul>"
        else:
            data = "error: %s" % upath
        return data



root = Home()

if os.path.exists(audiobooks_path):
	root.putChild('repo', File(audiobooks_path, defaultType='application/octet-stream'))
site = server.Site(root)
ip_adr = "localhost"
port = 9090
reactor.listenTCP(port, site)
print "running server at: %s:%d" % (ip_adr, port)
reactor.run()


