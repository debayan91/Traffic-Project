from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def semantic():
    return render_template('semantic_css.html')