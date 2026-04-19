from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
import base64

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///complaints.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    votes = db.Column(db.Integer, default=0)
    author = db.Column(db.String(100))
    anonymous = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Pending')  # Sent, Pending, Rejected, Accepted
    rejection_reason = db.Column(db.Text, nullable=True)
    media = db.relationship('Media', backref='complaint', lazy=True)
    comments = db.relationship('Comment', backref='complaint', lazy=True)

class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    data = db.Column(db.Text, nullable=False)
    media_type = db.Column(db.String(50), nullable=False)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaint.id'), nullable=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100))
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaint.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaint.id'), nullable=False)
    vote_type = db.Column(db.Integer, nullable=False)

with app.app_context():
    db.create_all()

    # Update or create admin user
    old_admin = User.query.filter_by(student_id='SP23cau144').first()
    if old_admin:
        db.session.delete(old_admin)
    new_admin = User.query.filter_by(student_id='Sanju').first()
    if not new_admin:
        new_admin = User(student_id='Sanju', password=generate_password_hash('sanju7900'), is_admin=True)
        db.session.add(new_admin)
    db.session.commit()

    if not Complaint.query.first():
        sample_complaints = [
            Complaint(title="Canteen food quality poor", description="The food in the canteen is not up to standard.", category="Canteen", author="Admin", votes=12, status="Pending"),
            Complaint(title="Hostel water issue", description="No water supply in hostel block A.", category="Hostel", author="Admin", votes=8, status="Accepted"),
            Complaint(title="Library books outdated", description="The library has very old books that are not useful.", category="Library", author="Student123", votes=5, status="Rejected"),
            Complaint(title="Classroom projector not working", description="The projector in room 101 is broken.", category="Classroom", author="Anonymous", votes=10, status="Sent"),
            Complaint(title="WiFi connection slow", description="Internet speed is very slow in the campus.", category="IT", author="Student456", votes=3, status="Pending"),
            Complaint(title="Parking space insufficient", description="Not enough parking spaces for students.", category="Facilities", author="Student789", votes=14, status="Accepted"),
        ]
        for c in sample_complaints:
            db.session.add(c)
        db.session.commit()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    student_id = data.get('student_id')
    password = data.get('password')

    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        # Create user for demo purposes
        user = User(student_id=student_id, password=generate_password_hash(password or 'password'))
        db.session.add(user)
        db.session.commit()

    if user and check_password_hash(user.password, password or 'password'):
        return jsonify({'success': True, 'user': {'id': user.id, 'student_id': user.student_id, 'is_admin': user.is_admin}})
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/api/complaints', methods=['GET'])
def get_complaints():
    category = request.args.get('category', 'All')
    sort = request.args.get('sort', 'new')

    query = Complaint.query
    if category != 'All':
        query = query.filter_by(category=category)

    if sort == 'top':
        query = query.order_by(Complaint.votes.desc())
    elif sort == 'new':
        query = query.order_by(Complaint.created_at.desc())
    elif sort == 'rising':
        query = query.order_by(Complaint.votes.desc(), Complaint.created_at.desc())

    complaints = query.all()
    result = []
    for c in complaints:
        media = [{'filename': m.filename, 'data': m.data, 'type': m.media_type} for m in c.media]
        comments = [{'text': cm.text, 'author': cm.author, 'created_at': cm.created_at.isoformat()} for cm in c.comments]
        result.append({
            'id': c.id,
            'title': c.title,
            'description': c.description,
            'category': c.category,
            'votes': c.votes,
            'author': c.author if not c.anonymous else 'Anonymous',
            'created_at': c.created_at.isoformat(),
            'status': c.status,
            'rejection_reason': c.rejection_reason,
            'media': media,
            'comments': comments
        })
    return jsonify(result)

@app.route('/api/complaints', methods=['POST'])
def add_complaint():
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    category = data.get('category')
    anonymous = data.get('anonymous', False)
    author = data.get('author', 'Anonymous')
    media_data = data.get('media', [])

    complaint = Complaint(title=title, description=description, category=category, anonymous=anonymous, author=author)
    db.session.add(complaint)
    db.session.flush()

    for media in media_data:
        media_obj = Media(filename=media['filename'], data=media['data'], media_type=media['type'], complaint_id=complaint.id)
        db.session.add(media_obj)

    db.session.commit()
    return jsonify({'success': True, 'id': complaint.id})

@app.route('/api/complaints/<int:complaint_id>/vote', methods=['POST'])
def vote_complaint(complaint_id):
    data = request.get_json()
    user_id = data.get('user_id')
    vote_type = data.get('vote_type')

    existing_vote = Vote.query.filter_by(user_id=user_id, complaint_id=complaint_id).first()
    if existing_vote:
        if existing_vote.vote_type == vote_type:
            db.session.delete(existing_vote)
            complaint = Complaint.query.get(complaint_id)
            complaint.votes -= vote_type
        else:
            existing_vote.vote_type = vote_type
            complaint = Complaint.query.get(complaint_id)
            complaint.votes += 2 * vote_type
    else:
        vote = Vote(user_id=user_id, complaint_id=complaint_id, vote_type=vote_type)
        db.session.add(vote)
        complaint = Complaint.query.get(complaint_id)
        complaint.votes += vote_type

    db.session.commit()
    return jsonify({'success': True, 'votes': complaint.votes})

@app.route('/api/complaints/<int:complaint_id>/comment', methods=['POST'])
def add_comment(complaint_id):
    data = request.get_json()
    text = data.get('text')
    author = data.get('author', 'Anonymous')

    comment = Comment(text=text, author=author, complaint_id=complaint_id)
    db.session.add(comment)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/complaints/<int:complaint_id>', methods=['DELETE'])
def delete_complaint(complaint_id):
    complaint = Complaint.query.get(complaint_id)
    if complaint:
        # Delete related media and comments first
        Media.query.filter_by(complaint_id=complaint_id).delete()
        Comment.query.filter_by(complaint_id=complaint_id).delete()
        Vote.query.filter_by(complaint_id=complaint_id).delete()
        db.session.delete(complaint)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 404

@app.route('/api/complaints/<int:complaint_id>/status', methods=['PUT'])
def update_complaint_status(complaint_id):
    data = request.get_json()
    status = data.get('status')
    rejection_reason = data.get('rejection_reason', None)

    complaint = Complaint.query.get(complaint_id)
    if not complaint:
        return jsonify({'success': False, 'message': 'Complaint not found'}), 404

    if status not in ['Sent', 'Pending', 'Rejected', 'Accepted']:
        return jsonify({'success': False, 'message': 'Invalid status'}), 400

    complaint.status = status
    if status == 'Rejected':
        complaint.rejection_reason = rejection_reason
    else:
        complaint.rejection_reason = None

    db.session.commit()
    return jsonify({'success': True, 'status': status, 'rejection_reason': rejection_reason})

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    complaints = Complaint.query.all()
    categories = {}
    statuses = {}
    total_votes = 0
    for c in complaints:
        categories[c.category] = categories.get(c.category, 0) + 1
        statuses[c.status] = statuses.get(c.status, 0) + 1
        total_votes += c.votes

    return jsonify({
        'categories': categories,
        'statuses': statuses,
        'total_complaints': len(complaints),
        'total_votes': total_votes
    })

if __name__ == '__main__':
    app.run(debug=True)