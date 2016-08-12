var http = require('http'),
    httpProxy = require('http-proxy');

// generate secret key
var secret = require('crypto').randomBytes(64).toString('hex');

// launch our special servers
var spawn = require('child_process').spawn;
var flask = spawn('python', ['runserver.py', secret], {shell:true, stdio:'inherit'})
var image = spawn('node', ['server.js', secret], {shell:true, stdio:'inherit'})


// Create a proxy server with custom application logic
var proxy = httpProxy.createProxyServer({});

// Route requests to either node (5001) or flask (5000) ports
var server = http.createServer(function(req, res) {
  console.log(req.url)

  if (req.url.startsWith('/static/') || req.url.startsWith('/images/') || req.url.startsWith('/alive')) {
	  proxy.web(req, res, { target: 'http://localhost:5001' }, function(e) {
	  	// on error
	  	res.writeHead(502, {
	  	    'Content-Type': 'text/plain'
	  	  });
	  	res.end('error in image-server\n'+e);
	   });
  } else {
	  proxy.web(req, res, { target: 'http://localhost:5000' }, function(e) {
	  	// on error
	  	res.writeHead(502, {
	  	    'Content-Type': 'text/plain'
	  	  });
	  	res.end('error in flask-server\n'+e);
   });
  }
});
// listen on http (80) port, and host defined by APP_HOSTNAME
var host = process.env.APP_HOSTNAME || '127.0.0.1';
var port = 80;
server.listen(port, host, function() {
	console.log("load-balancer listening on port "+port+", host " + host);
});