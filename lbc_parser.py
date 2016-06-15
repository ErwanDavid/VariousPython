# anchor extraction from html document
from bs4 import BeautifulSoup
import urllib.request
import string, re
from pymongo import MongoClient
import gridfs
from datetime import datetime
import sys
import pdfkit
import pprint

if  len(sys.argv) != 4:
    print ('Wrong number of arguments', len(sys.argv))
    print ('usage: lbc_parser.py  <mongodb-host> <mongodb-port> <path to config file>')
    sys.exit(-1)

pp = pprint.PrettyPrinter(indent=4)
client = MongoClient('mongodb://' +  sys.argv[1] + ':'+ sys.argv[2] + '/')
db = client['LBC3']
coll = db['annonces']

clientGridfs = MongoClient('mongodb://' +  sys.argv[1] + ':'+ sys.argv[2] + '/').LBC3_fs
fs = gridfs.GridFS(clientGridfs)


def string_clean(mystr):
    mystr = re.sub('\s+', ' ', mystr)
    mystr = re.sub('[^A-Za-z0-9 ]+', '', mystr)
    return str(mystr)

def int_clean(mystr):
    mystr = string_clean(mystr)
    mystr = re.sub('\D','',mystr)
    return mystr

def is_linked(href):
    if href == ''  or href == None:
        return False
    #print('URL test', href)
    return href and re.compile("\d{8}\d*\.htm").search(href)

def extractid(href):
    myid = re.search("\d{8}\d*", href).group(0)
    return str(myid)

def savepdf(url,title,category,annid):
    title = re.sub('[^0-9a-zA-Z]+', '-', title)
    filemane = 'tmp/' + annid +'_' + category + '_' + title + '.pdf'
    pdfkit.from_url(url, filemane)

    file = open(filemane, 'rb')
    gridfsid = fs.put( file.read(), filename=filemane)
    return gridfsid

def load_url(data):
    webpage = urllib.request.urlopen(data[0])
    soup = BeautifulSoup(webpage, "html.parser")
    link =[]
    title =[]
    price = []
    
    cpt_l = 0
    for obj in soup.find_all(href=is_linked):
        link.append(("http:" + obj.get('href')))
        cpt_l=cpt_l +1
        print(data[1],' ', cpt_l, "BS_link","http:" + obj.get('href'))
    cpt_t = 0
    for obj in soup.find_all(class_="item_title"):
        title.append(string_clean(obj.get_text()))
        cpt_t=cpt_t +1
        print(data[1],' ', cpt_t, "BS_title",string_clean(obj.get_text()))
    cpt_p = 0
    for obj in soup.find_all(class_="item_price"):
        price.append(int_clean(obj.contents[0]))
        cpt_p=cpt_p +1
        print(data[1],' ', cpt_p, "BS_price", int_clean(obj.contents[0]))

    if cpt_l != cpt_p or cpt_l != cpt_t or cpt_p != cpt_t:
        print ("ERROR in parsing")
        return
    for i in range(0,len(title)) :
        try:
            curId = data[1] + '_' + extractid(link[i])
            print(data[1],'SUMUP title', title[i], "\t price", price[i], "\t ID ", curId)
        except:
            print(data[1],' ',"ERROR during extract ", title[i], "price", price[i])
            return
        print(data[1],' ',"Try Update",  curId, "title", title[i] )
        result = coll.update({"_id": curId},{"$currentDate": {'last': { '$type': 'date' }}},upsert=False)
        result = coll.update({"_id": curId},{"$set" : {"p_cur" : price[i]}},upsert=False)
        print(data[1],' ',"Update result",  result['n'] )
        if result['n'] == 0 :
            firstdate = datetime.utcnow()
            print(data[1],' ',"INSERT", curId, "title", title[i],'price', price[i] )
            gridfsid = savepdf(link[i], title[i],data[1],curId)
            #gridfsid = 'fake'
            insert = {"_id": curId, "url": link[i], "p_init" : price[i] , "t" : title[i], 's' : data[1] ,'first': firstdate, 'gridfs_id' :  gridfsid}
            #pp.pprint(insert)
            coll.insert(insert)

# MAIN
for f in open(sys.argv[3]):
    if f.startswith('#'):
        continue
    data = f.split("\t")
    if data[1] :
        data[1] = data[1].rstrip()
        load_url(data)
