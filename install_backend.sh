mkdir /usr/local/uissh/ 
cd /usr/local/uissh/ && git clone https://github.com/UISSH/backend.git
cd /usr/local/uissh/backend && virtualenv venv
/usr/local/uissh/backend/venv/bin/pip install -r requirements.txt
cp /usr/local/uissh/backend/.env.template /usr/local/uissh/backend/.env
/usr/local/uissh/backend/venv/bin/python3 manage.py makemigrations
/usr/local/uissh/backend/venv/bin/python3 manage.py migrate
/usr/local/uissh/backend/venv/bin/python3 manage.py collectstatic --noinput

cd /usr/local/uissh/backend/static  && \
wget https://github.com/UISSH/frontend/releases/download/alpha/django_spa.zip -O  "django_spa.zip" && \
rm -rf common spa && \
unzip django_spa.zip && \
mv spa common
