In order to run this requires an API key from:
https://api.api-ninjas.com/v1/facts

**Project: Fibbage Game Clone**

1\. Project Description

This is a Fibbage-like game using fact api from API Ninjas (https://api-ninjas.com/). Future goals are to create other trivia and party games that multiple groups of players can enjoy in-person or online.

2\. Gameplay maturity rating

 Current game is based purely off the api from https://api.api-ninjas.com/v1/facts , I take no responsibilty for a facts generated by the API.

3\. Project Requirements.

 In order to run this requires a free API key from: https://api.api-ninjas.com
 Python and packages found in the requirements.txt

4\. Simplified database schema

 Hosts(username [PK], password[hashed], game[FK])

 Players(id[PK], name[unique], score)

 Games(id[PK], players[FK], room code[unique])

5\. User Flow

 User Flow Diagram TBD.

 User => Registers to become Host 

 Host => Start Game

 Host => End Game Session

 Player => Join Game

 Player => Submit Answer

 Player => Vote on Answer


6\. Unique Features not provided by the API

Trivia dynamically has nouns removed (to be improved upon) and blanks added in their stead.

Scoring, is handled solely host-side


**Future Ideas**

Adding additional games (Drawful for example) or game variants. (Can be added in Capstone 2)

An ability for the host to have custom facts or a trivia mode.

Adjustable timers (Could be implemented via a settings screen)

Add a Like System (could be added after voting stage)

Text to speech to read prompts (implementation already coded)

Tutorial Section (Can be implemented by adding a stage after the start poll but before main game)

Add anti-repeat logic to prevent multiple games from the host having repeated questions. (current implementation cannot support this as the game is deleted after completion)
