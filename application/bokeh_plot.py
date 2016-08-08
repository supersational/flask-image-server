from bokeh.plotting import figure, curdoc, vplot
from bokeh.embed import components
from bokeh.layouts import gridplot
from bokeh.palettes import Spectral6
from bokeh.models import CustomJS, ColumnDataSource, Range1d
from bokeh.models import Button, Slider
from bokeh.resources import INLINE
from bokeh.layouts import column

# querying the db and func for downsampling
from application.db import Datapoint, Datatype, session
from sqlalchemy.sql import func
from sqlalchemy import extract  
from itertools import groupby

def create_graph(participant_id, height=400):

	html = ""
	elements = []
	# datapoints = Datapoint.query.filter((Datapoint.participant_id==participant_id)).order_by(Datapoint.time).limit(1000)
	# datapoints = session.query(func.avg(Datapoint.value).label('value')).filter((Datapoint.participant_id==participant_id)).limit(1000)
	datapoints = Datapoint.query.with_entities( \
			Datapoint.datatype_id, \
			func.min(Datapoint.time).label('time'), \
			func.avg(Datapoint.value).label('value'), \
			extract('second', Datapoint.time).label('t') \
		).filter( \
			Datapoint.participant_id==participant_id \
		).group_by( \
			't', Datapoint.datatype_id \
		).order_by( Datapoint.datatype_id, 'time').all()
	# datatypes = set([d.datatype.name for d in datapoints]).datatype_id)
	# html += str(datatypes)
	# data = {key: [] for key in datatypes}
	# x_max = -float("inf")
	# x_min = float("inf")
	# html += str(datapoints)
	data = {}
	# html += "<br>"
	for datatype_id, dataseries in groupby(datapoints, lambda x: x[0]):
		data[datatype_id] = list(dataseries)

	names = {x.datatype_id: x.name for x in  session.query(Datatype).filter(Datatype.datatype_id.in_(data.keys())).all()}
	html += str(names)

		# html += "<h1>"+str(k)+"</h1>"+str(data[k][1])
		# html += "<br>"
		# html += str(map(lambda d: d[1], data[k]))
		# html += "<br>"
		# html += str(map(lambda d: d[2], data[k]))
		# x_max = max(point.value, x_max)
		# x_min = min(point.value, x_min)
	# html += "<br>"
	# html += str(data)

	# return "", "", str(html)

	p = figure(
		x_axis_type="datetime", title="Participant "+str(participant_id)+" data", responsive=True, height=height, 
		tools="pan,wheel_zoom,box_zoom,reset,resize,box_select", toolbar_location="above",
		)
	p.grid.grid_line_alpha=0.3
	p.xaxis.axis_label = 'Date'
	p.yaxis.axis_label = 'Value'

	datasources = []
	for i, (key, dataseries) in enumerate(data.iteritems()):
		# html += "<h1>"+str(key)+"</h1>" 
		# html += "<p>"+str(len(dataseries))+"</p>"
		# html += "<br>"
		# html += str(map(lambda d: d[1],dataseries))
		# html += "<br>"
		# html += str(map(lambda d: d[2],dataseries))
		# return "", "", str(html)
		name = str(names[key])
		x = map(lambda d: d[1], dataseries)
		y = map(lambda d:d[2], dataseries)
		datasource = ColumnDataSource(data=dict(x=x, y=y))
		datasources.append(datasource)
		p.line('x','y',source=datasource, legend=name, line_width=2, color=Spectral6[i%5])
		p.circle('x','y',source=datasource,  fill_color="white",  color=Spectral6[i%5], size=4)

	p.legend.location = "top_left"
	elements.append(p)
	# select data
	for ds in datasources:
		ds.callback = CustomJS(code="""
			console.log('selected')
			console.log(cb_obj.get('selected'))
			console.log(cb_obj.get('selected')['1d'].indices)
			""")
	
	callback = CustomJS(args=dict(figure=p), code="""
			console.log(cb_obj.get('selected'))
			console.log(line)
			fig = figure;
			lin = line;
			cb = cb_obj
	        var data = figure.get('data');
	        var f = cb_obj.get('value')
	        x = data['x']
	        y = data['y']
	        for (i = 0; i < x.length; i++) {
	            y[i] = Math.pow(x[i], f)
	        }
	        figure.trigger('change');
	    """)

	# # add a button widget and configure with the call back
	button = Button(label="Press Me", width=50, height=30)
	slider = Slider(start=0, end=4, value=1, step=1, title="Resolution", callback=callback)
	# elements.append(slider)

	# button.on_click(callback)

	# put the button and plot in a layout and add to the document
	container = column(children=elements, height=200)
	# html += str(dir(container))
	script, div = components(container)
	# html += str(container._id)
	# html += str(container.width)
	# html += "<style>#modelid_"+str(p._id)+" {width: 100% !important;}"
	# html += "#modelid_"+str(container._id)+" {width: 100% !important;}</style>"


	# cdn = """<link rel="stylesheet" href="https://cdn.pydata.org/bokeh/release/bokeh-0.12.1.min.css" type="text/css" />
	# <script type="text/javascript" src="https://cdn.pydata.org/bokeh/release/bokeh-0.12.1.min.js"></script>"""
	#   http://bokeh.pydata.org/en/latest/docs/reference/resources_embedding.html#bokeh-embed
	cdn = INLINE.render_js() + INLINE.render_css()

	return cdn, "<script>var fig, lin, cb;</script>"+script, html+"<div id='bokeh-container' style='width:100%;height:"+str(height)+"px'>"+div+"</div>"