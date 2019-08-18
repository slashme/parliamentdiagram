<?php require('auth.php'); ?>
<?php require('top.php'); ?>
<div class=block id=header>
  <?php require('header.php'); ?>

  <div class="block card">
    <div class="card-body">
      <p class="card-text">It is now possible to get the list of parties from a previous diagram that uses the legend templates that this tool creates. Try it out by putting the name of an existing diagram on Commons into the text box below.</p>
      <p class="card-text">Please submit bug reports and feature requests at the project's <a href="https://github.com/slashme/parliamentdiagram/issues/new">issue tracker</a>.</p>
    </div>
  </div>

  <div class="block card">
    <div class="card-body">
      <p class="card-text">This is a tool to generate arch-shaped parliament diagrams.</p>
      <p class="card-text">To use this tool, fill in the name and support of each party in the legislature, clicking "Add a party" whenever you need to add a new party. Then click "Make my diagram", and a link will appear to your SVG diagram. You can then freely download and use the diagram, but to use the diagram in Wikipedia, you should upload it to Wikimedia Commons. You can now do this directly, by clicking on the green button to create an upload link. Click on the link and follow the instructions: it will upload the file under your username, including the list of parties in the file description. This tool will automatically add your file to the <a href="https://commons.wikimedia.org/wiki/Category:Election_apportionment_diagrams">election apportionment diagrams</a> category, but you should categorise it in more detail after uploading.</p>
      <?php require('response.php'); ?>
    </div>
  </div>

  <div class="block card">
    <div class="card-body">
      <div id="infile">
        <div class="left">Country
          <select id="countrylist">
            <option value="">Select your country</option>
          </select>
        </div>

        <div class="button" id="wdpartylist">Query party list</div>
        <div class="left">Parties
          <select id="partylist">
            <option value="">Select your country first!</option>
          </select>
        </div>

        <div id="infile">
          <div class="left">Get list of parties from:</div><input class="right" type="text" name="infile" id="inputfile" value="File:My_Parliament.svg"><br>
        </div>
        <div class=button id="getfile">Get party list</div>
      </div>
    </div>
  </div>

  <div class="block card">
    <div class="card-body">
      <div id="partylistcontainer">
        <div id="party1">
          <div class="form">
            <div class="form-group row">
              <label class="col-sm-2 col-form-label">Party 1 name</label>
              <div class="col-sm-10">
                <input class="right form-control" type="text" name="Name1" value="Party 1">
              </div>
            </div>
            <div class="form-group row">
              <label class="col-sm-2 col-form-label">Party 1 delegates</label>
              <div class="col-sm-10">
                <input class="right form-control" type="number" name="Number1" value="1">
              </div>
            </div>
            <div class="form-group row">
              <label class="col-sm-2 col-form-label">Party 1 color</label>
              <div class="col-sm-10">
                <input class="right color form-control" type="text" name="Color1" value="AD1FFF" autocomplete="off" style="background-image: none; background-color: rgb(173, 31, 255); color: rgb(255, 255, 255);">
              </div>
            </div>
            <div class="form-group row">
              <label class="col-sm-2 col-form-label">Party 1 border</label>
              <div class="col-sm-10">
                <input class="right form-control" type="checkbox" name="Border1">
              </div>
            </div>
            <div class="form-group row">
              <label class="col-sm-2 col-form-label">Party 1 border color</label>
              <div class="col-sm-10">
                <input class="right color form-control" type="text" name="BColor1" value="000000" autocomplete="off" style="background-image: none; background-color: rgb(0, 0, 0); color: rgb(255, 255, 255);">
              </div>
            </div>

            <input type="submit" class="btn btn-danger deletebutton" value="Delete party 1" onclick="deleteParty(1)">
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="card">
    <div class="card-body">
      <button class="btn btn-info" id="addpartybutton">Add a party</button>
      <button class="btn btn-primary" onclick="CallDiagramScript()">Make my diagram</button>
    </div>
  </div>

  <div class="block">
    <div id="postcontainer">
      <br>
    </div>
  </div>

</div> <!-- Closes div.cotnainer in header.html -->
</div> <!-- Closes div#header -->
<?php require('footer.php'); ?>
