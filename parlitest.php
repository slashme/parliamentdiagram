<?php require('auth.php'); ?>
<?php require('top.php'); ?>
<div id="header">
  <?php require('header.php'); ?>

  <div class="block card">
    <div class="card-body">
      <h2 class="card-text">This is a tool to generate arch-shaped parliament diagrams.</h2>
	<p class="card-text">There are three ways to use this tool: You can get a list of parties from a previous diagram that has been created with this tool. Alternatively, you can do it manually: you can click the "Add a party" button at any time and fill in the name and number of seats in the form that appears, and click "Add a party" whenever you need to add a new party. The third option is to get a list of parties for your country from Wikidata. To do this, select your country from the drop-down box, click "Query party list" and you can select a party from the next drop-down list and click "add party" and fill in the number of seats.</p>
	<p><strong>Note: the colours of the parties generated from Wikidata are not correct! You need to correct them by hand!</strong></p>
	<p>After filling in the parties with any of these methods, click "Make my diagram", and a link will appear to your SVG diagram. You can then freely download and use the diagram, but to use the diagram in Wikipedia, you should upload it to Wikimedia Commons. You can do this directly, by clicking on the green button to create an upload link. Click on the link and follow the instructions: it will upload the file under your username, including the list of parties in the file description. This tool will automatically add your file to the <a href="https://commons.wikimedia.org/wiki/Category:Election_apportionment_diagrams">election apportionment diagrams</a> category, but you should categorise it in more detail after uploading.</p>
<p class="card-text">Please submit bug reports and feature requests at the project's <a href="https://github.com/slashme/parliamentdiagram/issues/new">issue tracker</a>.</p>
      <?php require('response.php'); ?>
    </div>
  </div>

  <div class="block card">
    <div class="card-body">
      <p class="card-text">To get the list of parties from an existing parliament diagram on commons which uses legend templates, put the name of the diagram into the text box below.</p>

      <div id="infile" class="form-group row">
        <label class="col-sm-3 col-form-label">Get list of parties from:</label>
        <div class="col-sm-9">
          <input class="right form-control" type="text" name="infile" id="inputfile" value="File:My_Parliament.svg">
        </div>
      </div>
      <button class="btn btn-primary" id="getfile">Get party list</button>
    </div>
  </div>

  <div class="block card">
    <div class="card-body">
      <p class="card-text">If you want to add a party manually <button class="btn btn-info" id="addpartymanual">Click here</button></p>
    </div>
  </div>

  <div class="block card">
    <div class="card-body">
      <div id="infile">
        <div class="form">
          <div class="form-group row">
            <label class="col-sm-3 col-form-label">Country</label>
            <div class="col-sm-9">
              <select id="countrylist" class="form-control">
                <option value="">Select your country</option>
              </select>
            </div>
          </div>

          <button class="btn btn-primary" id="wdpartylist">Query party list</button>

          <div class="form-group row mt-4">
            <label class="col-sm-3 col-form-label">Parties</label>
            <div class="col-sm-9">
              <select id="partylist" class="form-control">
                <option value="" selected="selected">Select your country first!</option>
              </select>
            </div>
          </div>
          <button class="btn btn-info" id="addpartybutton">Add a party</button>
        </div>
      </div>
    </div>
  </div>

  <div class="block card">
    <div class="card-body">
      <div id="partylistcontainer">
      </div>
    </div>
  </div>

  <div class="card">
    <div class="card-body">
      <button class="btn btn-primary" onclick="CallDiagramScript()">Make my diagram</button>
    </div>
  </div>

  <div class="block card">
    <div class="card-body">
	    <div id="postcontainer">
	      <br>
	    </div>
	    <div id="postcontainerbutton">
	      <br>
	    </div>
    </div>
  </div>

</div> <!-- Closes div.cotnainer in header.html -->
</div> <!-- Closes div#header -->
<?php require('footer.php'); ?>

