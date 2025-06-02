from datetime import datetime
from extensions import db

class Report(db.Model):
    __tablename__ = "report"

    id              = db.Column(db.Integer, primary_key=True)
    target_url      = db.Column(db.String(500), index=True, nullable=False)
    scan_results    = db.Column(db.Text, nullable=True)
    severity_score  = db.Column(db.Integer, index=True, nullable=False)
    ai_assessment   = db.Column(db.String(50), index=True, nullable=False)
    gpt_analysis    = db.Column(db.Text, nullable=True)
    bounty_estimate = db.Column(db.Float, nullable=True)
    status          = db.Column(db.String(20), default="Pending", index=True, nullable=False)
    timestamp       = db.Column(db.DateTime, default=datetime.utcnow, index=True, nullable=False)

    def __repr__(self):
        return f"<Report {self.target_url}>"
