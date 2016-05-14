# VariousPython
Couple of python scripts




## lbc_parser
Recuperer les pages du site le boncoin:
lbc_parser.py  <mongodb-host> <mongodb-port> <path to config file>
ex
python3.4 lbc_parser.py localhost 27017 ./conf.txt


##  lbc_server
Une page web hautement dynamique...
lbc_server.py  <mongodb-host> <mongodb-port> <path to config file> <host-port>
python3.4 lbc_server.py localhost 27017 ./conf.txt 8888

### conf.txt exemple
c'est un fichier tabulé
<url>   <Short-name>
http://www.leboncoin.fr/locations/offres/midi_pyrenees/?f=a&th=1&ros=5&ret=1&location=Portet-sur-Garonne%2031120        Loc_Portet
http://www.leboncoin.fr/locations/offres/midi_pyrenees/?f=a&th=1&ros=5&ret=1&location=Saubens%2031600   Loc_Saubens
