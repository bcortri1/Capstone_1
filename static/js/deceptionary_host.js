let $gameContainer = $("#game-container");
let $startContainer = $("#start-container")
let $questionContainer = $("#question-container")
let $responseContainer = $("#response-container")
let $gameTimer = $("#game-timer")
let playerCount = 0;
let gameEnd = false;
let gameStart = false;
let votingTime = false;
let responseTime = false;
let answerTime = false;
let gameContinue = null;
let currQuestion ="";



async function gameHostMain() {
//Will get the current question Info and time
    

    setInterval(async function(){
        currQuestion = await getCurrQuestion()
        qId = currQuestion.qId;
        qText = currQuestion.qText;
        qAnswer = currQuestion.qAnswer;
        qTimer = currQuestion.qTimer;
        qStage = currQuestion.qStage;


        if (gameEnd != true){
            if ((qStage === "answer") || (answerTime === true)){
                if (answerTime != true){
                    answerTime = true
                    votingTime = false;

                    setTimeout(function(){
                        $("#answer").attr("style", " border-color: rgb(255,215,0);")
                    },5000)

                    setTimeout( async function(){
                        $(".response").addClass("slide-out-down")
                        $(".question").addClass("slide-out-down")

                        setTimeout(function(){
                            $(".response").remove()
                            $(".question").remove()
                        ,2000})

                        gameContinue = await nextQuestion(qId)
                    }, 10000)

                    
                    if (gameContinue != "Game Over"){
                        answerTime = false
                    }
                    else{
                        gameEnd = true
                    }
                }
            }
            else if ((qStage === "voting") || (votingTime === true)){
                if (votingTime != true){
                    appendResponses($(".question").attr("id"))
                    votingTime = true
                    responseTime = false
                }
                $gameTimer.hide();
            }
            else if ((qStage === "response") || (responseTime === true)) {
                if (responseTime != true){
                    $questionContainer.append(createQuestionCard(qId,qText));
                    $gameTimer.show();
                    responseTime = true
                }
                timerAnimation($("#timer"), Number(qTimer), Number(60));
                    
            }
            else {
                gameEnd = true;
            }
        }
        else{
            endGame()
        }

    },2000)

}


//Ends Game
async function endGame(){
    let serverResp = await axios.get("/game/end")
    showPlayerScore(serverResp)
}


//Returns requests Next Question, if no more questions exist should return Game Over
async function nextQuestion(qId){
    let serverResp = await axios.post("/game/next",{
        qId:qId
    })
    return serverResp.data
}

//Returns an Object with all necessary question Info
async function getCurrQuestion(){
    let serverResp = await axios.get("/game/question")
    qId = serverResp.data.qId
    qText = serverResp.data.qText
    qAnswer = serverResp.data.qAnswer
    qTimer = serverResp.data.qTimer
    qStage = serverResp.data.qStage
    return {qId: qId, qText: qText, qAnswer: qAnswer, qTimer: qTimer, qStage: qStage}

}

//Creates and Appends response cards to responseContainer
async function appendResponses(qId){
    let serverResp= await axios.post(`/game/responses`,{
        qId: qId
    })
    responseList = serverResp.data[0]
    for (let i = 0; i < responseList.length; i++){
        let responses = responseList[i]
        $responseContainer.append(createResponseCard(responses))
    }
}


//Requires player response data and return a response card
function createResponseCard(serverResp){
    let $respCard = $("<div>").attr("id", `${serverResp.id}`).addClass("response card bg-dark text-white text-center m-3 m-autos")
    let $respText = $("<h4>").text(`${serverResp.text}`)
    $respCard.append($respText)
    return $respCard
}





// //Future TTS implementation
// function speakPrompt(string){
//     string = string.replace("_______", "BLANK")
//     speaknow = new SpeechSynthesisUtterance(string);
//     window.speechSynthesis.speak(speaknow); 
// }


//Creates and returns a JQuery Player Card
function createPlayerCard($playerCard){
    let $playerRow1= $("<div>").addClass("row")
    let $playerCol1= $("<div>").addClass("col-5")

    let $playerImage = $("<img>")
                        .attr("id", `${player.id}`)
                        .addClass("card-img")
                        .attr("style","display:inline-block; height:4.9rem; width:4.9rem;")
                        .attr("src", `/static/assets/pictures/${player.num}.png`)
                        .attr("alt", `Player${player.num} Picture`)

    let $playerRow2= $("<div>").addClass("row")
    let $playerCol2= $("<div>").addClass("col-7")

    let $playerText = $("<h4>").text(`${player.name}`)

    let $playerScore = $("<h4>").text(`${player.score}`)

    $playerCol1.append($playerImage)
    $playerCol2.append($playerText).append($playerScore)

    $playerRow1.append($playerCol1)
    $playerRow2.append($playerCol2)


    $playerCard.append($playerRow1).append($playerRow2)

    return $playerCard

}

//Show each player card in an ordered list at the end
function showPlayerScore(serverResp){
    for (let i = 0; i < serverResp.data.length; i++){
        let player = serverResp.data[i]
        if (i == 0){
            let $playerCard = $("<div>")
                            .attr("id", `${player.id}`)
                            .addClass("card text-white text-center m-3 m-autos")
                            .attr("style","background-color:ffd700;")

            $responseContainer.append(createPlayerCard($playerCard))
        }
        else{
            let $playerCard = $("<div>")
                            .attr("id", `${player.id}`)
                            .addClass("card bg-dark text-white text-center m-3 m-autos")

            $responseContainer.append(createPlayerCard($playerCard))
        }
    }
}

//Create and return a question card as a JQuery Object
function createQuestionCard(qId, qText){
    //Add animation

    $questionCard = $("<div>")
                    .attr("id", `${qId}`)
                    .addClass("question card bg-dark text-white m-3 mx-auto")
                    .attr("style", "width: 80%; border-radius: 25px;")
    
    $cardBody = $("<div>")
                .addClass("card-body")

    $cardText = $("<h4>")
                .text(`${qText}`)

    $cardBody.append($cardText)

    $questionCard.append($cardBody)

    return $questionCard
}

//Animate and Delete Question Card
function deleteQuestionCard(){
    //Add animation process
    
    $(".question").remove()
}

//Animates Joining Players
function playerJoined(player){
    $(`#p${player.num}`).text(player.name)
    $(`#p${player.num}-img`).removeClass("shake1 shake2 shake3 shake4 shake5 shake6 shake7 shake8")
    $(`#p${player.num}-img`).addClass("bounce")
}


//Animate Timer, takes time in seconds and $timerObj
function timerAnimation($timerObj, currentTime, targetTime){
    if (currentTime >= targetTime){
        $timerObj.attr("style", "width:0%")
    }
    else {
        tWidth = ((targetTime-currentTime)/targetTime)*100
        $timerObj.attr("style", `width: ${tWidth}%`)
    }
}

//As soon as page fully loads *****PUT AT END OF DOC*****
$(document).ready(async function () {
    let playerJoinPoll = setInterval( async function(){
        let serverResp = await axios.get(`/game/players`)
        serverResp.data.forEach(player => {
            playerJoined(player)
        });

        if ((serverResp.data.length >= 8) || gameStart === true){
            clearInterval(playerJoinPoll)
        }

    }, 2000);

    //Polls every 3 seconds until game starts, then begins the game
    let startGamePoll = setInterval(async function(){
        let serverResp = await axios.get(`/game/status`)
        gameStart = serverResp.data.gameStart
        playerCount = serverResp.data.playerCount

        if (gameStart === true){
            $startContainer.addClass("slide-out-down");
            setTimeout(function(){
                $startContainer.remove();
                gameHostMain()
                clearInterval(startGamePoll)
            },1900)
        }

    }, 3000);

});