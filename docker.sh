#!/bin/sh
# script for building and running the Dockerfile

# Common commands:

# bash docker.sh run  -> runs app in background

# any commands after run will launch interactive mode
# bash docker.sh run /bin/bash -> runs app into terminal 

# bash docker.sh rebuild      -> will update any changes to app or Dockerfile
# bash docker.sh reboot_db    -> will restart the db service


# container 'tag' to name the build
CONTAINERNAME="image-browser"
# name for our service, to check health use: docker ps -f name=flaskapp
APPNAME="flaskapp"
# name for db service (postgresql container)
DB_NAME="db"

# docker run commands:
# -i  interactive mode
# -t  allocate new tty (terminal)
# --rm clean up on exit
# --name short handle (must be removed with 'docker rm flaskapp' if not --rm)
# -P publish exposed ports on host OS 
# -p hostPort:containerPort = publish only specified ports
# --link db:postgres = link to db with alias inside container: 'postgres'
# the --link commands will set extra environment variables inside the container

if [ "$1" == "run" ]; then
	# echo commands so we know input args
	echo "either Ctrl-Z to exit (or if running using extra args: Ctrl-P then Ctrl-Q)"
	# appending any extra args will launch into debug mode
	docker rm -f ${APPNAME}
	docker run ${2:+ -t -i } -v images_volume:/home/app/application/images --name ${APPNAME} -p 80:80  --link ${DB_NAME}:postgres ${CONTAINERNAME} "${@:2}"
elif [ "$1" == "rebuild" ]; then
	docker build -t ${CONTAINERNAME} .
elif [ "$1" == "reboot_db" ]; then
	docker rm -f ${DB_NAME}
	docker run --name ${DB_NAME} -e POSTGRES_PASSWORD=testing -d postgres
fi

