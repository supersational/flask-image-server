var express = require('express');
var app = express();
var crypto = require('crypto');
var querystring =  require('querystring')
var url =  require('url')

console.log(crypto.createHmac('sha512', 'sven').digest('hex'))
var q = url.parse("http://127.0.0.1:5001/t/5.jpg?t=1458063101&k=db3c8279029cd3bce9fc5d3252b2e47305c5fa5a168651c6bba38b0b394a65d2da86d3d823c8bc27a47a0c7ea4bf7b8e7d047a9879f93a4262eafb1af73b2c52",true).query
console.log(q)
var secret = 'secret_key'
app.use('/static/', express.static(__dirname + '/static/'));

if (false) app.use(function(req, res, next) {
	var query = url.parse(req.url,true).query;
    var t = parseInt(query.t) 
    var s = secret+t
    console.log("\n"+req.url, "\n"+t, "\n"+query.ans+"\n"+s)
    if (isNaN(t)===false && query.k) {
    	var hash = crypto.createHmac('sha512', secret)
    	hash.update(t+'')
    	var value = hash.digest('hex')
    	var hash2 = crypto.createHmac('sha512', query.ans)
    	var ans_value = hash2.digest('hex')
    	console.log("k: "+query.k +"\nv: "+value+"\na: "+ans_value)
    	if (value===query.k) {
    		console.log("VALID")
		}
    }
    return next(); 
	res.status(404)        // HTTP status 404: NotFound
	   .send('Not found');
});
app.use('/t/', express.static(__dirname + '/images/thumbnail'));
app.use('/m/', express.static(__dirname + '/images/medium'));
app.use('/f/', express.static(__dirname + '/images/full'));

app.listen(5001, function () {
  console.log('listening on 5001..');
});

function time() {
	var d = new Date();
	return d.getTime(); // milliseconds since epoch
}