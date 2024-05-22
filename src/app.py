import datetime
import hashlib
import os
import tomllib
from typing import Any

from flask import Flask, abort, render_template, request
from parliamentarch import SeatData, write_svg_from_attribution
from parliamentarch.geometry import FillingStrategy

from westminster import treat_inputlist as westminster_treat_inputlist

app = Flask(__name__)

_oauthconfigfilepath = os.path.join(os.path.dirname(__file__), "oauth_config.toml")
if os.path.exists(_oauthconfigfilepath):
    with open(_oauthconfigfilepath, "rb") as _f:
        app.config.update(tomllib.load(_f), oauth_enabled=True)
    del _f
else:
    app.config.update(oauth_enabled=False)
del _oauthconfigfilepath

# redirects
@app.route("/")
@app.route("/index")
@app.route("/index.php")
def root():
    return app.redirect(app.url_for("archinputform"))

# legacy redirects
# @app.route("/parliamentinputform")
@app.route("/parliamentinputform.html")
# @app.route("/parlitest")
@app.route("/parlitest.php")
@app.route("/archinputform.php")
def archinputform_redirect():
    return app.redirect(app.url_for("archinputform"), 301)

@app.route("/USinputform.html")
@app.route("/USinputform.php")
def usinputform_redirect():
    return app.redirect(app.url_for("usinputform"), 301)

@app.route("/westminsterinputform.html")
@app.route("/westminsterinputform.php")
def westminsterinputform_redirect():
    return app.redirect(app.url_for("westminsterinputform"), 301)


# main pages
@app.route("/archinputform")
def archinputform():
    return render_template("archinputform.html")

@app.route("/USinputform")
@app.route("/usinputform")
def usinputform():
    return render_template("usinputform.html")

@app.route("/westminsterinputform")
def westminsterinputform():
    return render_template("westminsterinputform.html")


# direct requests
@app.post("/newarch")
@app.post("/newarch.py")
def newarch_generation():
    nowstrftime, request_hash, inputdata = common_handling("archlog")

    filename = already_existing_file(request_hash)
    if filename is not None:
        app.logger.info("File already exists")
        os.utime("static/"+filename)
    else:
        parties = inputdata.pop("parties", None)
        if parties is None:
            app.logger.error("No list of parties")
            abort(400, "No list of parties provided")

        attrib: dict[SeatData, int] = {}
        for d in parties:
            n = d.pop("nb_seats", 1)
            data = d.pop("name")
            attrib[SeatData(data, **d)] = n
        if inputdata.pop("denser_rows", False):
            filling_strategy = FillingStrategy.EMPTY_INNER
        else:
            filling_strategy = FillingStrategy.DEFAULT
        seat_radius_factor = inputdata.pop("seat_radius_factor", .8)

        filename = f"svgfiles/{nowstrftime}-{request_hash}.svg"
        write_svg_from_attribution("static/"+filename, # TODO: check that the path is correct
            attrib,
            filling_strategy=filling_strategy,
            seat_radius_factor=seat_radius_factor,
            **inputdata)
        # format taken by get_svg_from_attribution:
            # attrib: dict[SeatData, int]
            # **kwargs:
                # min_nrows: int
                # span_angle: float
                # seat_radius_factor: float
                # filling_strategy: FillingStrategy|str
                # canvas_size: float
                # margins: float|tuple[float, float]|tuple[float, float, float, float]
                # write_number_of_seats: bool
                # font_size_factor: float

    # TODO: maybe wrap the simple URL in some kind of response wrapper
    return app.url_for("static", filename=filename)

@app.post("/westminster")
@app.post("/westminster.py")
def westminster_generation():
    nowstrftime, request_hash, inputdata = common_handling("wlog")

    filename = already_existing_file(request_hash)
    if filename is not None:
        app.logger.info("File already exists")
        os.utime("static/"+filename)
    else:
        filename = westminster_treat_inputlist(nowstrftime, request_hash,
            option_wingrows=inputdata.pop("wingrows", None),
            partylist=inputdata.pop("parties", ()),
            **inputdata)

    return app.url_for("static", filename=filename)

def common_handling(logfn: str):
    # data
    data = request.form["data"]

    # inputdata
    inputdata: dict[str, Any] = app.json.loads(data)

    # no input: out
    if not inputdata:
        app.logger.error("No inputlist")
        abort(400, "No data provided")

    # nowstrftime
    nowstrftime = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d-%H-%M-%S-%f")

    # log the nowstrftime and inputlist on local file logfn *and* on the app logger
    app.logger.info("%s %s", nowstrftime, inputdata)
    # with open(logfn, "a") as logfile:
    #     print(nowstrftime, inputdata, file=logfile)

    # requesthash
    request_hash = hashlib.sha256(data.encode()).hexdigest()

    return nowstrftime, request_hash, inputdata

def already_existing_file(request_hash: str) -> str|None:
    for file in os.listdir("static/svgfiles"): # TODO: check that the path is correct
        if request_hash in file:
            return f"svgfiles/{file}"
    return None
