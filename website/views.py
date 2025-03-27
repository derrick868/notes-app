import os
import json
from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from .models import Note
from . import db

views = Blueprint('views', __name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), "website/static/uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

# Ensure the uploads folder exists at the start of the app
if not os.path.exists(UPLOAD_FOLDER):
    print(f"Creating folder: {UPLOAD_FOLDER}")
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@views.route('/edit-image/<int:note_id>', methods=['POST'])
@login_required
def edit_image(note_id):
    note = Note.query.get_or_404(note_id)

    if note.user_id != current_user.id:
        flash("You don't have permission to edit this image!", category="error")
        return redirect(url_for("views.home"))

    file = request.files.get("image")

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))

        # Update database
        note.image = filename
        db.session.commit()
        flash("Image updated successfully!", category="success")

    return redirect(url_for("views.home"))

@views.route('/update-note', methods=['POST'])
@login_required
def update_note():
    data = request.get_json()
    note_id = data.get('id')
    new_text = data.get('text')

    if not note_id or not new_text:
        return jsonify({'error': 'Missing note ID or text'}), 400

    note = Note.query.get(note_id)

    if not note:
        return jsonify({'error': 'Note not found'}), 404

    if note.user_id != current_user.id:
        return jsonify({'error': "You don't have permission to edit this note"}), 403

    # Update note text
    note.data = new_text
    db.session.commit()

    return jsonify({'message': 'Note updated successfully'}), 200

@views.route('/delete-note', methods=['POST'])
@login_required
def delete_note():
    try:
        data = request.get_json()  # ✅ Ensure JSON is parsed correctly
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400

        note_id = data.get('noteId')  # ✅ Match key in JS fetch()
        if not note_id:
            return jsonify({'error': 'Note ID missing'}), 400

        note = Note.query.get(note_id)
        if not note:
            return jsonify({'error': 'Note not found'}), 404

        if note.user_id != current_user.id:
            return jsonify({'error': "You don't have permission to delete this note"}), 403

        db.session.delete(note)
        db.session.commit()
        
        return jsonify({'message': 'Note deleted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500



@views.route('/', methods=['GET', 'POST']) 
@login_required
def home():
    if request.method == 'POST': 
        note = request.form.get('note')  # Get note text from form
        file = request.files.get("image")  # Get uploaded image file

        if len(note) < 1:
            flash('Note is too short!', category='error') 
        else:
            filename = None
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                
                # Print debug information
                print(f"Checking folder: {UPLOAD_FOLDER}")
                if not os.path.exists(UPLOAD_FOLDER):
                    print("Uploads folder does NOT exist. Creating it now...")
                    os.makedirs(UPLOAD_FOLDER)

                file_path = os.path.join(UPLOAD_FOLDER, filename)
                print(f"Saving file to: {file_path}")  # Debug output
                file.save(file_path)  # Save image

            new_note = Note(data=note, user_id=current_user.id, image=filename)  # Save image filename
            db.session.add(new_note)
            db.session.commit()
            flash('Note added successfully!', category='success')

    return render_template("home.html", user=current_user)



