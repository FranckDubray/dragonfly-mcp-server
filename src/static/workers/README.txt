Cette arborescence /src/static/workers contient les assets front si le serveur est configuré pour monter /static depuis src/static. 
Dans ce projet, le montage est depuis src/static par défaut (voir src/app_server/static_mount.py). 
Nous servons les JS/CSS depuis /static/workers/*.js|*.css.
Les fichiers ont été écrits dans src/web/static/workers/ pour séparer build et serve ; si besoin, dupliquez ou montez /web/static comme /static.
