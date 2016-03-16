var express = require('express');
var app = express();
var crypto = require('crypto');
var querystring =  require('querystring')
var url =  require('url')

var secret = 'secret_key'
function verify_hash(t, url, hash) {
    var s = t+url+secret
    console.log("hash="+crypto.createHash('sha512').update(s).digest('hex'),"\ns="+ s)
    return hash == crypto.createHash('sha512').update(s).digest('hex')
}
// console.log(verify_hash(10,'hello', 'e5fb4297f5cba1b68f4aaa1c99e646dca554e6ba113998f7553338036a01450cf6e3c113ccb2ee93c0afee6ed5fde76aa69c48e105a04524fbb71d02101342a4'))


// process.exit()




app.use('/static/', express.static(__dirname + '/static/'));

app.use(function(req, res, next) {
    var url_dict = url.parse(req.url,true)
    var query = url_dict.query;
    var dir = url_dict.pathname;
    var t = parseInt(query.t) 
    console.log("\n"+req.url, "\nt="+t, "\ndir="+dir+"\nk="+query.k)
    if (isNaN(t)===false && query.k.length>0) {
        if (verify_hash(t, dir, query.k)) {
            console.log("VALID")
            return next(); 
        }
    }
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