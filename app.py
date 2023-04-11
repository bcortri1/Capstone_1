from flask import Flask, redirect, render_template, jsonify, request, session, g, flash
import requests
from random import sample
from models import db, connect_db, Host, Game, Player, Question, Response
from forms import HostForm, PlayerForm, GameSelection, ResponseForm, PickForm
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from secret import FLASK_KEY, API_KEY
import subprocess
import nltk
import time

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///deceptionary'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = FLASK_KEY or "This is a default key"

CURR_HOST_KEY = "curr_user"
CURR_PLAYER_KEY = "curr_player"

try:
    command = "psql -c 'create database deceptionary'"
    subprocess.call(command, shell=True)
except:
    print(Exception)

connect_db(app)

with app.app_context():
    db.create_all()


# =====================================FUNCTIONS & BEFORE REQUESTS============================================


@app.before_request
def add_host_to_g():
    """If we're logged in, add curr host to Flask global."""
    if CURR_HOST_KEY in session:
        g.host = Host.query.get(session[CURR_HOST_KEY])
    else:
        session.pop(CURR_HOST_KEY, None)
        g.host = None
        
    


@app.before_request
def add_player_to_g():
    """If we're a player add curr player to Flask global."""
    if CURR_PLAYER_KEY in session:
        g.player = Player.query.get(session[CURR_PLAYER_KEY])
    else:
        session.pop(CURR_PLAYER_KEY, None)
        g.player = None


def end_game():
    """Deletes any game hosted by current host"""
    game = Game.query.filter(Game.host_username ==
                             session[CURR_HOST_KEY]).first()
    if game != None:
        db.session.delete(game)
        db.session.commit()
    return "Game Over", 404

def do_login(host):
    """Log in host."""
    session[CURR_HOST_KEY] = host.username


def do_logout():
    """Logout host & deletes any associated games"""
    if CURR_HOST_KEY in session:
        end_game()
        del session[CURR_HOST_KEY]


def create_game():
    """Creates new game in database and returns game object"""
    room_code = Game.create_code()
    game = Game(host_username=g.host.username, room_code=room_code)
    db.session.add(game)
    db.session.commit()
    return game


def get_player_scores():
    """Gets all players and sorts them by score"""
    game = None
    if (g.host != None):
        game = Game.query.filter(Game.host_username == g.host.username).first()
    elif (g.player != None):
        game = g.player.game
    if (game != None):
        players = Player.query.where(Player.game_id == game.id).order_by(Player.score)
        player_ordered = [player.serialize() for player in players]
        return player_ordered
    else:
        return None

# ==================================GAME QUESTION LOGIC==========================================


def get_facts():
    """Returns a list of 2 different facts, increasing later"""
    limit = 1
    api_url = f'https://api.api-ninjas.com/v1/facts?limit={limit}'
    response = requests.get(api_url, headers={'X-Api-Key': API_KEY})
    if response.status_code == requests.codes.ok:
        return response.json()
    else:
        return ("Error:", response.status_code, response.text)


def parse_fact(string):
    """Returns string in list format and a list of grammatical usages IE noun, verb, etc..."""
    word_list = []
    ps_list = []
    for word, ps in nltk.pos_tag(nltk.word_tokenize(string)):
        word_list.append(word)
        ps_list.append(ps)
    return word_list, ps_list


def find_duplicates(word_list):
    """Returns a list of words that have duplicates"""
    word_list = [word.lower() for word in word_list]
    duplicates = [word for word in word_list if word_list.count(word) > 1]
    return duplicates


def create_blank(word_list, gram_list):
    """Should return a sentence with a blank and the word/words that were blanked"""
    first_check = ["JJ", "NN", "NNS", "NNP", "NNPS"]
    second_check = ["NNP", "NNPS", "NN", "NNS"]
    third_check = ["NNP", "NNPS", "NN", "NNS"]
    duplicates = find_duplicates(word_list)

    # Checks for three words
    for i in reversed(range(len(gram_list)-2)):
        if (word_list[i].lower() not in duplicates) and (gram_list[i] in first_check):
            first_word = word_list[i]
            if (gram_list[i+1] in second_check) and (word_list[i+1].lower() not in duplicates):
                second_word = word_list[i+1]
                if (gram_list[i+2] in third_check) and (word_list[i+2].lower() not in duplicates):
                    third_word = word_list[i+2]
                    word_list[i] = "_______"
                    word_list.remove(second_word)
                    word_list.remove(third_word)
                    sentence = " ".join(word_list)
                    answer = f"{first_word} {second_word} {third_word}"
                    return [sentence, answer]

    # Checks for two words
    for i in reversed(range(len(gram_list)-1)):
        if (word_list[i].lower() not in duplicates) and (gram_list[i] in first_check):
            first_word = word_list[i]
            if (gram_list[i+1] in second_check) and (word_list[i+1].lower() not in duplicates):
                second_word = word_list[i+1]
                word_list[i] = "_______"
                word_list.remove(second_word)
                sentence = " ".join(word_list)
                answer = f"{first_word} {second_word}"
                return [sentence, answer]

    # Fallback to single word
    for i in reversed(range(len(gram_list)-1)):
        if (word_list[i].lower() not in duplicates) and (gram_list[i] in first_check):
            first_word = word_list[i]
            word_list[i] = "_______"
            sentence = " ".join(word_list)
            answer = f"{first_word}"
            return [sentence, answer]

    # In the unlikely event that a fact with no noun is found returns a default fact
    return ["The Ancient Romans boiled vinegar and _______ to make an energy drink (*default joke)", "goat poop"]


def create_questions(game_id):
    """Should return a list of questions and their answers"""
    facts = get_facts()
    trivia_list = []
    for fact in facts:
        fact = fact['fact']
        word_list, gram_list = parse_fact(fact)
        question = create_blank(word_list, gram_list)
        question = Question(
            game_id=game_id, text=question[0], answer=question[1])
        db.session.add(question)
        trivia_list.append(question.serialize())
    db.session.commit()
    return trivia_list

# =====================================HOME============================================


@app.route('/', methods=["GET"])
def home():
    """Homepage Redirect Logic"""
    if g.host != None:
        return redirect('/game/select')

    else:
        return redirect('/player/join')


# =====================================HOST============================================
@app.route('/login', methods=["GET", "POST"])
def host_login():
    """Login"""
    form = HostForm()

    if form.validate_on_submit():
        host = Host.authenticate(form.username.data,
                                 form.password.data)

        if host:
            do_login(host)
            flash(f"Hello, {host.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('host/login.html', form=form)


@app.route('/logout', methods=["GET"])
def host_logout():
    """Logout"""
    do_logout()
    return redirect('/login')


@app.route('/register', methods=["GET", "POST"])
def host_register():
    """Handles registration"""
    form = HostForm()
    if g.host == None:
        if form.validate_on_submit():
            try:
                host = Host.register(form.username.data, form.password.data)
                db.session.add(host)
                db.session.commit()
                flash("Success!", "success")
                do_login(host)
                return redirect('/game/select')

            except IntegrityError:

                flash("Username taken", "danger")
                return redirect('/register')
        else:
            return render_template('host/register.html', form=form)

    return redirect('/game/select')


# ====================================GAME======================================================
@app.route('/game/select', methods=["GET", "POST"])
def game_select():
    """Handles game selection"""
    # Currently only has one real game to select
    end_game()
    form = GameSelection()
    if form.validate_on_submit():
        if g.host != None:
            game = create_game()
            questions = create_questions(game.id)
            return redirect(f"/game")
        else:
            flash("Not a valid host", "danger")
            return redirect('/register')

    return render_template('host/select-game.html', form=form)


@app.route('/game', methods=["GET"])
def game_host():
    """Game on hosted machine"""
    # Currently supports 8 players
    player_limit = range(1, 9)

    if g.host != None:
        game = Game.query.filter(Game.host_username == g.host.username).first()
        if (game != None):
            questions = Question.query.filter(
                Question.game_id == game.id).all()
            return render_template('game/deceptionary.html', game=game, player_limit=player_limit, questions=questions)
        else:
            flash("No game with that id!", "danger")
            return redirect('/game/select')
    else:
        flash("Access Denied", "danger")
    return redirect('/register')


@app.route('/game/status', methods=["GET"])
def game_status():
    """Will return the start status"""
    game = None
    if (g.host != None):
        game = Game.query.filter(Game.host_username == g.host.username).first()
    elif (g.player != None):
        game = g.player.game

    if (game != None):
        return jsonify(gameStart=game.started, playerCount=len(game.players), status=200)

    flash("Error", "danger")
    return redirect("/")


@app.route('/game/question', methods=["GET"])
def game_current_question():
    if (g.host != None):
        game = Game.query.filter(Game.host_username == g.host.username).first()
    elif (g.player != None):
        game = g.player.game
    else:
        game = None
        
    if (game != None):
        curr_question = game.get_curr_question()
        if (curr_question == None):
            return "Game Over"

        if (game.started):
            if (curr_question.start_time == 0):
                curr_question.start_time = time.time()

            curr_question.update_stage()
            db.session.commit()
        qId = curr_question.id
        qText = curr_question.text
        qAnswer = curr_question.answer
        qTimer = curr_question.time_elapsed
        qStage = curr_question.stage

        return jsonify(qId=qId, qText=qText, qAnswer=qAnswer, qTimer=qTimer, qStage=qStage, status=200)

    flash("Error", "danger")
    return redirect("/")

# Make test requests here





@app.route('/game/players', methods=["GET"])
def game_host_players_update():
    """To get player names, scores, etc"""
    game = None
    if g.host != None:
        game = Game.query.filter(Game.host_username == g.host.username).first()
    if g.player != None:
        game = g.player.game
    if game != None:
        players = [player.serialize() for player in game.players]
        return players

    return "Not Authorized"


@app.route('/game/responses', methods=["POST"])
def game_get_responses():
    """To get question responses"""
    if g.host != None:
        game = Game.query.filter(Game.host_username == g.host.username).first()
    if g.player != None:
        game = g.player.game

    if game != None:
        qId = request.json.get('qId')
        question = Question.query.get(qId)
        answer = question.answer
        responses = [response.serialize() for response in question.responses]
        responses.append({'id': 'answer', 'text': answer,
                         'player_id': 'answer', 'question_id': question.id})
        responses = sample(responses, len(responses))
        print(responses)
        return jsonify(responses, 200)

    return "Not Authorized"


@app.route('/game/next', methods=["POST"])
def game_next_question():
    """To advance to the next question"""
    if g.host != None:
        game = Game.query.filter(Game.host_username == g.host.username).first()
        question = Question.query.get(request.json.get("qId"))
        if question == game.get_curr_question():
            game.curr_question_num += 1
            db.session.commit()
            return "Next Question"
        else:
            return "Game Over"
    return "Not Authorized"


@app.route('/game/end', methods=["GET", "POST"])
def game_end_send_score():
    """Ends Game"""
    if g.host != None:
        game = Game.query.filter(Game.host_username == g.host.username).first()
        if (game != None):
            players_sorted = get_player_scores()
            end_game()
            return jsonify(players_sorted)

    return "Not Authorized"

# ======================================PLAYER=======================================================


@app.route('/player/join', methods=["GET", "POST"])
def game_join():
    """Handles creation of a player and game joining logic"""
    form = PlayerForm()
    if form.validate_on_submit():
        game = Game.query.filter(Game.room_code == form.room_code.data).first()
        if g.player != None:
            return redirect(f'/player')
        elif (game != None) and (game.player_count < 8):
            num = game.player_count+1
            player = Player(name=form.name.data, game_id=game.id, num=num)
            db.session.add(player)
            db.session.commit()
            session[CURR_PLAYER_KEY] = player.id
            return redirect(f'/player')
        else:
            flash("Unable to join room!", "danger")

    return render_template('player/join.html', form=form)


@app.route('/player', methods=["GET"])
def player_screen():
    """Game player screen"""
    if g.player != None:
        game = g.player.game
        questions = [question.serialize() for question in game.questions]
        question_ids = [question["id"] for question in questions]
        return render_template('player/deceptionary.html', player=g.player, question_ids=question_ids, start=game.started)
    else:
        flash("Unable to join room!", "danger")

    return redirect('/')


@app.route('/player/start', methods=["GET"])
def player_start():
    """Handles 1st players ability to start game"""
    if (g.player != None) and (g.player.num == 1):
        game = g.player.game
        if (g.player.num == 1):
            game.started = True
            db.session.commit()
            #deceptionaryMain(game)
            return jsonify(gameStart=game.started, status=200)
        else:
            return jsonify(gameStart="Error", status=404)

    flash("Error", "danger")
    return redirect("/")

#Redo so it does not need form validation IE POST ONLY
@app.route('/player/response', methods=["POST"])
def player_response_form():
    """Handles responses"""
    if g.player != None:
        game = g.player.game
        question = game.get_curr_question()
        text = request.json.get('text')
        response = Response.query.filter_by(question_id = question.id, player_id = g.player.id).first()
        if (response == None):
            response = Response(text=text, player_id=g.player.id, question_id=question.id)
            db.session.add(response)
            question.update_stage()
            db.session.commit()
            return "Accepted", 202

        return "Resubmitting Not Allowed", 429

    return redirect("/")


@app.route('/player/choice', methods=["POST"])
def player_response_choice():
    """Handles player choices"""
    if (g.player != None):
        choice = request.json.get('choice')
        game = g.player.game
        if (choice == "answer"):
            g.player.score += 1000
        else:
            player = Player.query.get(choice)
            player.score +=500
        db.session.commit()
        return "Accepted", 202
    return redirect("/")

    



