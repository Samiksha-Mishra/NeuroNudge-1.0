from datetime import datetime

from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
import os
from scripts.inference import predict_image
from firebase_admin import firestore
import difflib
from textblob import TextBlob
import time
import pickle
import textstat
from textblob import TextBlob
import language_tool_python
import spacy

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

cred = credentials.Certificate(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
firebase_admin.initialize_app(cred)

# Initialize Firestore client
db = firestore.client()

@app.route("/auth", methods=["POST"])
def authenticate():
    id_token = request.json.get("idToken")
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        session['user'] = {
            'uid': decoded_token['uid'],
            'email': decoded_token.get('email'),
            'name': decoded_token.get('name')
        }
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 401

@app.route("/")
def index():
    return redirect(url_for('home'))

@app.route("/home")
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template("home.html", user=session['user'])

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")


@app.route("/neurocheck")
def neurocheck():
    return render_template("neurocheck.html")

@app.route("/aboutus")
def aboutus():
    return render_template("aboutus.html")

@app.route('/scribble')
def scribble_scan():
    if not session.get("user"):  # Adjust based on your login session key
        return redirect(url_for('login'))
    return render_template("handwritting.html")

@app.route('/talktrace')
def talk_trace():
    if not session.get("user"):
        return redirect(url_for('login'))
    return render_template("talk_trace.html")


@app.route("/reading_analyzer")
def pronunciation_feedback():
    if not session.get("user"):
        return redirect(url_for("login"))
    return render_template("pronunciation_feedback.html")
@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    UPLOAD_FOLDER = 'uploads'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    try:
        prediction, confidence = predict_image(filepath)
        return jsonify({
            'prediction': prediction,
            'confidence': f"{confidence} %"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/gamified')
def gamified_learning():
    if not session.get("user"):
        return redirect(url_for("login"))
    return render_template("gamified_learning.html")


@app.route('/soundquiz')
def sound_quiz():
    if not session.get("user"):
        return redirect(url_for("login"))
    return render_template("sound_quiz_randomized.html")




@app.route('/vr')
def vr_scene():
    if not session.get("user"):
        return redirect(url_for("login"))
    return render_template("vr.html")

@app.route('/experthelp')
def expert_help():
    if not session.get("user"):
        return redirect(url_for('login'))
    return render_template("expert_help.html")

@app.route('/comingsoon')
def coming_soon():
    return render_template("coming_soon.html")

@app.route('/progress')
def progress_dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    uid = session['user']['uid']
    doc = db.collection('users').document(uid).get()
    data = doc.to_dict() if doc.exists else {}


    return render_template("progress_dashboard.html",  # <-- updated HTML file
                           time_tracking=data.get('time_tracking', {}),
                           scores=data.get('scores', {}),
                           predictions=data.get('predictions', []),
                           progress=data.get('progress', {}),
                           progress_data=data)


@app.route('/save_progress', methods=['POST'])
def save_progress():
    if 'user' not in session:
        return jsonify({'status': 'unauthorized'}), 401

    uid = session['user']['uid']
    activity = request.json.get('activity')

    try:
        db.collection('users').document(uid).set({
            'progress': { activity: True }
        }, merge=True)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/log_result', methods=['POST'])
def log_result():
    if 'user' not in session:
        return jsonify({'status': 'unauthorized'}), 401

    uid = session['user']['uid']
    data = request.json
    activity = data.get('activity')
    score = data.get('score', 0)
    duration = data.get('duration', 0)

    try:
        db.collection('users').document(uid).set({
            f'scores.{activity}': score,
            f'time_tracking.{activity}': firestore.Increment(duration),
            f'progress.{activity}': True
        }, merge=True)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500



def store_prediction(uid, label, confidence):
    try:
        user_ref = db.collection('users').document(uid)
        doc = user_ref.get()
        existing = doc.to_dict().get('predictions', []) if doc.exists else []

        existing.append({
            'date': datetime.utcnow().strftime('%Y-%m-%d'),
            'label': label,
            'confidence': confidence
        })

        user_ref.set({'predictions': existing}, merge=True)
    except Exception as e:
        print("Prediction logging failed:", e)




@app.route('/compare_text', methods=['POST'])
def compare_text():
    original = request.json.get('original')
    spoken = request.json.get('spoken')

    original_words = original.lower().split()
    spoken_words = spoken.lower().split()

    matcher = difflib.SequenceMatcher(None, original_words, spoken_words)
    missing, extra = [], []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'delete':
            missing.extend(original_words[i1:i2])
        elif tag == 'insert':
            extra.extend(spoken_words[j1:j2])
        elif tag == 'replace':
            missing.extend(original_words[i1:i2])
            extra.extend(spoken_words[j1:j2])

    correct = len(original_words) - len(missing)
    accuracy = round(correct / len(original_words) * 100, 2)

    sentiment = TextBlob(spoken).sentiment.polarity
    mood = "positive" if sentiment > 0.1 else "negative" if sentiment < -0.1 else "neutral"

    return jsonify({
        "original": original,
        "spoken": spoken,
        "missing": missing,
        "extra": extra,
        "accuracy": accuracy,
        "sentiment": mood
    })




def calculate_wpm(start_time, end_time, num_words):
    elapsed_minutes = (end_time - start_time) / 60
    return round(num_words / elapsed_minutes, 2) if elapsed_minutes > 0 else 0

def get_reading_feedback(original, spoken, start_time, end_time):
    original_words = original.lower().split()
    spoken_words = spoken.lower().split()

    matcher = difflib.SequenceMatcher(None, original_words, spoken_words)
    missing, extra = [], []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'delete':
            missing.extend(original_words[i1:i2])
        elif tag == 'insert':
            extra.extend(spoken_words[j1:j2])
        elif tag == 'replace':
            missing.extend(original_words[i1:i2])
            extra.extend(spoken_words[j1:j2])

    correct = len(original_words) - len(missing)
    accuracy = round(correct / len(original_words) * 100, 2) if original_words else 0

    sentiment_score = TextBlob(spoken).sentiment.polarity
    mood = "positive" if sentiment_score > 0.1 else "negative" if sentiment_score < -0.1 else "neutral"

    wpm = calculate_wpm(start_time, end_time, len(spoken_words))

    return {
        "original": original,
        "spoken": spoken,
        "missing": missing,
        "extra": extra,
        "accuracy": accuracy,
        "wpm": wpm,
        "sentiment": mood
    }

@app.route('/reading_feedback', methods=['POST'])
def reading_feedback():
    data = request.json
    original = data.get('original')
    spoken = data.get('spoken')
    start_time = data.get('start_time')
    end_time = data.get('end_time')

    feedback = get_reading_feedback(original, spoken, start_time, end_time)
    return jsonify(feedback)

@app.route("/get_content")
def get_content():
    level = request.args.get("level", "easy")

    samples = {
        "easy": [
            "The sun is yellow",
            "I see a red ball",
            "Tom has a blue hat",
            "The dog is big",
            "Mom is baking a cake",
            "I like ice cream",
            "Dad is reading a book",
            "It is a hot day",
            "I can jump high",
            "We play in the park"
        ],
        "medium": [
            "Reading books helps you learn new words",
            "The boy is riding his red bicycle to school",
            "Jenny drew a big rainbow in her notebook",
            "Birds fly high in the sky on windy days",
            "The baby laughed when she saw the puppy",
            "He opened the box and found a toy robot",
            "They planted flowers in the garden last week",
            "I packed my lunch and water bottle for the trip",
            "She wore her favorite dress to the party",
            "We went to the zoo to see a giraffe"
        ],
        "hard": [
            "Although she was nervous, Mia spoke clearly on stage",
            "Understanding long words takes time and practice",
            "The astronaut floated in space during the mission",
            "Each season has its own special weather and colors",
            "Phonics and practice make strong readers",
            "He observed the butterfly's wings under the microscope",
            "When reading aloud, focus on every word you see",
            "Some children learn better with music and movement",
            "Curiosity helps kids ask more questions and explore",
            "The volcano erupted and covered the land with ash"
        ]
    }

    import random
    sentence = random.choice(samples.get(level, samples["easy"]))
    return jsonify({"sentence": sentence})


# Load model + NLP tools
smart_model = pickle.load(open("smart_predictor_RETRAINED_FIXED.pkl", "rb"))
language_tool = language_tool_python.LanguageTool('en-US')
nlp = spacy.load("en_core_web_sm")

@app.route('/talktrace_predict', methods=['POST'])
def talktrace_predict():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid input'}), 400

    reversals = int(data.get("reversals", 0))
    pauses = int(data.get("pauses", 0))
    shifts = int(data.get("shifts", 0))
    transcript = data.get("transcript", "")

    blob = TextBlob(transcript)
    word_count = len(blob.words)
    sentence_count = len(blob.sentences)
    filler_words = sum(transcript.lower().count(w) for w in ["um", "uh", "like"])
    readability = textstat.flesch_reading_ease(transcript)
    grammar_errors = len(language_tool.check(transcript))
    repetitions = sum(transcript.lower().split().count(w) > 1 for w in set(transcript.lower().split()))

    doc = nlp(transcript)
    pronouns = [0, 0, 0]  # I, you, they
    for token in doc:
        if token.text.lower() == "i":
            pronouns[0] += 1
        elif token.text.lower() == "you":
            pronouns[1] += 1
        elif token.text.lower() == "they":
            pronouns[2] += 1

    features = [[
        reversals, pauses, shifts, word_count, filler_words, sentence_count,
        readability, grammar_errors, repetitions, *pronouns
    ]]

    prediction = smart_model.predict(features)[0]
    confidence = round(max(smart_model.predict_proba(features)[0]) * 100, 2)

    return jsonify({
        "prediction": prediction,
        "confidence": confidence,
        "features": {
            "reversals": reversals,
            "pauses": pauses,
            "shifts": shifts,
            "word_count": word_count,
            "filler_words": filler_words,
            "sentence_count": sentence_count,
            "readability_score": readability,
            "grammar_errors": grammar_errors,
            "repetitions": repetitions,
            "pronoun_I": pronouns[0],
            "pronoun_you": pronouns[1],
            "pronoun_they": pronouns[2]
        }
    })

if __name__ == "__main__":
    app.run(debug=True)
