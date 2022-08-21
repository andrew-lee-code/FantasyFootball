# FantasyFootball

This repo is the home to Andrew's fantasy football research. To create a draft cheat sheet with high powered Andrewlytics, run the DraftSheetBuilder.py program.

## Introduction

Fantasy Pro's is a good source fantasy football data. They offer draft cheat sheets where players are ranked based on the consensus of over 100 experts. The python program in this repo takes that cheat sheet and builds on it by adding additional useful fields. Those fields are described below.

## Usage

Prerequisites: Have Python and venv installed on your machine

1.) Clone this repo and create a Python venv in the same location with the command `python -m venv ./venv`  
2.) Activate venv with `source .venv/bin/activate` on Mac or `<full_path_to_venv>/Scripts/activate` on Windows  
3.) Install the dependencies with `pip install -r requirements.txt`  
4.) Make sure the data in the relevant subdirectory of `InputData` is complete and has the same format as the others.  
5.) Adjust the `CONSTANTS` at the top of `DraftSheetBuilder.py`.  
6.) Run DraftSheetBuilder.py to create a draft sheet in the `./DraftSheets` directory

It is recommended to format the excel sheet with filters and color scales as in this example provided in the `DraftSheets` directory.

On draft day, it is important to understand the limitations of this draft board. There are no tell-all statistics that can tell you the perfect pick and fantasy football will always require a qualitative touch. Plus much of these added analytics are based on a player's performance the previous season and do not take into account changes to the landscape for this season. With this in mind, it is recommended to keep the following caveats in mind:  
 <ul>
<li>Changes in coaches, quarterback, and scheme can have a big impact on an offense. Teams who have had significant changes in these areas should be researched and used to qualify these statistics</li>
<li>Rookies or players who had significant injuries last season will be lacking in statistics from the previous year and thus should be researched separately </li>
<li>Every year there are a few players who were average the previous season but break out in the following season. The analytics will not predict these players and they should also be researched separately. This is crucial and can make or break a season.</li>
</ul>

## The Concept of Starters

Many of the below stats are calculated based on how a player performed compared to a "starter" at their position in the previous season. To be considered a starter, a player had to be either a top 12 QB, top 20 RB, top 30 WR, or top 10 TE. Defenses and kickers were excluded since they are heavily matchup-dependent.

## Startability

A players Startability is a score 0-1. It is the proportion of weeks where a player performed above average for a starter at their position.

## Starter PPG Delta

This value indicates how many more points a player scores per game compared to an average starter at their position.

## Consistency

A player's consistency is a score 0-1, indicating how much a player can be trusted to have a minimal number of poor performances. A "poor performance" is defined as scoring 33% points less than the average starter at their position. Consistency = (GamesPlayed - PoorPerformances) / GamesPlayed

## Explosiveness

A player's explosiveness is a score 0-1, indicating how often a player "goes off". An "explosive performance" is defined as scoring 33% higher than the average starter at their position. Explosiveness = CubeRoot( (ExplosiveGames / GamesPlayed) ) . Note: The cube root is taken because otherwise the distribution is heavily left-skewed
