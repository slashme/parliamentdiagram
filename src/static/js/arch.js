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
        $.ajax({
            dataType: "json",
            url: "https://query.wikidata.org/sparql?query=SELECT%20%3FwdPlain%20%3Flabel_en%20%3Fshort%20%3Fdisplay%0AWHERE%0A%7B%0A%20%20%3Fparty%20wdt%3AP31%2Fwdt%3AP279*%20wd%3AQ7278.%20%3Fparty%20wdt%3AP17%20wd%3A" + $('#countrylist').val() + ".%20%0A%20%20OPTIONAL%20%7B%20%3Fparty%20wdt%3AP1813%20%3Fshort.%20%7D%0A%20%20%3Fparty%20rdfs%3Alabel%20%3Flabel_en%20filter%20(lang(%3Flabel_en)%20%3D%20%22en%22).%0A%20%20BIND(REPLACE(STR(%3Fparty)%2C%22http%3A%2F%2Fwww.wikidata.org%2Fentity%2F%22%2C%22%22)%20AS%20%3FwdPlain)%0A%20%20BIND(COALESCE(%3Fshort%2C%20%3Flabel_en)%20AS%20%3Fdisplay)%0A%7D%20ORDER%20BY%20%3Flabel_en&format=json",
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
        const newname = $('#partylist :selected').text();
        console.log(newname);
        if (newname != "Select your country first!") {
            addParty(newname);
        }
    });

    $('#addpartymanual').click(function () {
        addParty();
    });

    // searching for /seats?/ at the end does not work for other languages, for example french uses "sièges"
    const wikitextregexp = /{{\s*legend\s*(?:\||｜)\s*([^|｜]*)(?:\||｜)\s*([^:：]*)(?::|：)\s*(\d+)[^}]*}}/g;
    $('#getfile').click(function () {
        $.ajax({
            dataType: "json",
            url: "https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=revisions&titles=" + $("#inputfile").val() + "&rvprop=content&rvlimit=1&callback=?",
        }).done(function (data) {
            let wikitext = 0;
            try {
                $.each(data.query.pages, function (i, item) {
                    wikitext = item.revisions[0]['*'];
                });
            } catch (e) {
                console.log(e);
                wikitext = 0;
            }
            if (wikitext == 0) {
                alert("Can't find the file on Commons. Please check the filename and try again.");
                return;
            }

            const partiesdata = [];
            for (let [, color, partyname, nseats] of wikitext.matchAll(wikitextregexp)) {
                partiesdata.push([partyname, color, nseats]);
            }

            if (partiesdata.length > 0) {
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
            } else {
                alert("Can't find number of seats, this is possibly an old diagram or one where the legend has been modified.")
            }
        }).fail(function () {
            alert("The request to Commons failed. Please check the filename and try again.");
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
    const partylistcontainer = document.getElementById("partylistcontainer");
    //New party's number: one more than the largest party number so far:
    let i = 0;
    $("div").each(function () {
        if (this.id.match(/^party[0-9]+$/)) {
            i = Math.max(i, parseInt(/[0-9]+$/.exec(this.id)[0]));
        }
    });
    i++;

    const newpartydiv = document.createElement('div');
    newpartydiv.id = "party" + i;
    partylistcontainer.appendChild(newpartydiv);

    // Party name label
    const partytitle = document.createElement('div');
    partytitle.className = 'left';
    if (newname == "") { newname = "Party " + i }
    partytitle.innerHTML = "Party " + i + " Name";
    newpartydiv.appendChild(partytitle);

    // Party name input control
    let input = document.createElement('div');
    input.innerHTML = '<input class="right" type="text" name="Name' + i + '" value="' + newname + '">'
    newpartydiv.appendChild(input);

    // Party support name tag
    const partysupport = document.createElement('div');
    partysupport.className = 'left';
    partysupport.innerHTML = "Party " + i + " delegates";
    newpartydiv.appendChild(partysupport);

    // Party support input control
    input = document.createElement('div');
    input.innerHTML = '<input class="right" type="number" name="Number' + i + '" value= "' + newnseats + '" >';
    newpartydiv.appendChild(input);

    // Party color name tag
    const partycolor = document.createElement('div');
    partycolor.className = 'left';
    partycolor.innerHTML = "Party " + i + " color";
    newpartydiv.appendChild(partycolor);

    // Party color input control
    input = document.createElement('div');
    if (newcolor == "") { newcolor = getRandomColor() }
    input.innerHTML = '<input class="right jscolor" type="text" name="Color' + i + '" value= "' + newcolor + '" >'
    newpartydiv.appendChild(input);

    // Party border width name tag
    const partybwidth = document.createElement('div');
    partybwidth.className = 'left';
    partybwidth.innerHTML = "Party " + i + " border width";
    newpartydiv.appendChild(partybwidth);

    // Party border width control
    input = document.createElement('div');
    input.innerHTML = '<input class="right" type="number" name="Border' + i + '" type="number" step="0.01" min="0.0" max="1.0" value="0.00">'
    newpartydiv.appendChild(input);

    // Party border color name tag
    const partybcolor = document.createElement('div');
    partybcolor.className = 'left';
    partybcolor.innerHTML = "Party " + i + " border color";
    newpartydiv.appendChild(partybcolor);

    // Party border color input control
    input = document.createElement('div');
    input.innerHTML = '<input class="right jscolor" type="text" name="BColor' + i + '" value= "000000" >'
    newpartydiv.appendChild(input);

    const delbutton = document.createElement('div');
    delbutton.className = 'button deletebutton';
    delbutton.innerHTML = "Delete party " + i;
    delbutton.setAttribute("onClick", "deleteParty(" + i + ")");
    newpartydiv.appendChild(delbutton);
    // Add a newline
    newpartydiv.appendChild(document.createElement("br"));

    //$( "input[name=Color" + i + "]").addClass('color'); /* no longer needed because I'm writing the innerHTML
    jscolor.installByClassName("jscolor");
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
            const num = parseInt(party['Num']);
            requestJSON.parties.push({
                name: party['Name'].replace(',', ''),
                nb_seats: num,
                color: '#' + party['Color'],
                border_size: parseFloat(party['Border']),
                border_color: '#' + party['BColor']
            });

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
            uploadlinkbutton.setAttribute("onClick", 'makeUploadLink("' + data + '", "' + legendstring + '")');
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
    let country, locality, body, year;
    if (country = document.getElementById("country").value) {
        filenameElements.push(country);
    }
    if (locality = document.getElementById("locality").value) {
        filenameElements.push(locality);
    }
    if (body = document.getElementById("body").value) {
        filenameElements.push(body);
    }
    if (year = document.getElementById("year").value) {
        filenameElements.push(year);
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

function makeUploadLink(linkdata, legendtext) {
    const fname = document.getElementById("inputFilename").value.replace(/(.svg)*$/i, ".svg");

    const uploadbutton = document.createElement('button');
    uploadbutton.id = "uploadbutton";
    uploadbutton.className = 'btn btn-primary';
    uploadbutton.setAttribute("onClick", 'postToUpload("' + fname + '", "' + linkdata + '", "' + legendtext + '", ignore=false)');
    uploadbutton.appendChild(document.createTextNode("Click to upload " + fname + " to Wikimedia Commons"));

    const buttonlocation = document.getElementById("postcontainerbutton");
    buttonlocation.innerHTML = "";
    buttonlocation.append(uploadbutton);
}

function postToUpload(fname, linkdata, legendtext, ignore = false) {
    // deactivate the button during processing
    const uploadbutton = document.getElementById("uploadbutton");
    uploadbutton.disabled = true;

    const today = (new Date()).toISOString().split("T")[0];
    $.ajax({
        type: "POST",
        url: "commons_upload",
        data: {
            uri: linkdata,
            filename: fname,
            pagecontent: encodeURIComponent("== {{int:filedesc}} ==\n{{Information\n|description = " + legendtext + "\n|date = " + today + "\n|source = [https://parliamentdiagram.toolforge.org/archinputform Parliament diagram tool]\n|author = [[User:{{subst:REVISIONUSER}}]]\n|permission = {{PD-shape}}\n|other versions =\n}}\n\n[[Category:Election apportionment diagrams]]\n"),
            ignorewarnings: ignore,
        },
    }).done(function (data) {
        let force_removebutton = false;
        let retry_ignore = false;

        // It is possible that the request returns both warnings and a successful result,
        // but assuming it's only in the case of ignorewarnings=true, the warnings are not shown
        if (data.upload && (data.upload.result === "Success")) {
            // Success
            const successdiv = document.createElement('div');
            successdiv.className = 'success';
            successdiv.append("Image successfully uploaded on ");
            const a = successdiv.appendChild(document.createElement("a"));
            try {
                a.href = data.upload.imageinfo.descriptionurl;
            } catch (e) {
                a.href = "https://commons.wikimedia.org/wiki/File:" + fname.replace(" ", "_");
            }
            a.setAttribute("target", "_blank");
            a.append("Commons");
            successdiv.append(".");
            uploadbutton.parentElement.appendChild(successdiv);

            force_removebutton = true;
        } else if (data.error) {
            // WM error case
            // alert(`Error (code "${data.error.code}"): " + ${data.error.info}`);
            const errordiv = document.createElement('div');
            errordiv.className = 'error';
            uploadbutton.parentElement.appendChild(errordiv);

            force_removebutton = true;

            if (data.error.code === "mwoauth-invalid-authorization") {
                $.ajax({
                    type: "POST",
                    url: "logout",
                });
                errordiv.append(
                    "You need to (re-)authorize the tool to upload files on your behalf.",
                    document.createElement("br"),
                );
                const a = errordiv.appendChild(document.createElement("a"));
                a.href = "login";
                a.append("Authorize");
            } else {
                errordiv.append(
                    `Error (code "${data.error.code}"):`,
                    document.createElement("br"),
                    data.error.info,
                    document.createElement("br"),
                    "Please raise an issue on the GitHub Issue tracker if the error seems internal to the Tool.",
                );
            }
        } else if (data.upload && data.upload.warnings) {
            // WM warning case - copied from PHP, not tested in practice
            const warningdiv = document.createElement('div');
            warningdiv.className = 'warning';
            uploadbutton.parentElement.appendChild(warningdiv);

            for (let w in data.upload.warnings) {
                if (w === "badfilename") {
                    warningdiv.append(
                        "The filename is not valid for Wikimedia Commons. Please choose a different one.",
                    );
                    force_removebutton = true;

                    // include other warnings from response.php
                } else if (w.startsWith("exists")) {
                    let a = document.createElement("a");
                    a.href = "https://commons.wikimedia.org/wiki/File:" + fname.replace(" ", "_");
                    a.setAttribute("target", "_blank");
                    a.append(fname);

                    if (w === "exists-normalized") {
                        warningdiv.append(
                            "Warning: a file with a similar name already exists on Commons.",
                            document.createElement("br"),
                        );
                    } else {
                        warningdiv.append(
                            "Warning: the file ",
                            a,
                            " already exists on Commons.",
                            document.createElement("br"),
                        );
                    }
                    if (fname.replace(" ", "_") === "My_Parliament.svg") {
                        warningdiv.append("This is a testing file, which you can try to overwrite ");
                    } else {
                        warningdiv.append("If you have confirmed that you want to overwrite that file, you can try to overwrite it ");
                    }
                    warningdiv.append(
                        "by clicking on the Upload button again.",
                        document.createElement("br"),
                        "Commons usually does not allow to do that, depending on your user rights. In any case, if you abuse this feature, you will be blocked."
                    );
                    retry_ignore = true;
                } else if (w === "duplicate") {
                    warningdiv.append(
                        "Warning: the file you are trying to upload is a duplicate of an existing file on Commons.",
                        document.createElement("br"),
                        "If you are sure that you want to upload it anyway, you can click the Upload button again.",
                    );
                    retry_ignore = true;
                } else {
                    // unrecognized warning
                    warningdiv.append(
                        `Warning: ${w}: ${data.upload.warnings[w]}`,
                    );
                    force_removebutton = true;
                }
            }
        } else {
            // other error case
            const div = document.createElement('div');
            div.className = 'error';
            div.append(
                "Unrecognized API response from server:",
                document.createElement("br"),
                JSON.stringify(data),
            );

            uploadbutton.parentElement.appendChild(div);
            force_removebutton = true;
        }

        if (retry_ignore && !force_removebutton) {
            uploadbutton.disabled = false;
            const onClick = uploadbutton.getAttribute("onClick");
            uploadbutton.setAttribute("onClick", onClick.replace("ignore=false", "ignore=true"));
        } else {
            uploadbutton.remove();
        }
    }).fail(function (xhr, textStatus, errorThrown) {
        // Error, including those thrown by the server
        const errordiv = document.createElement('div');
        errordiv.className = 'error';
        uploadbutton.parentElement.appendChild(errordiv);
        errordiv.innerHTML = xhr.responseText || ("Error: " + textStatus + ", " + errorThrown);
        uploadbutton.remove();
    });
}
