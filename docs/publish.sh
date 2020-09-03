SSH_USER=mw
WEB_SERVER=www.1wilson.org
WEB_ROOT=/var/www/htdocs/pub/
WEB_CONTENT=./build/html/
WEB_CONTENT_TGZ=./web_content.tgz

tar -C $WEB_CONTENT -czf $WEB_CONTENT_TGZ .
scp $WEB_CONTENT_TGZ $SSH_USER@$WEB_SERVER:
ssh $SSH_USER@$WEB_SERVER doas tar -C $WEB_ROOT -xzf $WEB_CONTENT_TGZ
