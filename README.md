#Python REST API Test: People Segmentation

##Scenario 1
First part is finished.

For testing: GET "http://127.0.0.1:8000/api/location/"

Second part is not finished yet.

That is why there is commented code there.
##For Starting Programm
### First step
Unzip test_people_segmentation.zip to any folder

**Create and activation virtualenv:**

python3 -m venv env

. env/bin/active

**Install requirements:**

cd test_people_segmentation

pip install -r requirements.txt

###Second Step

**Create migrate run webapp**

python manage.py migrate

python manage.py runserver