from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Words.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/icons'
app.config['ALLOWED_EXTENSIONS'] = {'svg'}
app.secret_key = 'SECRET_KEY' # not to important tbh isn't ment to be used in prod

db = SQLAlchemy(app)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word_en = db.Column(db.String(50), nullable=False)
    word_translated = db.Column(db.String(50))
    type = db.Column(db.String(50))
    svg_path = db.Column(db.String(100), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Word {self.name}>'

# Create the database
with app.app_context():
    db.create_all()
    # Add test Word (run once then comment out)
    if not Word.query.first():
        test_Word = Word(
            word_en='Fire',
            word_translated='Flame',
            type='noun',
            svg_path='icons/flame.svg'
        )
        db.session.add(test_Word)
        db.session.commit()

@app.route('/')
def index():
    Words = Word.query.order_by(Word.date_created).all()
    return render_template('index.html', Words=Words)


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_word(id):
    word = Word.query.get_or_404(id)

    if request.method == 'POST':
        original_filename = f"{word.word_en}.svg"
        word.word_en = request.form['word_en']
        word.word_translated = request.form['word_translated']
        word.type = request.form['type']

        # Generate new SVG path
        new_filename = f"{word.word_en}.svg"
        word.svg_path = f"icons/{new_filename}"

        # Handle file upload
        if 'svg_file' in request.files:
            file = request.files['svg_file']
            if file.filename != '':
                if file and allowed_file(file.filename):
                    # Ensure upload directory exists
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

                    # Delete old file if name changed
                    if word.word_en != request.form.get('original_word_en'):
                        old_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
                        if os.path.exists(old_path):
                            os.remove(old_path)

                    # Save new file
                    filename = secure_filename(new_filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                else:
                    flash('Only SVG files are allowed')
                    return redirect(request.url)

        try:
            db.session.commit()
            return redirect('/')
        except Exception as e:
            db.session.rollback()
            return f'There was an issue updating the word: {str(e)}'

    # Store original word_en in form for reference
    return render_template('edit.html', word=word, original_word_en=word.word_en)


@app.route('/new', methods=['GET', 'POST'])
def new_word():
    if request.method == 'POST':
        word_en = request.form['word_en']
        word_translated = request.form['word_translated']
        word_type = request.form['type']

        # Handle file upload
        if 'svg_file' not in request.files:
            flash('No file uploaded')
            return redirect(request.url)

        file = request.files['svg_file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            # Generate filename from English word
            filename = f"{secure_filename(word_en)}.svg"
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Save file
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(upload_path)

            # Create new word entry
            new_word = Word(
                word_en=word_en,
                word_translated=word_translated,
                type=word_type,
                svg_path=f"icons/{filename}"
            )

            try:
                db.session.add(new_word)
                db.session.commit()
                return redirect('/')
            except Exception as e:
                db.session.rollback()
                flash(f'Error creating entry: {str(e)}')
                return redirect(request.url)
        else:
            flash('Only SVG files are allowed')
            return redirect(request.url)

    return render_template('new.html')

if __name__ == '__main__':
    app.run(debug=True)


