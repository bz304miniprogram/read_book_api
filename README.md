# read_book_api\
## build
### The docker-compose.yml shows that port 443 of the host is linked to port 8000 of the docker VM.The registry.cn-hangzhou.aliyuncs.com/bz304/mini_program image expose port 8000 which is listened by nginx in VM. As the .ini file shows, Nginx server redirect the request to uWsgi server in which the Django project runs with .sock file.

### 1.get docker and docker-compose

### 2.pull the docker runtime of env
``` 
sudo docker pull registry.cn-hangzhou.aliyuncs.com/bz304/mini_program
```
### 3.build the image include backends with dockerfile
```
sudo docker build -t [image name] [path of folder contains dockerfile]
```

### 4.docker-compose with docker-compose.yml
```
sudo docker-compose up
```