import pandas as pd
import re

from pandas.core.frame import DataFrame


## CONSTANTS
POS_RANK_REGEX = r'([a-z]{1,3})(\d{1,2})'
SOS_REGEX = r'(\d) out of \d stars'
PLAYER_NAME_REGEX = r'(.*.)(\s\([A-Z]{1,3}\))'
WEEKS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17"]
OUTPUT_PATH = "./DraftSheets/2020_DRAFT_SHEET.xlsx"


## HELPER METHODS
def get_starters(previous_year_data:DataFrame):
    """Retrieves starting players from previous year (Top 10 QB's, 20 RB's, 30 WR's, and 10 TE's"""

    qb_starters = previous_year_data[previous_year_data['Position'] == 'QB'].sort_values('Points', ascending=False).head(10)
    rb_starters = previous_year_data[previous_year_data['Position'] == 'RB'].sort_values('Points', ascending=False).head(20)
    wr_starters = previous_year_data[previous_year_data['Position'] == 'WR'].sort_values('Points', ascending=False).head(30)
    te_starters = previous_year_data[previous_year_data['Position'] == 'TE'].sort_values('Points', ascending=False).head(10)
    starters = pd.concat([qb_starters, rb_starters, wr_starters, te_starters], ignore_index=True)
    
    return starters


def get_starter_PPGs(starters_df:DataFrame):
    """Calculates the PPG for a starting player at each position from the previous year"""

    starter_points = {}
    starter_points["QB"] = starters_df[starters_df["Position"] == 'QB']["Points"].median() / 16
    starter_points["RB"] = starters_df[starters_df["Position"] == 'RB']["Points"].median() / 16
    starter_points["WR"] = starters_df[starters_df["Position"] == 'WR']["Points"].median() / 16
    starter_points["TE"] = starters_df[starters_df["Position"] == 'TE']["Points"].median() / 16

    return starter_points


def clean_consensus_ratings(df:DataFrame):
    """Cleans the raw consensus ratings from Fantasy Pros website"""

    # Break positional rankings column into two columns
    df['POSITION'] = df.apply(lambda row: re.match(POS_RANK_REGEX, row.POS, re.IGNORECASE).group(1), axis = 1)
    df['POSITION_RANK'] = df.apply(lambda row: re.match(POS_RANK_REGEX, row.POS, re.IGNORECASE).group(2), axis = 1)

    # Reformat strength of schedule rating
    df['SOS'] = df.apply(lambda row: re.match(SOS_REGEX, row.SOS_SEASON, re.IGNORECASE).group(1) if re.match(SOS_REGEX, row.SOS_SEASON, re.IGNORECASE) else "N/A", axis = 1)
    
    # Drop unecessary columns and reorder
    df.drop(columns=["POS", "SOS_SEASON"], inplace=True)
    df.rename(columns={"PLAYER NAME" : "PLAYER"}, inplace=True)
    df = df[["TIER", "RANK", "POSITION_RANK", "POSITION", "PLAYER", "TEAM", "BYE", "SOS", "ECR VS. ADP"]]

    return df

def add_games_played_stat(data_previous_year:DataFrame, df:DataFrame):
    """Our consensus ratings csv that we read in doesn't have Games Played, so we add it from the previous year's data"""

    # Remove all columns excpet player names and games played
    data_previous_year_stripped = data_previous_year.filter(items=['Player', 'Games'])
    data_previous_year_stripped.rename(columns={"Player" : "PLAYER"}, inplace=True)

    df = pd.merge(df, data_previous_year_stripped, how="left", on="PLAYER")
    df.rename(columns={"Games" : "GAMES_PLAYED"}, inplace=True)
    return df

def combine_weekly_points_files(csv_filenames:list):
    """Reads in csv's containing weekly perfomances for each player and combines them into one dataframe"""

    # Get list of all players that had stats in at least one week during the previous season
    all_players = []
    for csv_filename in csv_filenames:
        temp_df = pd.read_csv(csv_filename)
        players = temp_df["Player"].to_list()
        all_players += players
        all_players = list(set(all_players))

    # Combine dataframes
    weekly_df = pd.DataFrame.from_dict({"Player": all_players})
    week = 1
    for csv_filename in csv_filenames:
        temp_df = pd.read_csv(csv_filename)
        temp_df.rename(columns={"Points" : f"Week{week}"}, inplace=True)
        temp_df.drop(columns=["Rank", "Team", "Position", "Games", "Avg"], inplace=True)
        weekly_df = pd.merge(weekly_df, temp_df, how="left", on="Player")
        week += 1
    
    # Remove null rows and replace N/A's with 0's
    weekly_df.dropna(inplace=True, how="all")
    weekly_df.fillna(0, inplace=True)

    return weekly_df.sort_values("Player")

def get_startability(starter_points:dict, player:str, position:str, weekly_points:DataFrame):
    """Calculates a player's startabiliy. How many weeks out of 16 were they above average for a starter at their position"""
    
    #If player did not have stats from last year then return N/a
    if player not in weekly_points["Player"].to_list():
        return "N/A"

    #If position is kicker or defense then return N/a
    if position not in starter_points.keys():
        return "N/A"

    startable_weeks = 0
    for week in WEEKS:
        if weekly_points.loc[weekly_points["Player"] == player, f"Week{week}"].item() > starter_points[position]:
            startable_weeks += 1
    
    return startable_weeks / 16

def get_starter_PPG_delta(player:str, position:str, starter_points:dict, previous_year_all_data:DataFrame):
    """Get the delta between a player's PPG and a starter's PPG at their position"""

    #If player did not have stats from last year then return N/a
    if player not in previous_year_all_data["Player"].to_list():
        return "N/A"

    #If position is kicker or defense then return N/a
    if position not in starter_points.keys():
        return "N/A"
    
    player_PPG = previous_year_all_data.loc[previous_year_all_data["Player"] == player, "Avg"].item()
    return player_PPG - starter_points[position]


def get_consistency(player:str, position:str, games_played:int, starter_points:dict, weekly_points:DataFrame):
    """Calculates a player's consistency score 0-1"""

    #If player did not have stats from last year then return N/a
    if player not in weekly_points["Player"].to_list():
        return "N/A"

    #If position is kicker or defense then return N/a
    if position not in starter_points.keys():
        return "N/A"
    
    poor_games = 0
    for week in WEEKS:
        points = weekly_points.loc[weekly_points["Player"] == player, f"Week{week}"].item()
        if points < (starter_points[position] - starter_points[position]*0.33):
            poor_games += 1
    
    # don't penalize players for haing "poor games" when they didn't play
    games_not_played = 17 - games_played
    poor_games_adjusted = poor_games - games_not_played

    return (float(games_played) - float(poor_games_adjusted)) / float(games_played)

def get_explosiveness(player:str, position:str, games_played:int, starter_points:dict, weekly_points:DataFrame):
    """Calculate explosiveness scores"""
    
    #If player did not have stats from last year then return N/a
    if player not in weekly_points["Player"].to_list():
        return "N/A"

    #If position is kicker or defense then return N/a
    if position not in starter_points.keys():
        return "N/A"
    
    explosive_games = 0
    for week in WEEKS:
        points = weekly_points.loc[weekly_points["Player"] == player, f"Week{week}"].item()
        if points > (starter_points[position] * 1.33):
            explosive_games += 1

    return (float(explosive_games) / float(games_played))

def add_previous_year_stats(df:DataFrame, qb_stats:DataFrame, rb_stats:DataFrame, wr_stats:DataFrame, te_stats:DataFrame):
    """Adds previous year's stats to dataframe"""

    # Clean the "Player" column to remove team name (ie. "Josh Allen (BUF)" becomes "Josh Allen")
    qb_stats["Player"] = qb_stats.apply(lambda row: re.match(PLAYER_NAME_REGEX, str(row.Player), re.IGNORECASE).group(1) if re.match(PLAYER_NAME_REGEX, str(row.Player), re.IGNORECASE) else "N/A", axis=1)
    rb_stats["Player"] = rb_stats.apply(lambda row: re.match(PLAYER_NAME_REGEX, str(row.Player), re.IGNORECASE).group(1) if re.match(PLAYER_NAME_REGEX, str(row.Player), re.IGNORECASE) else "N/A", axis=1)
    wr_stats["Player"] = wr_stats.apply(lambda row: re.match(PLAYER_NAME_REGEX, str(row.Player), re.IGNORECASE).group(1) if re.match(PLAYER_NAME_REGEX, str(row.Player), re.IGNORECASE) else "N/A", axis=1)
    te_stats["Player"] = te_stats.apply(lambda row: re.match(PLAYER_NAME_REGEX, str(row.Player), re.IGNORECASE).group(1) if re.match(PLAYER_NAME_REGEX, str(row.Player), re.IGNORECASE) else "N/A", axis=1)

    for index, row in df.iterrows():
        # Skip player if they don't have stats from last year
        if row.PLAYER not in pd.concat([qb_stats["Player"], rb_stats["Player"], wr_stats["Player"], te_stats["Player"]]).to_list():
            df.loc[index, "PPG"] = "-"
            df.loc[index, "Passing YPG"] = "-"
            df.loc[index, "Passing TD"] = "-"
            df.loc[index, "Rushes PG"] = "-"
            df.loc[index, "Rushing YPG"] = "-"
            df.loc[index, "Rushing TD"] = "-"
        else:
            if row.POSITION == "QB":
                games = qb_stats.loc[qb_stats["Player"] == row.PLAYER, "G"].item() 
                df.loc[index, "PPG"] = qb_stats.loc[qb_stats["Player"] == row.PLAYER, "FPTS/G"].item() 
                df.loc[index, "Passing YPG"] = float(qb_stats.loc[qb_stats["Player"] == row.PLAYER, "P_YDS"].item().replace(',','')) / games if games > 0 else 0 
                df.loc[index, "Passing TD"] = qb_stats.loc[qb_stats["Player"] == row.PLAYER, "PTD"].item() 
                df.loc[index, "Rushes PG"] = float(qb_stats.loc[qb_stats["Player"] == row.PLAYER, "R_ATT"].item()) / games if games > 0 else 0 
                df.loc[index, "Rushing YPG"] = float(qb_stats.loc[qb_stats["Player"] == row.PLAYER, "R_YDS"].item().replace(',','')) / games if games > 0 else 0 
                df.loc[index, "Rushing TD"] = qb_stats.loc[qb_stats["Player"] == row.PLAYER, "R_TD"].item() 
                df.loc[index, "Targets PG"] = "-"
                df.loc[index, "Receiving YPG"] = "-"
                df.loc[index, "Receiving TD"] = "-"
            elif row.POSITION == "RB":
                games = rb_stats.loc[rb_stats["Player"] == row.PLAYER, "G"].item() 
                df.loc[index, "PPG"] = rb_stats.loc[rb_stats["Player"] == row.PLAYER, "FPTS/G"].item() 
                df.loc[index, "Passing YPG"] = "-"
                df.loc[index, "Passing TD"] = "-"
                df.loc[index, "Rushes PG"] = float(rb_stats.loc[rb_stats["Player"] == row.PLAYER, "RU_ATT"].item()) / games if games > 0 else 0 
                df.loc[index, "Rushing YPG"] = float(rb_stats.loc[rb_stats["Player"] == row.PLAYER, "RU_YDS"].item().replace(',','')) / games if games > 0 else 0 
                df.loc[index, "Rushing TD"] = rb_stats.loc[rb_stats["Player"] == row.PLAYER, "RU_TD"].item() 
                df.loc[index, "Targets PG"] = float(rb_stats.loc[rb_stats["Player"] == row.PLAYER, "TGT"].item()) / games if games > 0 else 0 
                df.loc[index, "Receiving YPG"] = float(rb_stats.loc[rb_stats["Player"] == row.PLAYER, "RE_YDS"].item()) / games if games > 0 else 0
                df.loc[index, "Receiving TD"] = rb_stats.loc[rb_stats["Player"] == row.PLAYER, "RE_TD"].item() 
            elif row.POSITION == "WR":
                games = wr_stats.loc[wr_stats["Player"] == row.PLAYER, "G"].item() 
                df.loc[index, "PPG"] = wr_stats.loc[wr_stats["Player"] == row.PLAYER, "FPTS/G"].item() 
                df.loc[index, "Passing YPG"] = "-"
                df.loc[index, "Passing TD"] = "-"
                df.loc[index, "Rushes PG"] = float(wr_stats.loc[wr_stats["Player"] == row.PLAYER, "RU_ATT"].item()) / games if games > 0 else 0
                df.loc[index, "Rushing YPG"] = float(wr_stats.loc[wr_stats["Player"] == row.PLAYER, "RU_YDS"].item()) / games if games > 0 else 0
                df.loc[index, "Rushing TD"] = wr_stats.loc[wr_stats["Player"] == row.PLAYER, "RU_TD"].item()
                df.loc[index, "Targets PG"] = float(wr_stats.loc[wr_stats["Player"] == row.PLAYER, "TGT"].item()) / games if games > 0 else 0 
                df.loc[index, "Receiving YPG"] = float(wr_stats.loc[wr_stats["Player"] == row.PLAYER, "RE_YDS"].item().replace(',','')) / games if games > 0 else 0
                df.loc[index, "Receiving TD"] = wr_stats.loc[wr_stats["Player"] == row.PLAYER, "RE_TD"].item() 
            elif row.POSITION == "TE":
                games = te_stats.loc[te_stats["Player"] == row.PLAYER, "G"].item() 
                df.loc[index, "PPG"] = te_stats.loc[te_stats["Player"] == row.PLAYER, "FPTS/G"].item() 
                df.loc[index, "Passing YPG"] = "-"
                df.loc[index, "Passing TD"] = "-"
                df.loc[index, "Rushes PG"] = float(te_stats.loc[te_stats["Player"] == row.PLAYER, "RU_ATT"].item()) / games if games > 0 else 0
                df.loc[index, "Rushing YPG"] = float(te_stats.loc[te_stats["Player"] == row.PLAYER, "RU_YDS"].item()) / games if games > 0 else 0
                df.loc[index, "Rushing TD"] = te_stats.loc[te_stats["Player"] == row.PLAYER, "RU_TD"].item()
                df.loc[index, "Targets PG"] = float(te_stats.loc[te_stats["Player"] == row.PLAYER, "TGT"].item()) / games if games > 0 else 0 
                df.loc[index, "Receiving YPG"] = float(te_stats.loc[te_stats["Player"] == row.PLAYER, "RE_YDS"].item().replace(',','')) / games if games > 0 else 0
                df.loc[index, "Receiving TD"] = te_stats.loc[te_stats["Player"] == row.PLAYER, "RE_TD"].item()
    return df 


def output_draft_sheet(andrewlytics:DataFrame, weekly_df:DataFrame):
    """Compiles Andrewlytics and other player stats into final excel sheet"""

    read_me = pd.DataFrame(columns=["COLUMN_NAME", "EXPLANATION"])
    read_me = read_me.append({"COLUMN_NAME" : "RANK", "EXPLANATION": "Consensus ranking from 118 experts"} ,ignore_index=True)
    read_me = read_me.append({"COLUMN_NAME" : "TIER", "EXPLANATION": "Consensus tier from 118 experts"} ,ignore_index=True)
    read_me = read_me.append({"COLUMN_NAME" : "SOS", "EXPLANATION": "Strength of schedule rated 1-5 (5 is most favorable)"} ,ignore_index=True)
    read_me = read_me.append({"COLUMN_NAME" : "ECR VS. ADP", "EXPLANATION": "ADP minus Consensus Ranking. More positive number means player is being drafted later than they should be according to their ECR"} ,ignore_index=True)
    read_me = read_me.append({"COLUMN_NAME" : "Startability", "EXPLANATION": "Proportion of games where they were better than the average starter"} ,ignore_index=True)
    read_me = read_me.append({"COLUMN_NAME" : "Starter_PPG_Delta", "EXPLANATION": "Player PPG minus average starter PPG. Higher number indicates their PPG is that much higher than the average starter"} ,ignore_index=True)
    read_me = read_me.append({"COLUMN_NAME" : "Consistency", "EXPLANATION": "Rating 0-1 to estimate how consistently a player performed the previous year. A high score means they had fewer poor performances"} ,ignore_index=True)
    read_me = read_me.append({"COLUMN_NAME" : "Explosiveness", "EXPLANATION": "Rating 0-1 to estimate how explosively a player performed the previous year. A high score means they had more explosive performances"} ,ignore_index=True)

    with pd.ExcelWriter(OUTPUT_PATH) as writer:  
        andrewlytics.to_excel(writer, sheet_name='DRAFT_BOARD', index=False)
        weekly_df.to_excel(writer, sheet_name='2020_WEEKLY', index=False)
        read_me.to_excel(writer, sheet_name='READ_ME', index=False)


## MAIN
if __name__ == "__main__":
    # Get Starters from previous year
    data_2020 = pd.read_csv("./Data/2020_total.csv")
    starters = get_starters(data_2020)

    # Get starter points per game
    starter_points = get_starter_PPGs(starters)

    # Get weekly points dataframe
    weekly_filenames = [f"./Data/2020_Week{week}.csv" for week in WEEKS]
    weekly_points_df = combine_weekly_points_files(weekly_filenames)

    # Clean consensus rankings df
    base_df = pd.read_csv("./Data/2021_Consensus_Rankings.csv")
    base_df = clean_consensus_ratings(base_df)

    # Add games played to base dataframe
    base_df = add_games_played_stat(data_2020, base_df)

    # Add Andrewlytics
    base_df["Startability"] = base_df.apply(lambda row: get_startability(starter_points, row.PLAYER, row.POSITION, weekly_points_df), axis=1)
    base_df["Starter_PPG_Delta"] = base_df.apply(lambda row: get_starter_PPG_delta(row.PLAYER, row.POSITION, starter_points, data_2020), axis=1)
    base_df["Consistency"] = base_df.apply(lambda row: get_consistency(row.PLAYER, row.POSITION, row.GAMES_PLAYED, starter_points, weekly_points_df), axis=1)
    base_df["Explosiveness"] = base_df.apply(lambda row: get_explosiveness(row.PLAYER, row.POSITION, row.GAMES_PLAYED, starter_points, weekly_points_df), axis=1)
    base_df["Available?"] = "Y"
    
    # Add previous year stats to base dataframe
    qb_2020_stats = pd.read_csv("./Data/2020_Stats_QB.csv")
    rb_2020_stats = pd.read_csv("./Data/2020_Stats_RB.csv")
    wr_2020_stats = pd.read_csv("./Data/2020_Stats_WR.csv")
    te_2020_stats = pd.read_csv("./Data/2020_Stats_TE.csv")
    base_df = add_previous_year_stats(base_df, qb_2020_stats, rb_2020_stats, wr_2020_stats, te_2020_stats)

    output_draft_sheet(base_df, weekly_points_df)