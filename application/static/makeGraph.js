var makeGraph = function() {console.log("makeGraph not loaded yet")};
var loadGraphDatatypes = function() {console.log("makeGraphParticipant not loaded yet")};

(function makeGraphClosure() {
	var datatypes = {}
	var datatypes_loaded = false;
	var created_graph = false;
	// graph variables:
	var x,y, xAxis, yAxis, line, width, height;
	makeGraph = function (selector, participant_id, datatype_id, width, height) {


		Promise.all([
			load_datatypes(participant_id),
			setup_graph(selector, width, height)
			]).then(
				() => {
					console.log("loaded and setup_graph", datatypes)
					var datatype_id = null;
					for (var key in datatypes) {
						console.log(key, datatypes[key])
						if (datatypes[key]=='acceleration') {
							datatype_id = key;
							break
						}
					}
					if (datatype_id!=null) {
						console.log("datatype_id",  datatype_id)
						return load_datapoints(participant_id, datatype_id)
							
					}
				}
			).then((data) => {
				console.log("now rendering:", data);
				drawGraph(data)
			})
			// .catch((e) => {console.log("error in graphing:", e)})


	}
	function setup_graph(selector) {
		return new Promise((resolve) => {
			
			console.log("setting up graph")
			if (!width) width = $(window).width()-200;
			if (!height) height = 200;

			// Set the dimensions of the canvas / graph
			var margin = {top: 30, right: 20, bottom: 30, left: 50};
			width = width - margin.left - margin.right,
			height = height - margin.top - margin.bottom;

			// Set the range
			x = d3.time.scale()
			    .range([0, width])//.nice(d3.time.minute)

			y = d3.scale.linear()
			    .range([height, 0]);


			xAxis = d3.svg.axis()
			    .scale(x)
			    .orient("bottom");

			yAxis = d3.svg.axis()
			    .scale(y)
			    .orient("left");

			line = d3.svg.line()
			    .x(function(d) { return x(d.time); })
			    .y(function(d) { return y(d.value); });

			var svg = d3.select(".graph").append("svg")
			    .attr("width", width + margin.left + margin.right)
			    .attr("height", height + margin.top + margin.bottom)
			   .append("g")
			    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

			created_graph = true;
			resolve("created_graph");
		})
	}

	function drawGraph(data) {
		svg = d3.select(".graph").select("g")

	    x.domain(d3.extent(data, function(d) { return d.time; }));
	    y.domain(d3.extent(data, function(d) { return d.value; }));

		svg.append("g")
		  .attr("class", "x axis")
		  .attr("transform", "translate(0," + height + ")")
		  .call(xAxis);

		svg.append("g")
		  .attr("class", "y axis")
		  .call(yAxis)
		.append("text")
		  .attr("transform", "rotate(-90)")
		  .attr("y", 6)
		  .attr("dy", ".71em")

		svg.append("path")
		  .datum(data)
		  .attr("class", "path")
		  .attr("d", line);
	}

	function load_datapoints(participant_id, datatype_id) { 
		console.log("load_datapoints(",participant_id, datatype_id,")")
		return Datapoints.get_datapoints(participant_id, datatype_id).then(function(response) {
			console.log("Datapoints.get_datapoints", response)
			// parse the data
			var formatDate = d3.time.format("%Y-%m-%dT%H:%M:%S");
			function type(d) {
			  d.time = formatDate.parse(d[1]);
			  d.value = +d[0];
			  // console.log(d.time, d.value)
			  return {time: d.time, value: d.value};
			}

			var data = response.data.map(type)
			// t = 0
			// data = Array.apply(null, Array(100)).map(function(){
			// 	t++
			// 	return {time: new Date(t*100), value: t *100}
			// })
			console.log("data:",data)
			return data
		});
	}


	load_datatypes = function(participant_id) {
		if (datatypes_loaded) return;
		else {
			console.log("loading datatype");
			return Datapoints.get_datatypes(participant_id).then(function(data) {
						console.log("Datapoints.get_datatypes(participant_id)", data)
						datatypes_loaded = true;
						datatypes = data
						return;
					})
		}
	}

})();
