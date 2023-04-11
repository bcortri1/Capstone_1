const $startBtn = $('#btn-start');
const $playerText = $('#player-text');
const $choiceBtn = $('.btn-choice');
const $responseBtn = $('#btn-response');
const $gameContainer = $("#game-container");
const $responseContainer = $("#response-container");
const $choiceContainer = $("#choice-container")
let playerCount = 0;
let gameEnd = false;
let gameStart = false;
let votingTime = false;
let responseTime = false;
let currQuestion ="";


async function gamePlayerMain() {
    //Will get the current question Info and time
        currQuestion = await getCurrQuestion()
        qId = currQuestion.qId;
        qText = currQuestion.qText; //Possible Future Add blurb on player screen
        //qAnswer = currQuestion.qAnswer; //Not useful for players
        //qTimer = currQuestion.qTimer; //Not useful for players
        qStage = currQuestion.qStage; //Options are voting, response, answer

    
        setInterval(async function(){


    
            if (gameEnd != true){
                if (qStage === "answer"){
                    votingTime = false;
                    //Should do nothing until answer time is over
                    //Would be where "like votes" would happen
                }
                else if ((qStage === "voting")){
                    //Show list of other player responses ONCE
                    $responseContainer.hide()
                    if(votingTime != true){
                        appendChoices(qId)
                        votingTime = true;
                        responseTime = false;
                    }
                }
                else if ((qStage === "response")) {
                    //Show response form ONCE
                    if(responseTime != true){
                        $responseContainer.show()
                        responseTime = true
                    }

                }
                else {
                    gameEnd = true;
                }
            }
            else{
                //Show Player Score
                //Show A YOU WIN Logo if player won
                //Show button to go back to HOME SCREEN
                console.log("Game is Over ")
            }
    
        },2000)
    
    }



//Handles start game button request to server
async function startGameRequest(){
    let response = await axios.get(`/player/start`);
    if (response.gameStart == true) {
        $startBtn.remove();
        $playerText.remove();
    }
}

//Start Game Button Event Handler
$startBtn.on("click", async function(evt){
    startGameRequest();
    $startBtn.hide();
})

//Choice Button Event Handler
$choiceContainer.on("click",".btn-choice", async function(evt){
    evt.preventDefault();
    axios.post("/player/choice",{
        choice: $(this).attr('id')
    })
    $choiceContainer.empty()
})

//Response Button Event Handler
$responseBtn.on("click", async function(evt){
    evt.preventDefault();
    axios.post("/player/response",{
        text: $("#text").val()
    })
    $responseContainer.hide()
    currQuestion = await getCurrQuestion()
})


//General player poll
function playerGamePoll(){
    let generalPlayerPoll = setInterval( async function(){
        let serverResp = await axios.get(`/game/status`);
        started = serverResp.data.gameStart
        if(started){
            gamePlayerMain()
            $playerText.remove()
            clearInterval(generalPlayerPoll)
        }

    }, 5000)
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


//Polls server until game starts should be used by first player
function playerStartPoll(){
        const startPoll = setInterval( async function(){
            let serverResp = await axios.get(`/game/status`);
                started = serverResp.data.gameStart
                console.log(started)
            if (started === true){
                gamePlayerMain()
                clearInterval(startPoll)
            }
            
        }, 2000)
}




//Empties game container
function emptyGameContainer(){

}



//Creates and Appends response cards to responseContainer
async function appendChoices(qId){
    let serverResp= await axios.post(`/game/responses`,{
        qId: qId
    })
    choiceList = serverResp.data[0]
    for (let i = 0; i < choiceList.length; i++){
        let choice = choiceList[i]
        console.log(choice)
        $choiceContainer.append(createChoiceCard(choice))
    }
}


//Requires player response data and return a choice card
function createChoiceCard(choice){
    let $choiceCard = $("<div>").attr("id", `${choice.player_id}`).addClass("btn-choice card bg-dark text-white text-center m-3 m-autos")
    let $choiceText = $("<h4>").text(`${choice.text}`)
    $choiceCard.append($choiceText)
    return $choiceCard
}

playerGamePoll()