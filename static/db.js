var Event = {
	// participant_id not really necessary here, but can't hurt
	check_valid: function(participant_id, event_id, complete) {
		$.ajax({
			type: "POST",
			url: "/participant/"+participant_id+"/"+event_id+"/check_valid",
			complete : function(jqXHR, textStatus) {
			  	console.log("Event.check_valid("+participant_id+","+event_id+") "+textStatus);
			  	console.log(jqXHR)
				if (complete) complete(textStatus)
			} 
		});
	},
	add_image: function(participant_id, event_id, image_id, complete) {
		$.ajax({
			type: "POST",
			url: "/participant/"+participant_id+"/"+event_id+"/add_image/"+image_id,
			complete : function(jqXHR, textStatus) {
				console.log("Event.add_image("+participant_id+","+event_id+") " + textStatus);
				console.log(jqXHR)
				if (complete) complete(textStatus)
			} 
		});
	}
}