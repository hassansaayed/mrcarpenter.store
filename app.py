from flask import Flask, request, render_template_string

app = Flask(__name__)

comments = []

@app.route("/")
def home():
    return """
    <h2>Comment Section</h2>
    <form action='/comment' method='POST'>
        <input type='text' name='comment' placeholder='Enter your comment' required>
        <button type='submit'>Submit</button>
    </form>
    <h3>Previous Comments:</h3>
    <ul>
        """ + "".join(f"<li>{c}</li>" for c in comments) + """
    </ul>
    """

@app.route("/comment", methods=["POST"])
def comment():
    user_comment = request.form.get("comment")
    comments.append(user_comment)
    return render_template_string(home())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
