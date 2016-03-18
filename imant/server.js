var express = require('express');
var app = express();
var crypto = require('crypto');
var querystring =  require('querystring')
var url =  require('url')

if (process.argv.length<2 || process.argv[2].length<10) {
    console.log("NODE_SECRET_KEY is missing or <10 chars")
    process.exit()
}
var secret = process.argv[2]
console.log(secret, "<= NODE_SECRET_KEY")
function verify_hash(t, url, hash) {
    var s = t+url+secret
    // console.log("hash="+crypto.createHash('sha512').update(s).digest('hex'),"\ns="+ s)
    return hash == crypto.createHash('sha512').update(s).digest('hex')
}
// console.log(verify_hash(10,'hello', 'e5fb4297f5cba1b68f4aaa1c99e646dca554e6ba113998f7553338036a01450cf6e3c113ccb2ee93c0afee6ed5fde76aa69c48e105a04524fbb71d02101342a4'))





app.use('/alive', function(req, res) {res.send('alive')})
app.use('/static/', express.static(__dirname + '/static/'));

app.use(function(req, res, next) {
    var url_dict = url.parse(req.url,true)
    var query = url_dict.query;
    var dir = url_dict.pathname;
    var t = parseInt(query.t) 
    // console.log("\n"+req.url, "\nt="+t, "\ndir="+dir+"\nk="+query.k)
    if (isNaN(t)===false && query.k.length>0) {
        if (verify_hash(t, dir, query.k)) {
            return next(); 
        }
    }
    console.log("INVALID HASH t=", t," dir=", dir)
    return res.status(404)        // HTTP status 404: NotFound
	   .send('Not found');
});
app.use('/images/', express.static(__dirname + '/images/'));
// app.use('/m/', express.static(__dirname + '/images/medium'));
// app.use('/f/', express.static(__dirname + '/images/full'));

app.listen(5001, function () {
  console.log('listening on 5001..');
});

function time() {
	var d = new Date();
	return d.getTime(); // milliseconds since epoch
}