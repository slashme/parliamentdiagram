function CallArchScript(){
    // Create request string: this is the request that is passed to the python script.
    var requeststring="";
    var Demnum="";
    var Repnum="";
    var Indnum="";
    var Vacnum="";
    let requestJSON={};  // This is what we send to the python script
        requestJSON.denser_rows = false; //Because I'm not going to implement this here yet
    requestJSON.parties = []
    $("input").each(function() {
        if(this.value < 1){this.value = 0;}; //Make sure it's a number!
        switch(this.name){
            case "Dem":
                let demJSON = {}
                demJSON.name = "Democrats"
                demJSON.nb_seats = parseInt(this.value);
                demJSON.color = "#0000FF";
                demJSON.border_size = 0;
                demJSON.border_color = "#000000";
                requestJSON.parties.push(demJSON)
                break;
            case "Rep":
                let repJSON = {}
                repJSON.name = "Republicans"
                repJSON.nb_seats = parseInt(this.value);
                repJSON.color = "#FF0000";
                repJSON.border_size = 0;
                repJSON.border_color = "#000000";
                requestJSON.parties.push(repJSON)
                break;
            case "Ind":
                let indJSON = {}
                indJSON.name = "Independents"
                indJSON.nb_seats = parseInt(this.value);
                indJSON.color = "#C9C9C9";
                indJSON.border_size = 0;
                indJSON.border_color = "#000000";
                requestJSON.parties.push(indJSON)
                break;
            case "Vac":
                let vacJSON = {}
                vacJSON.name = "Vacant"
                vacJSON.nb_seats = parseInt(this.value);
                vacJSON.color = "#6B6B6B";
                vacJSON.border_size = 0;
                vacJSON.border_color = "#000000";
                requestJSON.parties.push(vacJSON)
                break;
            }
        }
    );
    console.log(requestJSON);

    //Now post the request to the script which actually makes the diagram.
    $.ajax({
        type: "POST",
        url: "newarch.py",
                data: {data: JSON.stringify(requestJSON)},
    }).done(function(data,status){
        data=data.trim();
        var postcontainer = document.getElementById("postcontainer"); //This will get the first node with id "postcontainer"
        var postparent = postcontainer.parentNode; //This will get the parent div that contains all the graphs
        var newpost = document.createElement("div"); //This is the new postcontainer that will hold our stuff.
        postparent.insertBefore(newpost, postcontainer);
        newpost.setAttribute("id", "postcontainer");
        //Now add the svg image to the page
        var img = document.createElement("img");
        img.src = data;
        newpost.appendChild(img);
        //and a linebreak
        newpost.appendChild(document.createElement("br"));
        //Add a link with the new diagram
        var a = document.createElement('a');
        var linkText = document.createTextNode("Click to download your SVG diagram.");
        a.appendChild(linkText);
        a.title = "SVG diagram";
        a.href = data;
        a.download = data;
        newpost.appendChild(a);
        //and a linebreak
        newpost.appendChild(document.createElement("br"));
    });
}
