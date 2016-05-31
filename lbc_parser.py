# anchor extraction from html document
from bs4 import BeautifulSoup
import urllib.request
import string, re
from pymongo import MongoClient
import gridfs
from datetime import datetime
import sys
import pdfkit


link =[]
title =[]
price = []

if  len(sys.argv) != 4:
    print ('Wrong number of arguments', len(sys.argv))
    print ('usage: lbc_parser.py  <mongodb-host> <mongodb-port> <path to config file>')
    sys.exit(-1)


client = MongoClient('mongodb://' +  sys.argv[1] + ':'+ sys.argv[2] + '/')
db = client['LBC']
coll = db['annonces']

clientGridfs = MongoClient('mongodb://' +  sys.argv[1] + ':'+ sys.argv[2] + '/').LBC_fs
fs = gridfs.GridFS(clientGridfs)


def string_clean(mystr):
    mystr = re.sub(' \s+','',mystr)
    mystr = re.sub('\n+','',mystr)
    mystr = re.sub('\s','_',mystr)
    mystr = re.sub('-','_',mystr)
    mystr = re.sub('\W','',mystr)
    mystr = re.sub('_',' ',mystr)
    return str(mystr)

def int_clean(mystr):
    mystr = string_clean(mystr)
    mystr = re.sub('\D','',mystr)
    return mystr

def is_linked(href):
    return href and re.compile("\d{8}\d*\.htm").search(href)

def extractid(href):
    myid = re.search("\d{8}\d*", href).group(0)
    return str(myid)

def savepdf(url,title,category):
    title = re.sub('[^0-9a-zA-Z]+', '-', title)
    filemane = 'tmp/' + category + '_' + title + '.pdf'
    pdfkit.from_url(url, filemane)

    file = open(filemane, 'rb')
    gridfsid = fs.put( file.read(), filename=filemane)
    return gridfsid

def load_url(data):
    webpage = urllib.request.urlopen(data[0])
    soup = BeautifulSoup(webpage, "html.parser")

    for obj in soup.find_all(href=is_linked):
        link.append(("http:" + obj.get('href')))
        print("append","http:" + obj.get('href'))

    for obj in soup.find_all(class_="item_title"):
        title.append(string_clean(obj.get_text()))

    for obj in soup.find_all(class_="item_price"):
        price.append(int_clean(obj.contents[0]))

    for i in range(0,len(title)) :
        try:
            print(title[i], "\t", price[i], "\t", extractid(link[i]))
        except:
            print("Error", title[i])
            continue
        print("a")
        result = coll.update({"_id": extractid(link[i])},{"$currentDate": {'last': { '$type': 'date' }}},upsert=False)
        result = coll.update({"_id": extractid(link[i])},{"$set" : {"p_cur" : price[i]}},upsert=False)
        # If exists
        if result['n'] == 0 :
            firstdate = datetime.now()
            print("NEW ", result['n'])
            gridfsid = savepdf(link[i], title[i],data[1])
            result = coll.insert({"_id": extractid(link[i]), "url": link[i], "p_init" : price[i] , "t" : title[i], 's' : data[1] ,'first': firstdate, 'gridfs_id' :  gridfsid})

# MAIN
for f in open(sys.argv[3]):
    data = f.split("\t")
    if data[1] :
        data[1] = data[1].rstrip()
        load_url(data)
