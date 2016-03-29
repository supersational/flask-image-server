
var _request_pending = false;
function create_query(url, data, callback) {
	if (_request_pending==true) return console.log("already waiting for a request to complete");
	_request_pending = true;
	$.ajax({
		type: "POST",
		url: url,
		data: data,
		complete : function(jqXHR, textStatus) {
			_request_pending = false;
		  	console.log("db.js request completed: "+url+", status:"+textStatus);
		  	if (jqXHR) console.log(jqXHR)
			if (callback && textStatus!=="error") callback(textStatus) // if error don't reload page so we can see the response object
		} 
	});
}
var Event = {
	// participant_id not really necessary here, but can't hurt
	check_valid: function(participant_id, event_id, complete) {
		create_query("/participant/"+participant_id+"/"+event_id+"/check_valid",undefined, complete)
	},
	add_image: function(participant_id, event_id, image_id, complete) {
		create_query("/participant/"+participant_id+"/"+event_id+"/"+image_id+"/add_image",undefined, complete)
	},
	remove_image: function(participant_id, event_id, image_id, direction, include_target, complete) {
		create_query(
			"/participant/"+participant_id+"/"+event_id+"/"+image_id+"/remove",
			{direction:direction, include_target:include_target}, complete)
	},
	split: function(dir, participant_id, event_id, image_id, complete) {
		if (dir=="left" || dir=="right") 
			create_query("/participant/"+participant_id+"/"+event_id+"/"+image_id+"/split_"+dir,undefined, complete)
	},
	annotate: function(participant_id, event_id, label_id, complete) {
		create_query("/participant/"+participant_id+"/"+event_id+"/annotate",{label_id:label_id}, complete)
	}
}
var Study = {
	remove_participant: function(participant_id, study_id, complete) {
		create_query("/remove_studyparticipant",{participant_id: participant_id, study_id:study_id}, complete)
	},
	remove_user: function(user_id, study_id, complete) {
		create_query("/user/"+user_id+"/modify_studies",{study_id:study_id, method: "remove"}, complete)
	}
}
var User = {
	change_password: function(user_id, old_password, new_password, complete) {
		create_query("/user/"+user_id+"/change_password",{original_password: original_password, new_password:new_password}, complete)
	}
}
var Image = {
	load_json: function(participant_id, start, end, num, complete) {
		create_query("/participant/"+participant_id+"/load_images", {start_id:start, end_id:end, number:num}, complete)
	}
}