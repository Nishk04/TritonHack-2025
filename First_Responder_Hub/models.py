from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Incident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    emergency_type = db.Column(db.String(120))
    address = db.Column(db.String(200))
    condition = db.Column(db.String(200))
    time_of_emergency = db.Column(db.String(100))

    def __repr__(self):
        return f"<Incident {self.id}: {self.emergency_type}, {self.address}>"
