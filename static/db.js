
var _request_pending = false;
var Event = {
	// participant_id not really necessary here, but can't hurt
	check_valid: function(participant_id, event_id, complete) {
		_request_pending = true;
		$.ajax({
			type: "POST",
			url: "/participant/"+participant_id+"/"+event_id+"/check_valid",
			complete : function(jqXHR, textStatus) {
				_request_pending = false;
			  	console.log("Event.check_valid("+participant_id+","+event_id+") "+textStatus);
			  	console.log(jqXHR)
				if (complete) complete(textStatus)
			} 
		});
	},
	add_image: function(participant_id, event_id, image_id, complete) {
		_request_pending = true;
		$.ajax({
			type: "POST",
			url: "/participant/"+participant_id+"/"+event_id+"/"+image_id+"/add_image",
			complete : function(jqXHR, textStatus) {
				_request_pending = false;
				console.log("Event.add_image("+participant_id+","+event_id+") " + textStatus);
				console.log(jqXHR)
				if (complete) complete(textStatus)
			} 
		});
	},
	remove_image: function(participant_id, event_id, image_id, direction, include_target, complete) {
		_request_pending = true;
		$.ajax({
			type: "POST",
			url: "/participant/"+participant_id+"/"+event_id+"/"+image_id+"/remove",
			data: {direction:direction, include_target:include_target},
			complete : function(jqXHR, textStatus) {
				_request_pending = false;
				console.log("Event.remove_image("+participant_id+","+event_id+", " + direction + ", "+include_target+")" + textStatus);
				console.log(jqXHR)
				if (complete) complete(textStatus)
			} 
		});
	},
	split: function(dir, participant_id, event_id, image_id, complete) {
		_request_pending = true;
		if (dir=="left" || dir=="right") 
			$.ajax({
				type: "POST",
				url: "/participant/"+participant_id+"/"+event_id+"/"+image_id+"/split_"+dir,
				complete : function(jqXHR, textStatus) {
					_request_pending = false;
					console.log("Event.split_left("+participant_id+","+event_id+") " + textStatus);
					console.log(jqXHR)
					if (complete) complete(textStatus)
				} 
			});
	},
	annotate: function(participant_id, event_id, label_id, complete) {
		_request_pending = true;
		$.ajax({
			type: "POST",
			data: {label_id:label_id},
			url: "/participant/"+participant_id+"/"+event_id+"/annotate",
			complete : function(jqXHR, textStatus) {
				_request_pending = false;
				console.log("Event.annotate("+participant_id+","+event_id+","+label_id+") " + textStatus);
				console.log(jqXHR)
				if (complete) complete(textStatus)
			} 
		});
	}
}
var Study = {
	remove_participant: function(participant_id, study_id, complete) {
		_request_pending = true;
		$.ajax({
			type: "POST",
			url: "/remove_studyparticipant",
			data: {participant_id: participant_id, study_id:study_id},
			complete : function(jqXHR, textStatus) {
				_request_pending = false;
				console.log("/remove_studyparticipant("+participant_id+","+study_id+") " + textStatus);
				console.log(jqXHR)
				if (complete) complete(textStatus)
			} 
		});
	}
}
