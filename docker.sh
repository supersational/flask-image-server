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
	VOLUME="-v //d/images://home/app/application/images/"
	LIVE_RELOADING="true"
	if [ "$LIVE_RELOADING" == "true" ]; then
		# this line mounts the application volume for live code changes
		VOLUME="-v /$(pwd)/application://home/app/application $VOLUME"
		# this line additionally mounts all python scripts in the root directory
		for f in ./*.py
		do
			echo $(pwd)/$f
			VOLUME="-v /$(pwd)/$f://home/app/$f $VOLUME"
		done
	fi
	# enable standard http port
	PORT="-p 80:80"

	
	echo docker run -d ${VOLUME} --name ${APPNAME} ${PORT} --link ${DB_NAME}:postgres ${CONTAINERNAME} 
	docker run -d ${VOLUME} --name ${APPNAME} ${PORT} --link ${DB_NAME}:postgres ${CONTAINERNAME} 
	
elif [ "$1" == "rebuild" ]; then
	docker build -t ${CONTAINERNAME} .
elif [ "$1" == "reboot_db" ]; then
	docker rm -f ${DB_NAME}
	docker run --name ${DB_NAME} -e POSTGRES_PASSWORD=testing -d postgres
elif [ "$1" == "bash" ]; then
	docker exec -it flaskapp bash
elif [ "$1" == "cmd" ]; then
	docker exec -it flaskapp "${@:2}"
fi

