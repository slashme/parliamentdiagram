from flask import Flask, redirect, render_template, url_for

app = Flask(__name__)

# redirects
@app.route("/")
@app.route("/index")
@app.route("/index.php")
def root():
    return redirect(url_for("archinputform"))

# legacy redirects
# @app.route("/parliamentinputform")
@app.route("/parliamentinputform.html")
# @app.route("/parlitest")
@app.route("/parlitest.php")
@app.route("/archinputform.php")
def archinputform_redirect():
    return redirect(url_for("archinputform"))

@app.route("/USinputform.html")
@app.route("/USinputform.php")
def usinputform_redirect():
    return redirect(url_for("usinputform"))

@app.route("/westminsterinputform.html")
@app.route("/westminsterinputform.php")
def westminsterinputform_redirect():
    return redirect(url_for("westminsterinputform"))


# main pages
@app.route("/archinputform")
def archinputform():
    return render_template("archinputform.html")

@app.route("/USinputform")
def usinputform():
    return render_template("usinputform.html")

@app.route("/westminsterinputform")
def westminsterinputform():
    return render_template("westminsterinputform.html")


# direct requests
@app.post("/newarch")
@app.post("/newarch.py")
def newarch_generation():
    return ("Not yet implemented", 503)

@app.post("/westminster")
@app.post("/westminster.py")
def westminster_generation():
    return ("Not yet implemented", 503)
