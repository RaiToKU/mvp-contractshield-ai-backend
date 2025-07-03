from app import db

class RiskAnnotation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_index = db.Column(db.Integer, nullable=False)
    end_index = db.Column(db.Integer, nullable=False)
    risk_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)