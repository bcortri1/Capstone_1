from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import secrets
import time
bcrypt = Bcrypt()
db = SQLAlchemy()


def connect_db(app):
    """Connect to database."""
    db.app = app
    db.init_app(app)


class Host(db.Model):
    """Contains hosts username and password"""

    __tablename__ = 'hosts'

    def __repr__(self):
        return f"Host: {self.username}"

    username = db.Column(db.String(20), primary_key=True)
    password = db.Column(db.String(200))

    @classmethod
    def register(cls, username, pwd):
        hashed = bcrypt.generate_password_hash(pwd)
        hashed_utf8 = hashed.decode("utf8")
        return cls(username=username, password=hashed_utf8)

    @classmethod
    def authenticate(cls, username, pwd):
        currUser = Host.query.filter_by(username=username).first()

        if currUser and bcrypt.check_password_hash(currUser.password, pwd):
            return currUser
        else:
            return False


class Game(db.Model):
    """Contains all game information"""

    __tablename__ = 'games'

    def __repr__(self):
        return f"Game: #{self.id} {self.host_username} {self.room_code}"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    room_code = db.Column(db.String(4), unique=True)
    started = db.Column(db.Boolean, default=False)
    host_username = db.Column(db.String(20), db.ForeignKey("hosts.username", ondelete="cascade"), unique=True)
    curr_question_num = db.Column(db.Integer, default = 0, nullable = True)

    
    players = db.relationship("Player", backref="game", cascade="all, delete")
    questions = db.relationship("Question", backref="game", cascade="all, delete", order_by='asc(Question.id)')

    @property
    def curr_question(self):
        """Return current Question Object"""
        if len(self.questions) > self.curr_question_num:
            return self.questions[self.curr_question_num]
        else:
            return None
        

    @property
    def player_count(self):
        return len(self.players)
    
    
    @classmethod
    def create_code(cls):
        room_code = secrets.token_hex(2).upper()

        check = Game.query.filter(Game.room_code == room_code).first()
        if check == None:
            return room_code
        else:
            return Game.create_code()


class Player(db.Model):
    """Contains player information"""

    __tablename__ = 'players'

    def __repr__(self):
        return f"Player: #{self.id} {self.name}"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(12))
    num = db.Column(db.Integer)
    score = db.Column(db.Integer, default=0, nullable=False)

    game_id = db.Column(db.Integer, db.ForeignKey("games.id"), nullable=False)

    responses = db.relationship(
        "Response", backref="player", cascade="all, delete")

    def serialize(self):
        """Returns a dict representation which we can turn into JSON"""
        return {
            'id': self.id,
            'name': self.name,
            'num': self.num,
            'score': self.score,
            'game_id': self.game_id
        }


class Response(db.Model):
    """Contains all player responses"""

    __tablename__ = 'responses'

    def __repr__(self):
        return f"Question: {self.question_id}, Player: {self.player_id}"

    _text = db.Column(db.String(40))
    player_id = db.Column(db.Integer, db.ForeignKey(
        "players.id"), primary_key=True, nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey(
        "questions.id"), primary_key=True, nullable=False)

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = str(text).upper()

    def serialize(self):
        """Returns a dict representation which we can turn into JSON"""
        return {
            'text': self._text,
            'player_id': self.player_id,
            'question_id': self.question_id
        }


class Question(db.Model):
    """Contains questions for each game"""

    __tablename__ = 'questions'

    def __repr__(self):
        return f"Question: {self.text}, Answer: {self.answer}"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    text = db.Column(db.String(400), nullable=False)
    _answer = db.Column(db.String(100), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"), nullable=False)
    start_time = db.Column(db.Integer, default = 0, nullable = False)
    stage = db.Column(db.String(20), default = "response", nullable=False)
    votes = db.Column(db.Integer, default = 0, nullable=False)
    responses = db.relationship(
        "Response", backref="question", cascade="all, delete")

    @property
    def answer(self):
        return self._answer

    @answer.setter
    def answer(self, answer):
        self._answer = answer.upper()
        
    @property
    def time_elapsed(self):
        return int(time.time()) - self.start_time
    
    @property
    def all_responses_in(self):
        print(len(self.responses))
        return len(self.responses) == self.game.player_count
    
    @property
    def all_votes_in(self):
        return self.votes == self.game.player_count
    
    
    def update_stage(self,stage=None):
        if (stage == None):
            if ((self.time_elapsed >= 90) or (self.stage == "answer")):
                self.stage = "answer"
                
            elif (((self.time_elapsed >= 60) and (self.time_elapsed < 90)) or (self.stage == "voting")):
                if(self.all_votes_in):
                    self.stage = "answer"
                else:
                    self.stage = "voting"
                
            elif (self.time_elapsed < 60):
                if(self.all_responses_in):
                    self.stage = "voting"
                else:
                    self.stage = "response"
                
        else:
            self.stage = stage

    def serialize(self):
        """Returns a dict representation which we can turn into JSON"""
        return {
            'id': self.id,
            'text': self.text,
            'answer': self._answer,
            'game_id': self.game_id,
            'start_time' : self.start_time,
            'stage' : self.stage
        }
        
