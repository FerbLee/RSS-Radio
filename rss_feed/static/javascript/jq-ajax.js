$(document).ready(function(){
	$('#download').click(function(){
	    var epid;
	    epid = $(this).attr("data-epid");
	    $.get('/rss_feed/download/', {episode_id: epid}, function(data){
	               $('#download_count').html(data);
	    });
	});
});


$(document).ready(function(){
	$('#player').on('play',function(){
		var epid;
	    epid = $(this).attr("data-epid");
	    $.get('/rss_feed/download/', {episode_id: epid}, function(data){
	               $('#download_count').html(data);
	    });
	});
});



$(document).ready(function(){
    $("#message").click(function(){
        alert("AAAAAAA");
    });
});