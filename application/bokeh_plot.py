from bokeh.models import Button
from bokeh.plotting import figure, curdoc, vplot
from bokeh.embed import components
from bokeh.layouts import gridplot
from bokeh.palettes import Spectral6
from bokeh.models import CustomJS, ColumnDataSource
from bokeh.resources import INLINE

from application.db import Datapoint, Datatype
def create_graph(participant_id):

	html = ""
	datapoints = Datapoint.query.filter((Datapoint.participant_id==participant_id)).order_by(Datapoint.time).limit(100000)
	datatypes = set([d.datatype.name for d in datapoints])
	html += str(datatypes)
	data = {key: [] for key in datatypes}
	for point in datapoints:
		data[point.datatype.name].append(point)



	height=200
	p = figure(x_axis_type="datetime", title="data", responsive=True, height=height/2)
	p.grid.grid_line_alpha=0.3
	p.xaxis.axis_label = 'Date'
	p.yaxis.axis_label = 'Value'

	for i, (key, dataseries) in enumerate(data.iteritems()):
		print dataseries
		p.line(map(lambda d: d.time, dataseries), map(lambda d:d.value, dataseries), color=Spectral6[i%5], legend=key, line_width=2)

	p.legend.location = "top_left"


	# # create a callback that will add a number in a random location
	# def callback():
	#     global i
	#     ds.data['x'].append(np.random.random()*70 + 15)
	#     ds.data['y'].append(np.random.random()*70 + 15)
	#     ds.data['text_color'].append(RdYlBu3[i%3])
	#     ds.data['text'].append(str(i))
	#     ds.trigger('data', ds.data, ds.data)
	#     i = i + 1

	# # add a button widget and configure with the call back
	# button = Button(label="Press Me")
	# button.on_click(callback)

	# put the button and plot in a layout and add to the document

	script, div = components(p)
	print script
	print div
	# cdn = """<link rel="stylesheet" href="https://cdn.pydata.org/bokeh/release/bokeh-0.12.1.min.css" type="text/css" />
	# <script type="text/javascript" src="https://cdn.pydata.org/bokeh/release/bokeh-0.12.1.min.js"></script>"""
	#   http://bokeh.pydata.org/en/latest/docs/reference/resources_embedding.html#bokeh-embed
	cdn = INLINE.render_js() + INLINE.render_css()

	return cdn, script, html+"<div id='bokeh-container' style='width:100%;height:"+str(height)+"px'>"+div+"</div>"