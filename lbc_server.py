from  http.server import BaseHTTPRequestHandler,HTTPServer
import urllib
import pymongo
from pymongo import MongoClient
import gridfs
from bson.objectid import ObjectId
import re
import time
import cgi
import sys
import pprint
from unicodedata import normalize

if  len(sys.argv) != 5:
    print ('Wrong number of arguments')
    print ('usage: lbc_server.py  <mongodb-host> <mongodb-port> <path to config file> <host-port>')
    sys.exit(-1)

PORT_NUMBER = int(sys.argv[4])
pp = pprint.PrettyPrinter(indent=4)


client = MongoClient('mongodb://' +  sys.argv[1] + ':'+ sys.argv[2] + '/')
#client = MongoClient('mongodb://' +  'minty' + ':'+ '27017' + '/')
db = client['LBC']
coll = db['annonces']
#coll = db['mini']

clientGridfs = MongoClient('mongodb://' +  sys.argv[1] + ':'+ sys.argv[2] + '/').LBC_fs
fs = gridfs.GridFS(clientGridfs)

class GetHandler(BaseHTTPRequestHandler):
    def get_url(self):
        urldic={}
        for f in open(sys.argv[3]):
        #for f in open('C:/Users/edavid/hubiC/Prog/pyhtmlparser/conf.txt'):
            data = f.split("\t")
            if data[1] :
                data[1] = data[1].rstrip()
                urldic[data[1]] = data[0]
        return urldic

    def print_html(self):
        urldic = self.get_url()
        message = '<html><head></head><body>'
        message = message +     '<h2>LBC</h2>'
        message = message +     '<form  method="post">\n\n'
        message = message +     '<table><tr><td valign="top"><select name="select">\n'
        for url in sorted(urldic):
            message = message +     '<option value="' + url + '|' + urldic[url] + '">' +  url + '</option>\n'
        message = message +     '</select> </td>\n'
        message = message +     '<td valign="top"><input type="radio" name="order" value="last" checked>Vendus en premier<br><input type="radio" name="order" value="first">Vers le plus Recent<br>\n'
        #message = message +     'price: <input type="number" name="price" value=""><br>\n'
        message = message +     '<input type="submit" value="Submit"></td></tr></table></form>\n'
        message = message +     '</body></html>'

        return message



    def do_GET(self):
        if "/files" in self.path :
            parsed_path = self.path.split('/')[2]
            print("parsed_path", parsed_path)
            f = fs.get(ObjectId(parsed_path))
            self.send_response(200)
            mimetype='application/pdf'
            self.send_header('Content-type',mimetype)
            self.end_headers()
            self.wfile.write(f.read())

        else :
            page_html = self.print_html()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(bytes(page_html, "utf-8"))
        return


    def do_POST(self):
        if (True) :
            page_html = '<html><head>'\
                      + '</head>\n<body>\n'
            length = int(self.headers['content-length'])
            postvars = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
            print ('postvars', postvars)
            select = postvars[b'select'][0].decode("utf-8").split('|')[0]
            url = postvars[b'select'][0].decode("utf-8").split('|')[1]
            order = postvars[b'order'][0].decode("utf-8") 
            if order in 'last':
                disorder = 'first'
            else:
                disorder = 'last'
            
            print ('order', order)
            print ('select', select)
            cursor = coll.find({'s' : select}).sort([(order, pymongo.ASCENDING),(disorder, pymongo.DESCENDING)])
            
            table_html = '<a href="' + url + '">' + url +'</a>\n<br><br>\n<table border="1"><tr>'
            cpt = 0

            for annonce in cursor:
                cpt += 1
                pp.pprint(annonce)
                text = annonce['t']
                #text = normalize('NFKD', text).encode('ASCII', 'ignore')
                print("last", annonce['last'])
                table_html = table_html + '<td>\n<a target="_blank" href="' + annonce['url']+ '"> ' 
                table_html = table_html +  text + "</a><br>"
                table_html = table_html +  annonce['p_cur'] + " eur <br>" 
                if 'gridfs_id' in annonce.keys():
                    table_html = table_html +  '<a target="_blank" href="/files/' + str(annonce['gridfs_id']) + '">Archive pdf</a><br>' 
                table_html = table_html +  "<br>" + annonce['s']
                table_html = table_html +  "<br>" + str(annonce['first']) + "<br>" 
                table_html = table_html + str(annonce['last']) +"</td>"
                modulo = cpt % 5
                if(modulo == 0):
                     table_html = table_html + "</tr>\n<tr>"
            table_html += '</tr></table>\n'

            page_html = page_html + '<h2>Count :' + str(cpt) + '</h2>\n'
            page_html = page_html + table_html
            page_html = page_html + '</body></html>'
            self.send_response(200)
            self.end_headers()
            self.wfile.write(bytes(page_html, "utf-8"))
        return



if __name__ == '__main__':
    try:
        #Create a web server and define the handler to manage the
        #incoming request
        server = HTTPServer(('', PORT_NUMBER), GetHandler)
        print ('Started httpserver on port', PORT_NUMBER)
        #Wait forever for incoming htto requests
        server.serve_forever()
    except KeyboardInterrupt:
        print ('^C received, shutting down the web server')
        server.socket.close()
