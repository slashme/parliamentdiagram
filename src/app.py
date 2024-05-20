import datetime
import hashlib
import os
from typing import Any

from flask import Flask, render_template, request
from parliamentarch import SeatData, write_svg_from_attribution
from parliamentarch.geometry import FillingStrategy

app = Flask(__name__)

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
    return app.redirect(app.url_for("archinputform"))

@app.route("/USinputform.html")
@app.route("/USinputform.php")
def usinputform_redirect():
    return app.redirect(app.url_for("usinputform"))

@app.route("/westminsterinputform.html")
@app.route("/westminsterinputform.php")
def westminsterinputform_redirect():
    return app.redirect(app.url_for("westminsterinputform"))


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
    # TODO: maybe wrap the simple URL in some kind of response wrapper
    nowstrftime = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d-%H-%M-%S-%f")

    data = request.form["data"]
    inputdata: dict[str, Any] = app.json.loads(data)

    app.logger.info("%s %s", nowstrftime, inputdata)

    request_hash = hashlib.sha256(data.encode()).hexdigest()

    if not inputdata:
        app.logger.error("No inputlist")
        return ("No data provided", 400)

    cached_filename = already_existing_file(request_hash)
    if cached_filename is not None:
        return app.url_for("static", filename=cached_filename)

    parties = inputdata.pop("parties", None)
    if parties is None:
        app.logger.error("No list of parties")
        return ("No list of parties provided", 400)

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
    return app.url_for("static", filename=filename)

def already_existing_file(request_hash: str) -> str|None:
    for file in os.listdir("static/svgfiles"): # TODO: check that the path is correct
        if request_hash in file:
            return f"svgfiles/{file}"
    return None

@app.post("/westminster")
@app.post("/westminster.py")
def westminster_generation():
    return ("Not yet implemented", 503)
