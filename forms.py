from flask_wtf import FlaskForm
from wtforms import SubmitField

class ScanForm(FlaskForm):
    submit = SubmitField('🔍 Run New Scan')