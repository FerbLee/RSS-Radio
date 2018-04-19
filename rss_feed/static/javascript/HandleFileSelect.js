function handleFileSelect(evt) {
    var files = evt.target.files;
    var f = files[0];
    var reader = new FileReader();
	
      reader.onload = (function(theFile) {
        return function(e) {
          document.getElementById(eid).innerHTML = ['<p>New Image:</p>','<img src="', e.target.result,'" title="', theFile.name, '" width="200"/>'].join('');
        };
      })(f);

      reader.readAsDataURL(f);
  }