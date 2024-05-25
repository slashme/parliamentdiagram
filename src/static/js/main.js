$(document).ready(function () {
    $.ajax({
        dataType: "json",
        url: "https://query.wikidata.org/sparql?query=SELECT%20DISTINCT%20%3Fstate%20%3FstateLabel%20%3Fid%20WHERE%20%7B%0A%20%20%3Fstate%20wdt%3AP31%2Fwdt%3AP279%2a%20wd%3AQ3624078%3B%0A%20%20%20%20%20%20%20%20%20p%3AP463%20%3FmemberOfStatement.%0A%20%20%3FmemberOfStatement%20a%20wikibase%3ABestRank%3B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20ps%3AP463%20wd%3AQ1065.%0A%20%20MINUS%20%7B%20%3FmemberOfStatement%20pq%3AP582%20%3FendTime.%20%7D%0A%20%20MINUS%20%7B%20%3Fstate%20wdt%3AP576%7Cwdt%3AP582%20%3Fend.%20%7D%0A%20%20BIND%28STRAFTER%28STR%28%3Fstate%29%2C%20STR%28wd%3A%29%29%20AS%20%3Fid%29%0A%20%20SERVICE%20wikibase%3Alabel%20%7B%20bd%3AserviceParam%20wikibase%3Alanguage%20%22en%22.%20%7D%0A%7D%20ORDER%20BY%20%3FstateLabel&format=json",
    }).done(function (data) {
        $.each(data.results.bindings, function (key, value) {
            $('#countrylist').append($("<option></option>").attr("value", value.id.value).text(value.stateLabel.value));
        });
    });
    $('#countrylist').select2();

    $('#wdpartylist').click(function () {
        var country_WD_item = $('#countrylist').val();
        $.ajax({
            dataType: "json",
            url: "https://query.wikidata.org/sparql?query=SELECT%20%3FwdPlain%20%3Flabel_en%20%3Fshort%20%3Fdisplay%0AWHERE%0A%7B%0A%20%20%3Fparty%20wdt%3AP31%2Fwdt%3AP279*%20wd%3AQ7278.%20%3Fparty%20wdt%3AP17%20wd%3A" + country_WD_item + ".%20%0A%20%20OPTIONAL%20%7B%20%3Fparty%20wdt%3AP1813%20%3Fshort.%20%7D%0A%20%20%3Fparty%20rdfs%3Alabel%20%3Flabel_en%20filter%20(lang(%3Flabel_en)%20%3D%20%22en%22).%0A%20%20BIND(REPLACE(STR(%3Fparty)%2C%22http%3A%2F%2Fwww.wikidata.org%2Fentity%2F%22%2C%22%22)%20AS%20%3FwdPlain)%0A%20%20BIND(COALESCE(%3Fshort%2C%20%3Flabel_en)%20AS%20%3Fdisplay)%0A%7D%20ORDER%20BY%20%3Flabel_en&format=json",
        }).done(function (data) {
            $('#partylist')
                .find('option')
                .remove()
                .end();
            $.each(data.results.bindings, function (key, value) {
                $('#partylist').append($("<option></option>").attr("value", value.wdPlain.value).text(value.label_en.value))
            });
            $('#partylist').select2();
        });
    });

    $('#addpartybutton').click(function () {
        var newname = $('#partylist :selected').text();
        if (newname == "Select your country first!") { newname = "" }
        addParty(newname);
        console.log(newname);
    });

    $('#addpartymanual').click(function () {
        addParty();
    });

    // searching for /seats?/ at the end does not work for other languages, for example french uses "sièges"
    const wikitextregexp = /{{\s*legend\s*\|\s*([^|]*)\|\s*([^:]*)(?::\s*(\d+))?/g;
    $('#getfile').click(function () {
        $.ajax({
            dataType: "json",
            url: "https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=revisions&titles=" + $("#inputfile").val() + "&rvprop=content&rvlimit=1&callback=?",
        }).done(function (data) {
            let wikitext;
            $.each(data.query.pages, function (i, item) {
                wikitext = item.revisions[0]['*'];
            });

            const partiesdata = [];
            for (let [, color, partyname, nseats] of wikitext.matchAll(wikitextregexp)) {
                partiesdata.push([partyname, color, nseats]);
            }

            // Delete all parties first
            $("div").each(function () {
                const thisid = this.id;
                if (thisid.match(/^party[0-9]+$/)) {
                    deleteParty(parseInt(/[0-9]+$/.exec(thisid)[0]));
                }
            });

            partiesdata.forEach(function (triplet) {
                addParty(...triplet);
            });
        });
    });

    // Enable/disable advanced parameters
    let enable_advanced_btn = $('#enable-advanced');
    let disable_advanced_btn = $('#disable-advanced');
    let advanced_body = $('#advanced-body');
    enable_advanced_btn.click(function () {
        enable_advanced_btn.hide();
        disable_advanced_btn.show();
        advanced_body.show();
    });
    disable_advanced_btn.click(function () {
        enable_advanced_btn.show();
        disable_advanced_btn.hide();
        advanced_body.hide();
    });
});

function addParty(newname = "", newcolor = "", newnseats = 0) {
    // Party list <div> where dynamic content will be placed
    var partylistcontainer = document.getElementById("partylistcontainer");
    //New party's number: one more than the largest party number so far:
    i = 0;
    $("div").each(function () {
        if (this.id.match(/^party[0-9]+$/)) {
            i = Math.max(i, parseInt(/[0-9]+$/.exec(this.id)[0]));
        }
    });
    i++;
    var newpartydiv = document.createElement('div');
    newpartydiv.id = "party" + i;
    partylistcontainer.appendChild(newpartydiv);
    //Party name label
    var partytitle = document.createElement('div');
    partytitle.className = 'left';
    if (newname == "") { newname = "Party " + i }
    partytitle.innerHTML = "Party " + i + " Name";
    newpartydiv.appendChild(partytitle);
    //Party name input control
    var input = document.createElement('div');
    input.innerHTML = '<input class="right" type="text" name="Name' + i + '" value="' + newname + '">'
    newpartydiv.appendChild(input);
    //Party support name tag
    var partysupport = document.createElement('div');
    partysupport.className = 'left';
    partysupport.innerHTML = "Party " + i + " delegates";
    newpartydiv.appendChild(partysupport);
    //Party support input control
    var input = document.createElement('div');
    input.innerHTML = '<input class="right" type="number" name="Number' + i + '" value= "' + newnseats + '" >';
    newpartydiv.appendChild(input);
    //Party color name tag
    var partycolor = document.createElement('div');
    partycolor.className = 'left';
    partycolor.innerHTML = "Party " + i + " color";
    newpartydiv.appendChild(partycolor);
    //Party color input control
    var input = document.createElement('div');
    if (newcolor == "") { newcolor = getRandomColor() }
    input.innerHTML = '<input class="right jscolor" type="text" name="Color' + i + '" value= "' + newcolor + '" >'
    newpartydiv.appendChild(input);
    //Party border width name tag
    var partycolor = document.createElement('div');
    partycolor.className = 'left';
    partycolor.innerHTML = "Party " + i + " border width";
    newpartydiv.appendChild(partycolor);
    //Party border width control
    var input = document.createElement('div');
    input.innerHTML = '<input class="right" type="number" name="Border' + i + '" type="number" step="0.01" min="0.0" max="1.0" value="0.00">'
    newpartydiv.appendChild(input);
    //Party border color name tag
    var partybcolor = document.createElement('div');
    partybcolor.className = 'left';
    partybcolor.innerHTML = "Party " + i + " border color";
    newpartydiv.appendChild(partybcolor);
    //Party border color input control
    var input = document.createElement('div');
    input.innerHTML = '<input class="right jscolor" type="text" name="BColor' + i + '" value= "000000" >'
    newpartydiv.appendChild(input);
    var delbutton = document.createElement('div');
    delbutton.className = 'button deletebutton';
    delbutton.innerHTML = "Delete party " + i;
    delbutton.setAttribute("onClick", "deleteParty(" + i + ")");
    newpartydiv.appendChild(delbutton);
    //Add a newline
    newpartydiv.appendChild(document.createElement("br"));
    //$( "input[name=Color" + i + "]").addClass('color'); /* no longer needed because I'm writing the innerHTML
    jscolor.installByClassName("jscolor");
}

//Generate random color, based on http://stackoverflow.com/questions/1484506
function getRandomColor() {
    var letters = '0123456789ABCDEF'.split('');
    var color = ''; // In my case, I don't want the leading #
    for (var i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

function CallDiagramScript() {
    const requestJSON = {};  // This is what we send to the python script

    // Retrieve advanced parameters
    requestJSON.denser_rows = $('#advanced-body').is(':visible') && $('#row-densifier').is(':checked');

    const partylist = new Array();
    $("input").each(function () {
        const thisname = this.name;
        if (thisname.startsWith("Name")) {
            partylist[/[0-9]+$/.exec(thisname)[0]] = { Name: this.value };
        } else if (thisname.startsWith("Number")) {
            partylist[/[0-9]+$/.exec(thisname)[0]]['Num'] = this.value;
        } else if (thisname.startsWith("Color")) {
            partylist[/[0-9]+$/.exec(thisname)[0]]['Color'] = this.value;
        } else if (thisname.startsWith("Border")) {
            //If we're processing a border width, add value if it's a number, maxing out at 1.
            //Add 0 if it's not a number or if it's equal to 0.
            let bwidth = parseFloat(this.value);
            if (isNaN(bwidth)) { bwidth = 0 }; //!\\
            bwidth = Math.min(Math.max(bwidth, 0), 1);
            partylist[/[0-9]+$/.exec(thisname)[0]]['Border'] = bwidth;
        } else if (thisname.startsWith("BColor")) {
            partylist[/[0-9]+$/.exec(thisname)[0]]['BColor'] = this.value;
        }
    });

    // Create legend string: this is a Wikipedia markup legend that can be pasted into an article.
    let legendstring = "";
    let totalseats = 0; //count total seats to check for empty diagram
    requestJSON.parties = [];
    for (let party of partylist) {
        if (party) {
            let partyJSON = {}
            const num = parseInt(party['Num']);
            partyJSON.name = party['Name'].replace(',', '');
            partyJSON.nb_seats = parseInt(num);
            partyJSON.color = '#' + party['Color'];
            partyJSON.border_size = parseFloat(party['Border']);
            partyJSON.border_color = '#' + party['BColor'];
            requestJSON.parties.push(partyJSON);

            totalseats += num;

            if (num == 1) {
                legendstring += "{{legend|#" + party['Color'] + "|" + party['Name'] + ": 1 seat}} ";
            } else {
                legendstring += "{{legend|#" + party['Color'] + "|" + party['Name'] + ": " + num + " seats}} ";
            }
        }
    }
    if (totalseats > 0) {
        //Now post the request to the script which actually makes the diagram.
        $.ajax({
            type: "POST",
            url: "newarch.py",
            data: { data: JSON.stringify(requestJSON) },
        }).done(function (data, status) {
            data = data.trim();

            // This will get the first node with id "postcontainer"
            const postcontainer = document.getElementById("postcontainer");
            // Remove old images
            while (postcontainer.hasChildNodes()) {
                postcontainer.removeChild(postcontainer.lastChild);
            }

            // This will get the first node with id "postcontainerbutton"
            const postcontainerbutton = document.getElementById("postcontainerbutton");
            // Remove stale upload button, if any
            while (postcontainerbutton.hasChildNodes()) {
                postcontainerbutton.removeChild(postcontainerbutton.lastChild);
            }

            // Now add the svg image to the page
            const img = document.createElement("img");
            img.src = data;
            img.setAttribute("id", "SVGdiagram");
            postcontainer.appendChild(img);
            // and a linebreak
            postcontainer.appendChild(document.createElement("br"));

            // Add a link with the new diagram
            const abtn = document.createElement('a');
            abtn.className = "btn btn-success"
            abtn.appendChild(document.createTextNode("Click to download your SVG diagram."));
            abtn.title = "SVG diagram";
            abtn.href = data;
            abtn.download = data;
            postcontainer.appendChild(abtn);
            // and a horizontal line
            postcontainer.appendChild(document.createElement("hr"));

            // Now add the legend template text with the party names, colours and support.
            const legendtitle = document.createElement('h4');
            postcontainer.appendChild(legendtitle);
            legendtitle.appendChild(document.createTextNode("Legend template for use in Wikipedia:"));
            postcontainer.appendChild(document.createElement("br"));
            postcontainer.appendChild(document.createTextNode(legendstring));
            postcontainer.appendChild(document.createElement("hr"));

            // File upload name label
            const filenametitle = document.createElement('div');
            filenametitle.className = 'left greendiv';
            filenametitle.innerHTML = "Filename to upload:";
            postcontainer.appendChild(filenametitle);

            // File upload name input control
            let input = document.createElement('div');
            input.innerHTML = '<input class="right" type="text" name="' + data.replace(/.*\//, '').replace(/.svg\s*$/, '') + '" id="inputFilename" value= "My_Parliament.svg" >';
            postcontainer.appendChild(input);

            // Year label
            let yeartitle = document.createElement('div');
            yeartitle.className = 'left greendiv';
            yeartitle.innerHTML = "Election year:";
            postcontainer.appendChild(yeartitle);

            // Year input control
            input = document.createElement('div');
            input.innerHTML = '<input class="right" type="number" name="year" id="year" min="0" max="' + (new Date()).getFullYear() + '" value=' + (new Date()).getFullYear() + ' oninput="updateFilename()" >';
            postcontainer.appendChild(input);

            // Country label
            const countrytitle = document.createElement('div');
            countrytitle.className = 'left greendiv';
            countrytitle.innerHTML = "Country:";
            postcontainer.appendChild(countrytitle);

            // Country input control
            input = document.createElement('div');
            input.innerHTML = '<input class="right" type="text" name="country" id="country" value=""  oninput="updateFilename()">';
            postcontainer.appendChild(input);

            // Locality label
            const localitytitle = document.createElement('div');
            localitytitle.className = 'left greendiv';
            localitytitle.innerHTML = "Locality:";
            postcontainer.appendChild(localitytitle);

            // Locality input control
            input = document.createElement('div');
            input.innerHTML = '<input class="right" type="text" name="locality" id="locality" value=""  oninput="updateFilename()">';
            postcontainer.appendChild(input);

            // Body label
            const bodytitle = document.createElement('div');
            bodytitle.className = 'left greendiv';
            bodytitle.innerHTML = "Body (e.g. Town Council, Bundestag or Senate):";
            postcontainer.appendChild(bodytitle);

            // Body input control
            input = document.createElement('div');
            input.innerHTML = '<input class="right" type="text" name="body" id="body" value="Parliament" oninput="updateFilename()">';
            postcontainer.appendChild(input);
            postcontainer.appendChild(document.createElement("br"));

            // Button to add a link to upload the new diagram
            const uploadwarn = document.createElement('div');
            uploadwarn.className = 'notice';
            uploadwarn.innerHTML = "This image is for a real-world body or a notable work of fiction and I want to upload it to Commons.<br />I understand that images uploaded for private use can be deleted without notice and can lead to my username being blocked.";
            postcontainer.appendChild(uploadwarn);

            const uploadlinkbutton = document.createElement('a');
            uploadlinkbutton.className = 'btn btn-primary';
            uploadlinkbutton.setAttribute("onClick", 'makeUploadLink("' + inputname + '", "' + data + '", "' + legendstring + '")');
            uploadlinkbutton.appendChild(document.createTextNode("Generate upload link"));
            postcontainer.appendChild(uploadlinkbutton);
            // and a linebreak
            postcontainer.appendChild(document.createElement("br"));
        }).fail(function (xhr, textStatus, errorThrown) {
            // data doesn't contain "svg", so post an error message instead

            // This will get the first node with id "postcontainer"
            const postcontainer = document.getElementById("postcontainer");

            // Remove old images
            while (postcontainer.hasChildNodes()) {
                postcontainer.removeChild(postcontainer.lastChild);
            }

            // This is the new postcontainer that will hold our stuff.
            const newpost = document.createElement("div");
            postcontainer.appendChild(newpost);

            const errordiv = document.createElement("div");
            errordiv.id = "error";
            errordiv.className = "error";
            errordiv.appendChild(document.createTextNode("Oops, your diagram wasn't successfully generated!"));
            errordiv.appendChild(document.createElement("br"));
            errordiv.appendChild(document.createTextNode("(" + textStatus + ", " + errorThrown + ")"));
            errordiv.appendChild(document.createElement("br"));
            errordiv.appendChild(document.createTextNode("Please raise a "));
            const bugreportlink = document.createElement("a");
            bugreportlink.href = "https://github.com/slashme/parliamentdiagram/issues/new";
            bugreportlink.appendChild(document.createTextNode("bug report"));
            errordiv.appendChild(bugreportlink);
            errordiv.appendChild(document.createTextNode("."));
            newpost.appendChild(errordiv);
            // add a linebreak
            newpost.appendChild(document.createElement("br"));

            // Even though we failed, still add the legend template text with the party names, colours and support.
            newpost.appendChild(document.createTextNode("Legend template for use in Wikipedia:"));
            newpost.appendChild(document.createElement("br"));
            newpost.appendChild(document.createTextNode(legendstring));
            newpost.appendChild(document.createElement("br"));
        });
        console.log(requestJSON);
        console.log(legendstring);
    } else {
        alert("There are no delegates in your parliament. Cannot generate a diagram!");
    }
}

function updateFilename() {
    const filenameElements = [];
    if (document.getElementById("country").value) {
        filenameElements.push(document.getElementById("country").value);
    }
    if (document.getElementById("locality").value) {
        filenameElements.push(document.getElementById("locality").value);
    }
    if (document.getElementById("body").value) {
        filenameElements.push(document.getElementById("body").value);
    }
    if (document.getElementById("year").value) {
        filenameElements.push(document.getElementById("year").value);
    }

    let newFilename = "";
    if (filenameElements.length > 0) {
        newFilename = filenameElements.join("_");
    } else {
        newFilename = "My_Parliament";
    }
    newFilename += ".svg";

    document.getElementById("inputFilename").value = newFilename;
}

function makeUploadLink(inputname, linkdata, legendtext) {
    var a = document.createElement('a');
    a.className = "btn btn-primary";
    var fname = "";
    //This is kind of dumb: I'm iterating through all the inputs on the
    //page to find any that match the name that's being called. FIXME
    $("input").each(function () {
        if (this.name == inputname) {
            fname = this.value
        }
    });
    fname = fname.replace(/(.svg)*$/i, ".svg");
    var linkText = document.createTextNode("Click to upload " + fname + " to Wikimedia Commons");
    a.appendChild(linkText);
    //Now get today's date and format it suitably for use in Wikimedia Commons templates:
    var today = new Date();
    var DD = today.getDate();
    var MM = today.getMonth() + 1;
    var YYYY = today.getFullYear();

    if (DD < 10) {
        DD = '0' + DD
    }

    if (MM < 10) {
        MM = '0' + MM
    }

    today = YYYY + '-' + MM + '-' + DD;
    //Now build the query URL that will be used to upload the image to Commons:
    a.href = document.URL.replace(/\?.*$/, '') + "?action=upload&uri=/data/project/parliamentdiagram/public_html/" + linkdata + "&filename=" + fname + "&pagecontent=" + encodeURIComponent("== {{int:filedesc}} ==\n{{Information\n|description = " + legendtext + "\n|date = " + today + "\n|source = [https://parliamentdiagram.toolforge.org/parliamentinputform.html Parliament diagram tool]\n|author = [[User:{{subst:REVISIONUSER}}]]\n|permission = {{PD-shape}}\n|other versions =\n}}\n\n[[Category:Election apportionment diagrams]]\n");
    a.setAttribute('target', '_blank');
    buttonlocation = document.getElementById("postcontainerbutton");
    buttonlocation.innerHtml = "";
    buttonlocation.append(a);
    //    var SVGdiagram = document.getElementById("SVGdiagram"); //This will get the first node with id "SVGdiagram"
    //    var diagramparent = SVGdiagram.parentNode; //This will get the parent div that contains the diagram
    //    diagramparent.insertBefore(a, SVGdiagram.nextSibling); //Insert our new node after the diagram
    //    diagramparent.insertBefore(document.createElement("br"), SVGdiagram.nextSibling); //Insert a linebreak after the diagram
}

function deleteParty(i) {
    var delparty = document.getElementById("party" + i);
    var partylistcontainer = document.getElementById("partylistcontainer");
    partylistcontainer.removeChild(delparty);
}
