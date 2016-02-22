var Event = {
	// participant_id not really necessary here, but can't hurt
	check_valid: function(event_id, participant_id, success) {
		$.ajax({
		  type: "POST",
		  url: "/participant/"+participant_id+"/"+event_id+"/check_valid",
		  success: function() {console.log("Event.check_valid("+participant_id+","+event_id+") success"); if (success) success()} 
		});
	},
	add_image: function(event_id, participant_id, image_id, success) {
		$.ajax({
		  type: "POST",
		  url: "/participant/"+participant_id+"/"+event_id+"/add_image",
		  success: function() {console.log("Event.add_image("+participant_id+","+event_id+") success"); if (success) success()} 
		});
	}
}