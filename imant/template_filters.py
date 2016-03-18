from imant import app
# Add Jinja2 filters
@app.template_filter('time')
def get_time(s):
	if type(s) == str:
	    return s[11:20]
	elif s is None:
		return ""
	else:
		return s.strftime("%H:%M:%S")

@app.template_filter('verbose_date')
def verbose_date(date):
	return date.strftime("%A %d %B %Y %H:%M")

@app.template_filter('verbose_seconds')
def verbose_seconds(seconds):
	days, rem = divmod(seconds, 86400)
	hours, rem = divmod(rem, 3600)
	minutes, seconds = divmod(rem, 60)
	if minutes + hours + days <= 0 and seconds < 1: seconds = 1
	locals_ = locals()
	magnitudes_str = ("{n} {magnitude}".format(n=int(locals_[magnitude]), magnitude=magnitude[0:-1] if int(locals_[magnitude]==1) else magnitude)
			            for magnitude in ("days", "hours", "minutes", "seconds") if locals_[magnitude])
	return ", ".join(magnitudes_str)