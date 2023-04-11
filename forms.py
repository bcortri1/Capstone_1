from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, RadioField
from wtforms.validators import DataRequired, Length


class HostForm(FlaskForm):
    """Host form, for login and registering"""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    
class PlayerForm(FlaskForm):
    """Form for players to join room"""
    room_code = StringField('Room Code', validators=[DataRequired(), Length(min=4, max=4)])
    name = StringField('Player Name', validators=[DataRequired(), Length(min=1, max=12)])
    
class GameSelection(FlaskForm):
    """Game Selection"""
    
class ResponseForm(FlaskForm):
    """Form for players to submit answers"""
    text = StringField('Submit your lie!')
    
class PickForm(FlaskForm):
    """Form for players to pick answers"""
