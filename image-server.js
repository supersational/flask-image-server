var express = require('express');
var app = express();
var crypto = require('crypto');
var url =  require('url')

if (process.argv.length<3 || (process.argv.length>=3 && process.argv[2].length<10)) {
    console.log("NODE_SECRET_KEY is missing or <10 chars")
    process.exit()
}
var secret = process.argv[2]

console.log(secret, "<= NODE_SECRET_KEY len = ", secret.length)
function verify_hash(t, url, hash) {
    var s = t+url+secret
    // console.log("hash="+crypto.createHash('sha512').update(s).digest('hex'),"\ns="+ s)
    return hash == crypto.createHash('sha512').update(s).digest('hex')
}
// console.log(verify_hash(10,'hello', 'e5fb4297f5cba1b68f4aaa1c99e646dca554e6ba113998f7553338036a01450cf6e3c113ccb2ee93c0afee6ed5fde76aa69c48e105a04524fbb71d02101342a4'))


// set cache times
var cache_expiry_static = 30*24*60*60*1000; // 1 month
var cache_expiry_images = 24*60*60*1000; // 1 day


app.use(function(req, res, next) {
    console.log("GOT REQUEST ", req.url);
    next(); // Passing the request to the next handler in the stack.
});
app.use('/alive', function(req, res) {res.send('alive')})
app.use('/static/', express.static(__dirname + '/application/static/', {maxAge:cache_expiry_static}));

app.use(function(req, res, next) {
    var url_dict = url.parse(req.url,true)
    var query = url_dict.query;
    var dir = url_dict.pathname;
    var t = parseInt(query.t) 
    console.log("\n"+req.url, "\nt="+t, "\ndir="+dir+"\nk="+query.k)
    if (isNaN(t)===false && query.k.length>0) {
        if (verify_hash(t, dir, query.k)) {
            return next(); 
        }
    }
    console.log("INVALID HASH t=", t," dir=", dir)
    return res.status(404)        // HTTP status 404: NotFound
	   .send('Not found');
});
app.use('/images/', express.static(__dirname + '/application/images/', {maxAge:cache_expiry_images}));

var host = '127.0.0.1';
app.listen(5001, host, function () {
  console.log('image server listening on 5001.. host=', host);
});

function time() {
	var d = new Date();
	return d.getTime(); // milliseconds since epoch
}