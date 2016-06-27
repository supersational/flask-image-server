var makeGraph = function(selector, width, height) {

	$("<style type='text/css'>"
	+"	.axis path,"
	+"	.axis line {"
	+"	  fill: none;"
	+"	  stroke: #000;"
	+"	  shape-rendering: crispEdges;"
	+"	}"
	+""
	+"	.x.axis path {"
	+"	  display: none;"
	+"	}"
	+""
	+"	.path {"
	+"	  fill: none;"
	+"	  stroke: steelblue;"
	+"	  stroke-width: 1.5px;"
	+"	}"
	+"	</style>").appendTo("head");

	if (!width) width = $(window).width()-200;
	if (!height) height = 200;
	console.log(width, height, $(".gallery").width())
	// Set the dimensions of the canvas / graph
	var margin = {top: 30, right: 20, bottom: 30, left: 50};
	width = width - margin.left - margin.right,
	height = height - margin.top - margin.bottom;

	// Set the ranges
	var x = d3.time.scale().range([0, width]);
	var y = d3.scale.linear().range([height, 0]);

	// Define the axes
	var xAxis = d3.svg.axis().scale(x)
	    .orient("bottom").ticks(5);

	var yAxis = d3.svg.axis().scale(y)
	    .orient("left").ticks(5);

	// Define the line

	var line = d3.svg.line()
	    .x(function(d) { return x(d.time); })
	    .y(function(d) { return y(d.value); });

	   
	var svg = d3.select(selector).append("svg")
	    .attr("width", width + margin.left + margin.right)
	    .attr("height", height + margin.top + margin.bottom)
	  .append("g")
	    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");


	var formatDate = d3.time.format("%Y-%m-%dT%H:%M:%S");
	function type(d) {
	  d.time = formatDate.parse(d[1]);
	  d.value = +d[0];
	  return {time: d.time, value: d.value};
	}

	function drawChart(data) {
		// console.log("data:",data)
		data = data.map(type)
		console.log("data:",data)
		x.domain(d3.extent(data, function(d) { return d.time; }));
		y.domain(d3.extent(data, function(d) { return d.value; }));
		console.log("svg", svg[0][0])

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
		  .style("text-anchor", "end")
		  .text("Price ($)");

		svg.append("path")
		  .datum(data)
		  .attr("class", "path")
		  .attr("d", line);
		console.log("x", x)
		console.log("y", y)
		console.log("svg", svg)
		console.log("svg", svg[0][0].children)
	}


	participant_id = 11
	Datapoints.get_datatypes(participant_id, function(datatype_dict) {
		console.log(datatype_dict)
		for (var firstKey in datatype_dict) if(datatype_dict[firstKey]=='mean') break;
		console.log(firstKey)
		console.log(datatype_dict[firstKey])


		Datapoints.get_datapoints(participant_id, firstKey, function(data) {
			// console.log(data)
			drawChart(data.data)

		})
	});

}
$(document).ready(function() {makeGraph(".graph")})