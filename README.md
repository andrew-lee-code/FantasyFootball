# FantasyFootball
This repo is the home to Andrew's fantasy football research. To create a draft cheat sheet with high powered Andrewlytics, run the DraftSheetBuilder.py program.  
  
## Introduction  
Fantasy Pro's is a good source fantasy football data. They offer draft cheat sheets where players are ranked based on the consensus of over 100 experts. The python program in this repo takes that cheat sheet and builds on it by adding additional useful fields. Those fields are described below.  
  
## The Concept of Starters  
Many of the below stats are calculated based on how a player performs compared to a "starter" at their position. To be considered a starter, a player had to be either a top 10 QB, top 20 RB, top 30 WR, or top 10 TE. Defenses and kickers were excluded since they are heavily matchup-dependent. 
  
## Startability  
A players Startability is a score 0-1. It is the proportion of weeks where a player performed above average for a starter at their position.  
  
## Starter PPG Delta  
This value indicates how many more points a player scores per game compared to an average starter at their position.  
  
## Consistency  
A player's consistency is a score 0-1, indicating how much a player can be trusted to have a minimal number of poor performances. A "poor performance" is defined as scoring 33% points less than the average starter at their position. Consistency = (GamesPlayed - PoorPerformances) / GamesPlayed

## Explosiveness  
A player's explosiveness is a score 0-1, indicating how often a player "goes off". An "explosive performance" is defined as scoring 33% higher than the average starter at their position. Explosiveness - (ExplosiveGames / GamesPlayed)
