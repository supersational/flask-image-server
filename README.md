# Flask-image-server

A webserver you can use to annotate wearable camera images.

### Requirements
#### Node.js (4.4.0)
install modules in package.json using `npm install` (in root directory)

#### Python
`pip install -r requirements.txt`
PIL (Python Imaging Library) has additional dependencies (see Dockerfile for Ubuntu instructions)

### Running the server
`node load-balancer.js`
will start the server on localhost (port 80) or whatever the `APP_HOSTNAME` env variable is set to (0.0.0.0 for production)

### Deploying production server
You can auto-deploy using git-push, (using the private key file)

Add the production git repo:
`git remote add production ssh://sven@40.76.222.25/home/sven/MLdocker/app_auto`

To use a ssh private-key file with Git use ssh-agent:
```
eval $(ssh-agent)
ssh-add /path/to/your/private_openssh_key
(type in password)
```
You will now automatically authenticate using the provided file.

Make your changes and push (to production):
```
git add .
git commit -m "made some changes"
git push production master
```
Output should be something like:
```
Counting objects: 9, done.
Delta compression using up to 4 threads.
Compressing objects: 100% (9/9), done.
Writing objects: 100% (9/9), 906 bytes | 0 bytes/s, done.
Total 9 (delta 6), reused 0 (delta 0)
remote: auto-updating app.. Wed Aug 17 16:27:21 UTC 2016
remote: HEAD is now at 73e8c0e config.py
remote: auto-updating complete! Wed Aug 17 16:27:21 UTC 2016
To ssh://sven@40.76.222.25/home/sven/MLdocker/app_auto
   d26d02f..73e8c0e  master -> master
```
Meaning the server should now be live on http://40.76.222.25/ !

