var http = require('http'),
    httpProxy = require('http-proxy');

// Create a proxy server with custom application logic
var proxy = httpProxy.createProxyServer({});

// Route requests to either node (5001) or flask (5000) ports
var server = http.createServer(function(req, res) {
  // console.log(req.url)
  if (req.url.startsWith('/static/') || req.url.startsWith('/images/') || req.url.startsWith('/alive')) {
	  proxy.web(req, res, { target: 'http://127.0.0.1:5001' });
  } else {
	  proxy.web(req, res, { target: 'http://127.0.0.1:5000' });
  }
});
// listen on http (80) port, and host defined by APP_HOSTNAME
var host = process.env.APP_HOSTNAME || '127.0.0.1';
var port = 80;
console.log("listening on port "+port+", host " + host);
server.listen(port, host);