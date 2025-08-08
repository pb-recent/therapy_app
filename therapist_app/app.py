
from flask import Flask, render_template, request, redirect, url_for, send_file
import csv
from io import StringIO
import datetime

app = Flask(__name__)

# Simple in-memory data storage
patients = []
sessions = []
patient_id_counter = 1
session_id_counter = 1

@app.route('/')
def index():
    return render_template('index.html', patients=patients, sessions=sessions)

@app.route('/add_patient', methods=['GET', 'POST'])
def add_patient():
    global patient_id_counter
    if request.method == 'POST':
        name = request.form['name']
        dob_str = request.form.get('dob')
        gender = request.form.get('gender')
        contact = request.form.get('contact')
        initial_note = request.form.get('initial_note')
        referred_by = request.form.get('referred_by')

        if not name:
            return "Patient name is mandatory.", 400

        dob = datetime.datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None

        new_patient = {
            'id': patient_id_counter,
            'name': name,
            'dob': dob,
            'gender': gender,
            'contact': contact,
            'initial_note': initial_note,
            'referred_by': referred_by,
            'last_session_date': None
        }
        patients.append(new_patient)
        patient_id_counter += 1
        return redirect(url_for('index'))
    return render_template('add_patient.html')

@app.route('/add_session/<int:patient_id>', methods=['GET', 'POST'])
def add_session(patient_id):
    global session_id_counter
    patient = next((p for p in patients if p['id'] == patient_id), None)
    if not patient:
        return "Patient not found.", 404

    if request.method == 'POST':
        primary_diagnosis = request.form['primary_diagnosis']
        secondary_diagnosis = request.form.get('secondary_diagnosis')
        tertiary_diagnosis = request.form.get('tertiary_diagnosis')
        assessment_done = request.form.get('assessment_done')
        therapy_given = request.form.get('therapy_given')
        progress_note = request.form.get('progress_note')

        if not primary_diagnosis:
            return "Primary diagnosis is mandatory.", 400

        new_session = {
            'id': session_id_counter,
            'patient_id': patient_id,
            'primary_diagnosis': primary_diagnosis,
            'secondary_diagnosis': secondary_diagnosis,
            'tertiary_diagnosis': tertiary_diagnosis,
            'assessment_done': assessment_done,
            'therapy_given': therapy_given,
            'progress_note': progress_note,
            'date': datetime.datetime.now().date()
        }
        sessions.append(new_session)
        session_id_counter += 1

        patient['last_session_date'] = new_session['date']
        return redirect(url_for('index'))
    return render_template('add_session.html', patient=patient)

def calculate_age(dob, today):
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

@app.route('/export_excel')
def export_excel():
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Patient ID', 'Name', 'DOB', 'Gender', 'Contact', 'Initial Note', 'Referred By', 'Last Session Date', 'Age at Last Session', 'Last Session Primary Diagnosis'])

    today = datetime.date.today()
    for p in patients:
        age_at_last_session = None
        last_session_primary_diagnosis = None

        if p['last_session_date'] and p['dob']:
            age_at_last_session = calculate_age(p['dob'], p['last_session_date'])

        last_session = next((s for s in sessions if s['patient_id'] == p['id'] and s['date'] == p['last_session_date']), None)
        if last_session:
            last_session_primary_diagnosis = last_session['primary_diagnosis']

        writer.writerow([
            p['id'], p['name'], p['dob'], p['gender'], p['contact'], p['initial_note'],
            p['referred_by'], p['last_session_date'], age_at_last_session, last_session_primary_diagnosis
        ])

    output.seek(0)
    return send_file(StringIO(output.getvalue().encode('utf-8')),
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name='patient_report.csv')

if __name__ == '__main__':
    app.run(debug=True)
