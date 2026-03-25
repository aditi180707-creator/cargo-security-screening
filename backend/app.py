from flask import Flask, render_template, request, redirect, session
import os
import shutil
from ultralytics import YOLO
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

# Load your trained model
model = YOLO(r"C:\Users\HP\OneDrive\Desktop\cargo-ai-detector\dataset\runs\detect\train\weights\best.pt")

UPLOAD_FOLDER = "uploads"
STATIC_OUTPUT = "static/output"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_OUTPUT, exist_ok=True)

# ── In-memory scan history (resets when server restarts) ──
scan_history = []
scan_counter = 1000  # starting scan ID number


# ---------------- LOGIN ----------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == "admin" and password == "123":
            session['user'] = username
            return redirect('/dashboard')
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')


# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')

    # Calculate real stats from scan_history
    total = len(scan_history)
    cleared = sum(1 for s in scan_history if s['risk'] == 'Safe')
    flagged = total - cleared
    last5 = list(reversed(scan_history[-5:]))  # most recent first

    return render_template(
        'dashboard.html',
        total=total,
        cleared=cleared,
        flagged=flagged,
        last5=last5
    )


# ---------------- SCAN PAGE ----------------
@app.route('/scan')
def scan():
    if 'user' not in session:
        return redirect('/')
    return render_template('scan_page.html')


# ---------------- PREDICT ----------------
@app.route('/predict', methods=['POST'])
def predict():
    global scan_counter
    if 'user' not in session:
        return redirect('/')

    file = request.files['image']

    if file:
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        # Run YOLO
        results = model.predict(source=filepath, save=True)
        save_dir = results[0].save_dir

        # Get output image
        files = os.listdir(save_dir)
        image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not image_files:
            return "No output image found"

        result_filename = image_files[0]

        # Copy to static/output
        src_path = os.path.join(save_dir, result_filename)
        dest_path = os.path.join(STATIC_OUTPUT, result_filename)
        shutil.copy(src_path, dest_path)

        # Detection count and class names
        count = len(results[0].boxes)
        names = results[0].names
        detected_classes = []
        detected_names = []
        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            class_name = names[cls_id]
            detected_classes.append(class_name.lower())
            detected_names.append(class_name)

        # Risk logic based on what was detected
        high_threat_items = ['gun', 'knife', 'pistol', 'rifle', 'revolver',
                             'explosive', 'grenade', 'bullet', 'weapon', 'firearm']
        medium_threat_items = ['scissors', 'blade', 'wrench',
                               'plier', 'hammer', 'screwdriver', 'cutter']

        if count == 0:
            risk = "Safe"
        elif any(item in detected_classes for item in high_threat_items):
            risk = "HIGH THREAT"
        elif any(item in detected_classes for item in medium_threat_items):
            risk = "Medium Risk"
        elif count <= 2:
            risk = "Low Risk"
        else:
            risk = "Medium Risk"

        # Build detection string
        if count == 0:
            detections = "No objects detected"
            detected_label = "No threats"
        else:
            detections = f"Objects detected: {count} — {', '.join(detected_names)}"
            detected_label = ', '.join(detected_names)

        # Save to scan history
        scan_counter += 1
        scan_record = {
            'scan_id': f"#SC-{scan_counter}",
            'time': datetime.now().strftime("%H:%M IST"),
            'detected': detected_label,
            'count': count,
            'risk': risk,
            'image': result_filename,
            'detections': detections,
        }
        scan_history.append(scan_record)

        return render_template(
            'result.html',
            result_image=result_filename,
            risk=risk,
            detections=detections
        )

    return "No file uploaded"


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

    if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)