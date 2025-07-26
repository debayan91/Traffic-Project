from flask import (Flask, send_file, url_for, jsonify, render_template)

app = Flask(__name__)

@app.route("/")
def hello_world():
    return render_template('semantic_css.html')


@app.route("/download")
def download():
    path="static\\best.pt"
    return send_file(path, as_attachment=True)

@app.route("/download2")
def download2():
    path="static\\t_lights.py"
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.debug = True
    app.run()