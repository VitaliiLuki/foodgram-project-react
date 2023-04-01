![example workflow](https://github.com/VitaliiLuki/foodgram-project-react/actions/workflows/foodgram_workflow.yaml/badge.svg)

[![Python](https://img.shields.io/badge/-Python-464646?style=flat-square&logo=Python)](https://www.python.org/)
[![Django](https://img.shields.io/badge/-Django-464646?style=flat-square&logo=Django)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/-Django%20REST%20Framework-464646?style=flat-square&logo=Django%20REST%20Framework)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-464646?style=flat-square&logo=PostgreSQL)](https://www.postgresql.org/)
[![Nginx](https://img.shields.io/badge/-NGINX-464646?style=flat-square&logo=NGINX)](https://nginx.org/ru/)
[![gunicorn](https://img.shields.io/badge/-gunicorn-464646?style=flat-square&logo=gunicorn)](https://gunicorn.org/)
[![docker](https://img.shields.io/badge/-Docker-464646?style=flat-square&logo=docker)](https://www.docker.com/)
[![GitHub%20Actions](https://img.shields.io/badge/-GitHub%20Actions-464646?style=flat-square&logo=GitHub%20actions)](https://github.com/features/actions)
[![Yandex.Cloud](https://img.shields.io/badge/-Yandex.Cloud-464646?style=flat-square&logo=Yandex.Cloud)](https://cloud.yandex.ru/)

Foodgram реализован для публикации рецептов. Авторизованные пользователи могут подписываться на понравившихся авторов, добавлять рецепты в избранное, в покупки, скачать список покупок ингредиентов для добавленных в покупки рецептов.

# Запуск проекта

### Склонировать репозиторий на локальную машину:

```
https://github.com/VitaliiLuki/foodgram-project-react
```

### Для работы с удаленным сервером (на ubuntu):

* Выполните вход на свой удаленный сервер.

* Установите docker на сервер:

```
sudo apt install docker.io 
```

* Установите docker-compose на сервер:

```
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

* Отредактируйте контекст файла infra/nginx/nginx.conf, в строке server_name впишите свой IP удаленного сервера.

* Создайте в корне сервера /home/<server_username>/ папку nginx.
* Скопируйте файл docker-compose.yml и nginx.conf из директории infra на сервер:

```
scp docker-compose.yml <username>@<host>:/home/<server_username>/docker-compose.yml
```
  
```  
scp nginx/nginx.conf <username>@<host>:/home/<server_username>/nginx/nginx.conf
```
  
* Cоздайте .env файл и впишите:

```
DB_ENGINE=<django.db.backends.postgresql>

DB_NAME=<имя базы данных postgres>

DB_USER=<пользователь бд>

DB_PASSWORD=<пароль>

DB_HOST=<db_postgres>

DB_PORT=<5432>

SECRET_KEY=<секретный ключ проекта django>
```
  
### Создайте и запуште образы frontend и backend на Docker Hub
  
```
cd backend/foodgram_backend
```
```
docker build -t <dockerhub_username>/foodgram_backend:latest .
```
```
docker login -u <dockerhub_username> 
```
```
docker push <dockerhub_username>/foodgram_backend:latest 
```

```
cd frontend
```
```
docker build -t <dockerhub_username>/foodgram_frontend:latest .
```
```
docker push <dockerhub_username>/foodgram_frontend:latest 
```

* Для сборки образов и запуска контейнеров на сервере из дериктории /home/<server_username>/ выполните команду:

```
sudo docker-compose up -d
```

### После успешной сборки на сервере выполните команды (только после первого деплоя):

* Соберите статические файлы:

```
sudo docker-compose exec backend python manage.py collectstatic
```

* Примените миграции:

```
sudo docker-compose exec web python manage.py migrate
```

* Загрузите ингридиенты в базу данных (необязательно):

```
sudo docker-compose exec web python manage.py load_data
```

* Создать суперпользователя Django:

```
sudo docker-compose exec backend python manage.py createsuperuser
```

* После сборки и деплоя на удаленном сервере сайт будет доступен по вашему IP.
* Эндоинты для API можно посмотреть по адресу /api/docs.


#### Для работы с Workflow добавьте в Settings -> Secrets and variables -> Actions переменные окружения для работы:

Примеры и определения переменных указаны в файле infra/.env.sample.



#### Ознакомиться с рабочей версией сайта можно [тут](http://158.160.55.187/).

#### Логин и пароль для админа на время ревью:
login: admin

password: admin
