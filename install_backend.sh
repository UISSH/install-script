mkdir /usr/local/uissh/ 
cd /usr/local/uissh/ 
git clone https://github.com/UISSH/backend.git
cd backend
virtualenv venv
./venv/bin/pip install -r requirements.txt
cp .env.template .env
./venv/bin/python3 manage.py makemigrations
./venv/bin/python3 manage.py migrate
./venv/bin/python3 manage.py collectstatic --noinput

cd static
wget https://github.com/UISSH/frontend/releases/download/alpha/django_spa.zip -O  "django_spa.zip"
rm -rf common spa
unzip django_spa.zip
mv spa common
