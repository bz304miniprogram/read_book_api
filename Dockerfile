#Dockerfile

#Base image
FROM registry.cn-hangzhou.aliyuncs.com/bz304/mini_program:latest

# Local directory with project source
#ENV DOCKER_SRC=mini_program_api
# Directory in container for all project files
#ENV DOCKER_HOME=/root
# Directory in container for project source files
#ENV DOCKER_PROJECT=/root/project

# Create application subdirectories
#WORKDIR $DOCKER_HOME
#RUN mkdir media static

#VOLUME ["$DOCKER_HOME/media/"]

# Install required packages and remove the apt packages cache when done.
#RUN yum -y install epel-release && \
#    yum -y install python-pip && \
#    yum -y install git nginx gcc gcc-c++ python-devel && yum -y install mysql && yum -y #install mysql-devel && yum install nc -y && yum clean all &&\
#    pip install --upgrade pip


WORKDIR $DOCKER_PROJECT
COPY ./ ./

#Extra python3 requirements
RUN pip3 install -i https://pypi.mirrors.ustc.edu.cn/simple/ -r requirements.txt

EXPOSE 8000
RUN chmod u+x start_script
ENTRYPOINT ["./start_script"]









