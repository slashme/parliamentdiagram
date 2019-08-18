$(document).ready(function() {
	$('#party1').hide();
	  $.ajax({
	    dataType: "json",
	    url: "https://query.wikidata.org/sparql?query=SELECT%20DISTINCT%20%3Fstate%20%3FstateLabel%20%3Fid%20WHERE%20%7B%0A%20%20%3Fstate%20wdt%3AP31%2Fwdt%3AP279%2a%20wd%3AQ3624078%3B%0A%20%20%20%20%20%20%20%20%20p%3AP463%20%3FmemberOfStatement.%0A%20%20%3FmemberOfStatement%20a%20wikibase%3ABestRank%3B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20ps%3AP463%20wd%3AQ1065.%0A%20%20MINUS%20%7B%20%3FmemberOfStatement%20pq%3AP582%20%3FendTime.%20%7D%0A%20%20MINUS%20%7B%20%3Fstate%20wdt%3AP576%7Cwdt%3AP582%20%3Fend.%20%7D%0A%20%20BIND%28STRAFTER%28STR%28%3Fstate%29%2C%20STR%28wd%3A%29%29%20AS%20%3Fid%29%0A%20%20SERVICE%20wikibase%3Alabel%20%7B%20bd%3AserviceParam%20wikibase%3Alanguage%20%22en%22.%20%7D%0A%7D%20ORDER%20BY%20%3FstateLabel&format=json",
})
	.done(function(data){$.each(data.results.bindings, function(key, value){
		$('#countrylist').append($("<option></option>").attr("value",value.id.value).text(value.stateLabel.value));
	});});
	$('#countrylist').select2();

$('#wdpartylist').click(function(){
		var country_WD_item = $('#countrylist').val();
	  $.ajax({
	    dataType: "json",
	    url: "https://query.wikidata.org/sparql?query=SELECT%20%3FwdPlain%20%3Flabel_en%20%3Fshort%20%3Fdisplay%0AWHERE%0A%7B%0A%20%20%3Fparty%20wdt%3AP31%2Fwdt%3AP279*%20wd%3AQ7278.%20%3Fparty%20wdt%3AP17%20wd%3A"+country_WD_item+".%20%0A%20%20OPTIONAL%20%7B%20%3Fparty%20wdt%3AP1813%20%3Fshort.%20%7D%0A%20%20%3Fparty%20rdfs%3Alabel%20%3Flabel_en%20filter%20(lang(%3Flabel_en)%20%3D%20%22en%22).%0A%20%20BIND(REPLACE(STR(%3Fparty)%2C%22http%3A%2F%2Fwww.wikidata.org%2Fentity%2F%22%2C%22%22)%20AS%20%3FwdPlain)%0A%20%20BIND(COALESCE(%3Fshort%2C%20%3Flabel_en)%20AS%20%3Fdisplay)%0A%7D%20ORDER%20BY%20%3Flabel_en&format=json",
})
		.done(function(data){
			$('#partylist')
				.find('option')
				.remove()
				.end();
			$.each(data.results.bindings, function(key, value){
			$('#partylist').append($("<option></option>").attr("value",value.wdPlain.value).text(value.label_en.value))
	});
			$('#partylist').select2();
		});

});

$('#addpartybutton').click(function(){
	var newname=$('#partylist').text();
	var newcolor="";
        // Party list <div> where dynamic content will be placed
        var partylistcontainer = document.getElementById("partylistcontainer");
        //New party's number: one more than the largest party number so far:
        i=0;
        $( "div" ).each( function() { 
            if(this.id.match( /^party[0-9]+$/ )){
                i=Math.max(i, parseInt(/[0-9]+$/.exec(this.id)[0] ));
              }
          }
        )
        i++;
        var newpartydiv=document.createElement('div');
        newpartydiv.id="party" + i;
        partylistcontainer.appendChild(newpartydiv);
        //Party name label
        var partytitle=document.createElement('div');
        partytitle.className = 'left';
	if(newname==""){newname="Party " + i }
        partytitle.innerHTML = "Party " +  i ;
        newpartydiv.appendChild(partytitle);
        //Party name input control
        var input=document.createElement('div');
        input.innerHTML = '<input class="right" type="text" name="Name' +  i + '"   value="' + newname + '">'
        newpartydiv.appendChild(input);
        //Party support name tag
        var partysupport=document.createElement('div');
        partysupport.className = 'left';
        partysupport.innerHTML = "Party " + i + " delegates";
        newpartydiv.appendChild(partysupport);
        //Party support input control
        var input=document.createElement('div');
        input.innerHTML = '<input class="right" type="number" name="Number' +  i + '"   value= "0" >';
        newpartydiv.appendChild(input);
        //Party color name tag
        var partycolor=document.createElement('div');
        partycolor.className = 'left';
        partycolor.innerHTML = "Party " + i + " color";
        newpartydiv.appendChild(partycolor);
        //Party color input control
        var input=document.createElement('div');
	if(newcolor==""){newcolor=getRandomColor()}
        input.innerHTML = '<input class="right color" type="text" name="Color' +  i + '" value= "' +  newcolor + '" >'
        newpartydiv.appendChild(input);
        //Party border checkbox name tag
        var partycolor=document.createElement('div');
        partycolor.className = 'left';
        partycolor.innerHTML = "Party " + i + " border";
        newpartydiv.appendChild(partycolor);
        //Party border checkbox control
        var input=document.createElement('div');
        input.innerHTML = '<input class="right" type="checkbox" name="Border' +  i + '" >'
        newpartydiv.appendChild(input);
        //Party border color name tag
        var partybcolor=document.createElement('div');
        partybcolor.className = 'left';
        partybcolor.innerHTML = "Party " + i + " border color";
        newpartydiv.appendChild(partybcolor);
        //Party border color input control
        var input=document.createElement('div');
        input.innerHTML = '<input class="right color" type="text" name="BColor' +  i + '" value= "' +  "000000" + '" >'
        newpartydiv.appendChild(input);
        var delbutton=document.createElement('div');
        delbutton.className = 'button deletebutton';
        delbutton.innerHTML = "Delete party " + i;
        delbutton.setAttribute("onClick", "deleteParty(" + i + ")");
        newpartydiv.appendChild(delbutton);
          //Add a newline
        newpartydiv.appendChild(document.createElement("br"));
        //$( "input[name=Color" + i + "]").addClass('color'); /* no longer needed because I'm writing the innerHTML
        //jscolor.init();
});


	$('#getfile').click(function(){
	  var wikiurl = "https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=revisions&titles="+$("#inputfile").val()+"&rvprop=content&rvlimit=1&callback=?";
	  $.ajax({
	    dataType: "json",
	    url: wikiurl,
	  })
		  .done(function(data){
			  $.each(data.query.pages, function(i,item){
				  wikitext=item.revisions[0]['*'];
			  });
	var res = wikitext.split("{{legend");
	len=res.length;
	if(len<2){alert("legend template not detected, cannot auto-fill party list.")};
	
	regex2=": ";
	regex3=" seats}}";
	//create array to hold party data
	partydata=[];
 
	for(i=1; i<len; i++)
	    {
		partydata[i-1]=[];
		partydata[i-1][0]=res[i].slice(2,8);
		seatnum = res[i].search(regex2);
		if(seatnum == -1){alert("Can't find number of seats, this is probably an old diagram.")};
		partydata[i-1][1]=res[i].slice(9,seatnum);
//		seatsend = res[i].search(regex3);
//		partydata[i-1][2]=res[i].slice(seatnum+2,seatsend);
	    }
	// Delete all parties first
        // Select party list <div>
        var partylistcontainer = document.getElementById("partylistcontainer");
        //Find out how many parties we have
        numparties=0;
        $( "div" ).each( function() { 
            if(this.id.match( /^party[0-9]+$/ )){
		    deleteParty( parseInt(/[0-9]+$/.exec(this.id)[0] ));
              }
          }
        );

	//Generate parties from array: 
	partydata.forEach(function(element){
		addParty(element[1], element[0])
	});

	  });
	});
});

//Generate random color, based on http://stackoverflow.com/questions/1484506
function getRandomColor() {
        var letters = '0123456789ABCDEF'.split('');
        var color = ''; // In my case, I don't want the leading #
        for (var i = 0; i < 6; i++ ) {
                color += letters[Math.floor(Math.random() * 16)];
        }
        return color;
}

function CallDiagramScript(){
        // Create request string: this is the request that is passed to the python script.
        var requeststring="";
        // Create legend string: this is a Wikipedia markup legend that can be pasted into an article.
        var legendstring="";
        var legendname = "";
        var legendnum  = "";
	var totalseats = 0; //count total seats to check for empty diagram
        var partylist   = new Array();
        $( "input" ).each( function() { 
                if(this.name.match( /^Name/ )){
                  partylist[/[0-9]+$/.exec(this.name)[0]]={Name: this.value };
                }
                if(this.name.match( /^Number/ )){
                  partylist[/[0-9]+$/.exec(this.name)[0]]['Num']=this.value;
                }
                if(this.name.match( /^Color/ )){
                  partylist[/[0-9]+$/.exec(this.name)[0]]['Color']=this.value;
                }
		//If we're processing a border checkbox, only add "none" if it's not checked.
                if(this.name.match( /^Border/ )){
		  if(!this.checked){
		    partylist[/[0-9]+$/.exec(this.name)[0]]['BColor']="none";
		  }
                }
		//If we're processing a border color, don't overwrite a "none" value.
                if(this.name.match( /^BColor/ )){
                  if(partylist[/[0-9]+$/.exec(this.name)[0]]['BColor']!="none"){
		    partylist[/[0-9]+$/.exec(this.name)[0]]['BColor']=this.value;
		  }
                }
        });
        var arrayLength = partylist.length;
        for (var i = 1; i < arrayLength; i++) {
          if(partylist[i]) {
              requeststring += partylist[i]['Name'];
              requeststring += ', ';
              requeststring += partylist[i]['Num'];
	      totalseats += partylist[i]['Num'];
              requeststring += ', ';
              requeststring += '#';
              requeststring += partylist[i]['Color'];
              requeststring += ', ';
              if(partylist[i]['BColor'] !="none"){requeststring += '#'};
              requeststring += partylist[i]['BColor'];
              if ( i < (arrayLength - 1)){ requeststring += '; '}
              if (partylist[i]['Num'] == 1){
                legendstring += "{{legend|#" + partylist[i]['Color'] +"|" + partylist[i]['Name'] +": 1 seat}} "
              }
              else {
                legendstring += "{{legend|#" + partylist[i]['Color'] +"|" + partylist[i]['Name'] +": "+ partylist[i]['Num']+" seats}} "
              }
              }
            }
            if(totalseats > 0){
        //Now post the request to the script which actually makes the diagram.
        $.ajax({
                type: "POST",
                url: "newarch.py",
                data: {inputlist: requeststring },
        }).done( function(data,status){
		data=data.trim();
                var postcontainer = document.getElementById("postcontainer"); //This will get the first node with id "postcontainer"
		while (postcontainer.hasChildNodes()) { //Remove old images
		    postcontainer.removeChild(postcontainer.lastChild);
		}
                //Now add the svg image to the page
                var img = document.createElement("img");
                img.src = data;
		img.setAttribute("id", "SVGdiagram");
                postcontainer.appendChild(img);
                //and a linebreak
                postcontainer.appendChild(document.createElement("br"));
                //Add a link with the new diagram
                var a = document.createElement('a');
                var linkText = document.createTextNode("Click to download your SVG diagram.");
                a.appendChild(linkText);
                a.title = "SVG diagram";
                a.href = data;
                a.download = data;
                postcontainer.appendChild(a);
                //and a linebreak
                postcontainer.appendChild(document.createElement("br"));
                //Now add the legend template text with the party names, colours and support.
                var newtext = document.createTextNode("Legend template for use in Wikipedia:");
                postcontainer.appendChild(newtext);
                postcontainer.appendChild(document.createElement("br"));
                newtext = document.createTextNode(legendstring);
                postcontainer.appendChild(newtext);
                postcontainer.appendChild(document.createElement("br"));
                postcontainer.appendChild(document.createElement("br"));
		//File upload name label
		var filenametitle=document.createElement('div');
		filenametitle.className = 'left greendiv';
		filenametitle.innerHTML = "Filename to upload:";
		postcontainer.appendChild(filenametitle);
		//File upload name input control
		var input=document.createElement('div');
		inputname = data.replace(/.*\//,'').replace(/.svg\s*$/,'');
		input.innerHTML = '<input class="right" type="text" name="' +  inputname + '" id="inputFilename" value= "My_Parliament.svg" >';
		postcontainer.appendChild(input);
		//Year label
		var yeartitle=document.createElement('div');
		yeartitle.className = 'left greendiv';
		yeartitle.innerHTML = "Election year:";
		postcontainer.appendChild(yeartitle);
		//Year input control
		var input=document.createElement('div');
		input.innerHTML = '<input class="right" type="number" name="year" id="year" min="0" max="'+(new Date()).getFullYear()+'" value='+(new Date()).getFullYear()+' oninput="updateFilename()" >';
		postcontainer.appendChild(input);
		//Country label
		var countrytitle=document.createElement('div');
		countrytitle.className = 'left greendiv';
		countrytitle.innerHTML = "Country:";
		postcontainer.appendChild(countrytitle);
		//Country input control
		var input=document.createElement('div');
		input.innerHTML = '<input class="right" type="text" name="country" id="country" value=""  oninput="updateFilename()">';
		postcontainer.appendChild(input);
		//Locality label
		var localitytitle=document.createElement('div');
		localitytitle.className = 'left greendiv';
		localitytitle.innerHTML = "Locality:";
		postcontainer.appendChild(localitytitle);
		//Locality input control
		var input=document.createElement('div');
		input.innerHTML = '<input class="right" type="text" name="locality" id="locality" value=""  oninput="updateFilename()">';
		postcontainer.appendChild(input);
		//Body label
		var bodytitle=document.createElement('div');
		bodytitle.className = 'left greendiv';
		bodytitle.innerHTML = "Body (e.g. Town Council, Bundestag or Senate):";
		postcontainer.appendChild(bodytitle);
		//Body input control
		var input=document.createElement('div');
		input.innerHTML = '<input class="right" type="text" name="body" id="body" value="Parliament" oninput="updateFilename()">';
		postcontainer.appendChild(input);
                postcontainer.appendChild(document.createElement("br"));
                //Button to add a link to upload the new diagram
		var uploadlinkbutton=document.createElement('div');
		uploadlinkbutton.className = 'button greenbutton';
		uploadlinkbutton.innerHTML = "This image is for a real-world body or a notable work of fiction and I want to upload it to Commons.<br />I understand that images uploaded for private use can be deleted without notice and can lead to my username being blocked.";
		uploadlinkbutton.setAttribute("onClick", 'makeUploadLink("'+ inputname +'", "'+ data +'", "' + legendstring + '")');
		postcontainer.appendChild(uploadlinkbutton);
                //and a linebreak
                postcontainer.appendChild(document.createElement("br"));
        })
	.fail( function(xhr, textStatus, errorThrown) { //data doesn't contain "svg", so post an error message instead
		var postcontainer = document.getElementById("postcontainer"); //This will get the first node with id "postcontainer"
		while (postcontainer.hasChildNodes()) { //Remove old images
		    postcontainer.removeChild(postcontainer.lastChild);
		}
		var newpost = document.createElement("div"); //This is the new postcontainer that will hold our stuff.
		postcontainer.appendChild(newpost);
		var errordiv=document.createElement('div');
		errordiv.id="error";
		errordiv.className = 'error';
		errordiv.innerHTML = "Oops, your diagram wasn't successfully generated! Maybe you have more than 31061 seats. If not, please raise a bug report.";
		newpost.appendChild(errordiv);
		//add a linebreak
		newpost.appendChild(document.createElement("br"));
		//Even though we failed, still add the legend template text with the party names, colours and support.
		var newtext = document.createTextNode("Legend template for use in Wikipedia:");
		newpost.appendChild(newtext);
		newpost.appendChild(document.createElement("br"));
		newtext = document.createTextNode(legendstring);
		newpost.appendChild(newtext);
		newpost.appendChild(document.createElement("br"));}
	);
        console.log(requeststring);
        console.log(legendstring);
      }
	    else
	    {
	    alert("There are no delegates in your parliament. Cannot generate a diagram!");
	    }
}
 
function updateFilename(){
	newFilename="";
	if (document.getElementById("country").value) {newFilename = document.getElementById("country").value}
	if (document.getElementById("locality").value) {
		if (newFilename) {newFilename += "_"}
		newFilename += document.getElementById("locality").value
	} 
	if (document.getElementById("body").value) {
		if (newFilename) {newFilename += "_"}
		newFilename += document.getElementById("body").value
	} 
	if (document.getElementById("year").value) {
		if (newFilename) {newFilename += "_"}
		newFilename += document.getElementById("year").value
	}
	if (newFilename=="") {newFilename = "My_Parliament"}
	newFilename += ".svg";
	document.getElementById("inputFilename").value = newFilename;
}

function makeUploadLink(inputname, linkdata, legendtext){
	var a = document.createElement('a');
	var fname="";
	//This is kind of dumb: I'm iterating through all the inputs on the
	//page to find any that match the name that's being called. FIXME
	$( "input" ).each( function() { 
			if(this.name == inputname){
				fname = this.value
			}
	});
	fname = fname.replace(/(.svg)*$/i, ".svg");
	var linkText = document.createTextNode("Click to upload "+fname+" to Wikimedia Commons");
	a.appendChild(linkText);
	//Now get today's date and format it suitably for use in Wikimedia Commons templates:
	var today = new Date();
	var DD = today.getDate();
	var MM = today.getMonth()+1;
	var YYYY = today.getFullYear();

	if(DD<10) {
		DD='0'+DD
	} 

	if(MM<10) {
		MM='0'+MM
	} 

	today = YYYY+'-'+MM+'-'+DD;
	//Now build the query URL that will be used to upload the image to Commons:
	a.href = document.URL.replace(/\?.*$/,'') + "?action=upload&uri=/data/project/parliamentdiagram/public_html/" + linkdata + "&filename=" + fname + "&pagecontent=" + encodeURIComponent( "== {{int:filedesc}} ==\n{{Information\n|description = " + legendtext + "\n|date = " + today + "\n|source = [https://tools.wmflabs.org/parliamentdiagram/parliamentinputform.html Parliament diagram tool]\n|author = \n|permission = {{PD-shape}}\n|other versions =\n}}\n\n[[Category:Election apportionment diagrams]]\n");
	a.setAttribute('target', '_blank');
	var SVGdiagram = document.getElementById("SVGdiagram"); //This will get the first node with id "SVGdiagram"
	var diagramparent = SVGdiagram.parentNode; //This will get the parent div that contains the diagram
	diagramparent.insertBefore(a, SVGdiagram.nextSibling); //Insert our new node after the diagram
	diagramparent.insertBefore(document.createElement("br"), SVGdiagram.nextSibling); //Insert a linebreak after the diagram
}
function deleteParty(i){
  var delparty = document.getElementById("party"+i);
  var partylistcontainer = document.getElementById("partylistcontainer");
  partylistcontainer.removeChild(delparty);
}
