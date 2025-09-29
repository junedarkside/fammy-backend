<!-- basic evnv commands -->
source venv/bin/activate                
deactivate 

<!-- django create app -->
pyhton manage.py startapp [appname]

<!-- local dev mode -->
docker-compose -f docker-compose.yml up

<!-- production mode -->
docker-compose -f docker-compose-rds.yml up



<!-- docker logs -->
docker-compose -f docker-compose-backend.yml logs

<!-- after add account model then add AUTH_USER_MODEL = 'Accounts.Account' to login by email then  create super user-->
<!-- create super user -->
docker-compose -f docker-compose.yml run --rm web sh -c "python manage.py createsuperuser"

