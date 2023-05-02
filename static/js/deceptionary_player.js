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
let waitTime = true;
let currQuestion ="";


async function gamePlayerMain() {
    //Will get the current question Info and time
    setTimeout(function(){waitTime = false}, 5000)
    
        playerInterval = setInterval(async function(){
            if (waitTime === false){
                currQuestion = await getCurrQuestion()
                qId = currQuestion.qId;
                qText = currQuestion.qText;
                qStage = currQuestion.qStage; //Options are voting, response, answer
            }

    
            if (gameEnd != true){
                if (qStage === "answer"){
                    votingTime = false;
                    waitTime = false;
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
                        waitTime = true;
                    }
                }
                else if ((qStage === "response")) {
                    //Show response form ONCE
                    if(responseTime != true){
                        $responseContainer.show()
                        responseTime = true;
                        waitTime = true;
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
                window.location.replace("./player/join")
            }
    
        },5000)
    
    }



//Handles start game button request to server
async function startGameRequest(){
    let response = await axios.post(`/player/start`,{});
    if (response.gameStart == true) {
        $startBtn.remove();
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
    waitTime = false;
})

//Response Button Event Handler
$responseBtn.on("click", async function(evt){
    evt.preventDefault();
    let resp = axios.post("/player/response",{
        text: $("#text").val(),
        qId: currQuestion.qId
    })
    $responseContainer.hide()
    waitTime = false
})


//General player poll
function playerGamePoll(){
    generalPlayerPoll = setInterval( async function(){
        let serverResp = await axios.get("/game/status");
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
    let serverResp = await axios.get("/player/question")
    let qId = serverResp.data.qId
    let qText = serverResp.data.qText
    let qAnswer = serverResp.data.qAnswer
    let qTimer = serverResp.data.qTimer
    let qStage = serverResp.data.qStage
    console.log({qId: qId, qText: qText, qAnswer: qAnswer, qTimer: qTimer, qStage: qStage})
    return {qId: qId, qText: qText, qAnswer: qAnswer, qTimer: qTimer, qStage: qStage}

}


// //Polls server until game starts should be used by first player
// function playerStartPoll(){
//         const startPoll = setInterval( async function(){
//             let serverResp = await axios.get(`/game/status`);
//                 started = serverResp.data.gameStart
//                 console.log(started)
//             if (started === true){
//                 gamePlayerMain()
//                 clearInterval(startPoll)
//             }
            
//         }, 3000)
// }




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