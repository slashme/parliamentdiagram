import datetime
import hashlib
import os
import tomllib
from typing import Any
from urllib.parse import unquote_plus

from flask import Flask, abort, render_template, request, session
import mwoauth
from parliamentarch import SeatData, write_svg_from_attribution
from parliamentarch.geometry import FillingStrategy
from requests import get as requests_get, post as requests_post
from requests_oauthlib import OAuth1

from westminster import treat_inputlist as westminster_treat_inputlist
from template import main as template_main, SeatData as TemplateSeatData

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

@app.route("/templateform")
def templateform():
    return render_template("templateform.html")


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

@app.post("/template")
@app.post("/template.py")
def template_generation():
    nowstrftime, request_hash, inputdata = common_handling("tlog")

    filename = already_existing_file(request_hash)
    if filename is not None:
        app.logger.info("File already exists")
        os.utime("static/"+filename)
    else:
        filename = f"svgfiles/{nowstrftime}-{request_hash}.svg"

        if inputdata.pop("demo", False):
            filling = True
        else:
            # expect the same SeatData format as parliamentarch
            # data, color, border_size, border_color
            # convert it to svg properties
            # title, fill, stroke-width, stroke
            # also manage the seat numbers, from nb_seats to dict value
            filling = {}
            for party in inputdata.pop("partylist"):
                nb_seats = party.pop("nb_seats", 1)
                party["title"] = party.pop("name", None)
                party["desc"] = party.pop("data", None)
                party["fill"] = party.pop("color")
                party["stroke-width"] = party.pop("border_size", 0)
                party["stroke"] = party.pop("border_color", "black")
                filling[TemplateSeatData(**party)] = nb_seats

        template_main("static/svg_templates/"+inputdata.pop("template_id")+"_template.svg", "static/"+filename,
            filling=filling,
        )

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


# oauth
@app.route("/login")
def login():
    if not app.config["oauth_enabled"]:
        abort(501, "OAuth is not enabled on this server")

    # TODO: if already logged in, redirect away?

    consumer_token = mwoauth.ConsumerToken(app.config["CONSUMER_KEY"], app.config["CONSUMER_SECRET"])
    try:
        redirect, request_token = mwoauth.initiate(app.config["OAUTH_MWURI"], consumer_token)
    except Exception:
        app.logger.exception("mwoauth.initiate failed")
        abort(400, "OAuth initiation failed")

    session["request_token"] = request_token._asdict()
    return app.redirect(redirect)

@app.route("/oauth_callback")
def oauth_callback():
    if not app.config["oauth_enabled"]:
        abort(501, "OAuth is not enabled on this server")

    if "request_token" not in session:
        abort(400, "OAuth callback failed. Are cookies disabled?")

    consumer_token = mwoauth.ConsumerToken(app.config["CONSUMER_KEY"], app.config["CONSUMER_SECRET"])

    try:
        access_token = mwoauth.complete(
            app.config["OAUTH_MWURI"],
            consumer_token,
            mwoauth.RequestToken(**session["request_token"]),
            request.query_string)

        identity = mwoauth.identify(app.config["OAUTH_MWURI"], consumer_token, access_token)
    except Exception:
        app.logger.exception("OAuth authentication failed")
        abort(400, "OAuth authentication failed")

    session["access_token"] = access_token._asdict()
    session["username"] = identity["username"]

    # TODO: rethink that redirect
    # probably save an after_oauth_callback route in the session (and check it too)
    # makeUploadLink in arch.js could use that
    return app.redirect(app.url_for("root"))

@app.route("/logout")
@app.post("/logout")
def logout():
    session.clear()
    if request.method == "POST":
        return "Success"
    # TODO: same, the logout link in base.html could use a better redirect
    return app.redirect(app.url_for("root"))

@app.get("/get_username")
def get_username():
    return {"username": session.get("username", "")}

@app.post("/commons_upload")
def commons_upload():
    # parameters that should be included in the request:
        # uri / filetosend
            # prolly make that start with "static/" so that python can open the file
            # or full url enabled with _external=True, if Commons allows copy uploads (but it seems not)
        # filename / new_file_name / commons_file_name
            # the one usually starting with a capital, ending with .svg, handled by the JS up til then
            # the one that will identify the file on Commons
        # pagecontent / desc
            # the description of the file, filled by the JS
        # comment
            # "Direct upload from the ParliamentDiagram tool" - a constant
            # the former one was slightly different, but this one is better
        # ignore / ignorewarnings
            # format to be decided, probably a boolean but to be authorized by a session marker

    if not app.config["oauth_enabled"]:
        abort(501, "OAuth is not enabled on this server")

    if "access_token" not in session:
        abort(401, "Not logged in")

    params = request.form
    try:
        filetosend = params["uri"].lstrip("/\\")
        commons_file_name = params["filename"]
        desc = unquote_plus(params["pagecontent"])
    except KeyError as e:
        app.logger.error("Missing parameter %s", e)
        abort(400, f"Missing parameter {e}")
    comment = "Direct upload from the ParliamentDiagram tool"
    ignorewarnings = params.get("ignorewarnings", "false") # everything coming in is a string

    override_tickets = session.setdefault("override_tickets", {})
    # using a dict because sets aren't serializable in JSON

    if (ignorewarnings != "false") and ((filetosend, commons_file_name) not in override_tickets):
        app.logger.error("Unauthorized use of ignorewarnings")
        abort(403, "Unauthorized use of ignorewarnings")

    absfiletosend = os.path.abspath(filetosend)
    if os.path.dirname(absfiletosend) != os.path.abspath("static/svgfiles"):
        app.logger.error("File not in the correct directory")
        abort(403, "File not at the authorized location")
    if not os.path.exists(absfiletosend):
        app.logger.error("File not found")
        abort(400, "File not found")

    url = "https://commons.wikimedia.org/w/api.php"

    auth = OAuth1(
        app.config["CONSUMER_KEY"],
        client_secret=app.config["CONSUMER_SECRET"],
        resource_owner_key=session["access_token"]["key"],
        resource_owner_secret=session["access_token"]["secret"],
    )

    tokenrequest_data = requests_get(url=url, auth=auth, params=dict(
        action="query",
        meta="tokens",
        format="json",
    )).json()

    crsf_token = tokenrequest_data["query"]["tokens"]["csrftoken"]

    with open(filetosend, "rb") as f:
        uploadrequest_data = requests_post(url=url, auth=auth,
            files=dict(file=(os.path.basename(filetosend), f, "multipart/form-data")),
            data=dict(
                action="upload",
                format="json",

                filename=commons_file_name,
                comment=comment,
                # tags=?,
                text=desc,
                ignorewarnings=ignorewarnings, # to be managed
                token=crsf_token,
            )).json()

    override_tickets.pop((filetosend, commons_file_name), None)

    if uploadrequest_data.get("upload", {}).get("result", None) == "Warning":
        if all((k == "duplicate") or k.startswith("exists") for k in uploadrequest_data["upload"]["warnings"]):
            override_tickets[(filetosend, commons_file_name)] = None

    # The JS possibly makes the decision of what do do,
    # but we make the decision of whether to authorize an override or not

    return uploadrequest_data
