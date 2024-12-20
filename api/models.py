from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(180), unique=False, nullable=False)

    lists = db.relationship('List', backref = 'user' , lazy=True, cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref = 'user' , lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.email}>'

    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
            "lists": [list.serialize() for list in self.lists]
        }
#relación de uno a muchos User con List
class List(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tasks = db.relationship('Task', backref='list', lazy=True)
    position = db.Column(db.Integer, nullable=True) 

    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "position": self.position,  
            "tasks": sorted([task.serialize() for task in self.tasks], key=lambda x: x['position'])
        }
#relación de uno a muchos List con Task    
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(100), unique=False, nullable=False)
    position = db.Column(db.Integer, nullable=True) 
    list_id = db.Column(db.Integer, db.ForeignKey('list.id', ondelete='CASCADE'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))

    def __repr__(self):
        return f'<Task {self.text}>'
    
    def serialize(self):
        return {
            "list_id": self.list_id,
            "id": self.id,
            "text": self.text,
            "position": self.position
        }   