import boto3
import os
import pytz
import requests
import logging
from datetime import datetime

# Define the Central Time timezone
central = pytz.timezone("US/Central")

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Retrieve secrets from environment variables
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.environ.get("AWS_REGION")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME")

# AWS Clients
boto3.setup_default_session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)
sns_client = boto3.client("sns")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

# Constants
TEAM_ID = 16  # Chicago Blackhawks' team ID
BASE_URL = "https://api-web.nhle.com/v1/"


# Monitor Chicago Blackhawks goals in the first period of home games
def main():
    logging.info("Starting Blackhawks goal monitor.")

    today = datetime.now(central).strftime("%Y-%m-%d")
    logging.info(f"Fetching games for today: {today}")

    games = fetch_games_for_today(today)

    if not games:
        logging.info("No games found for today.")
        return

    logging.info(f"Found {len(games)} game(s) today.")

    for game in games:
        if is_blackhawks_home_game(game):
            game_id = game["id"]
            logging.info(f"Blackhawks home game found: Game ID {game_id}")

            if check_first_period_goal(game_id):
                logging.info(
                    f"Goal detected in the first period for Game ID {game_id}."
                )

                if not has_notification_been_sent(game_id):
                    logging.info(
                        f"No notification sent yet for Game ID {game_id}. Sending now."
                    )
                    send_goal_notification(game_id)
                    record_notification_in_dynamodb(game_id)
                else:
                    logging.info(f"Notification already sent for Game ID {game_id}.")
            else:
                logging.info(f"No first-period goal detected for Game ID {game_id}.")
        else:
            logging.info(f"Game ID {game['id']} is not a Blackhawks home game.")


# Fetch the schedule for today's games.
def fetch_games_for_today(date):
    url = f"{BASE_URL}schedule/{date}"
    logging.info(f"Fetching game data from: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        # Extract the 'gameWeek' and search for the correct date
        games = next(
            (
                day["games"]
                for day in response.json().get("gameWeek", [])
                if day["date"] == date
            ),
            [],
        )
        return games
    except requests.RequestException as e:
        logging.error(f"Failed to fetch games: {e}")
        return []


# Check if the given game is a home game for the Chicago Blackhawks.
def is_blackhawks_home_game(game):
    try:
        return game["homeTeam"]["id"] == TEAM_ID
    except KeyError as e:
        logging.error(
            f"Missing key in game data for Game ID {game.get('id', 'unknown')}: {e}"
        )
        return False


# Check if the Chicago Blackhawks scored in the first period of the specified game.
def check_first_period_goal(game_id):
    play_by_play_url = f"{BASE_URL}gamecenter/{game_id}/play-by-play"
    try:
        response = requests.get(play_by_play_url)
        response.raise_for_status()
        events = response.json().get("plays", [])

        for event in events:
            if (
                event.get("typeCode") == 505  # 505 is the typeCode for a goal
                and event.get("periodDescriptor", {}).get("number") == 1
            ):
                return True
        return False
    except requests.RequestException as e:
        logging.error(f"Failed to fetch play-by-play data for Game ID {game_id}: {e}")
        return False


# Check DynamoDB to see if a notification has already been sent for the given game.
def has_notification_been_sent(game_id):
    try:
        response = table.get_item(Key={"gameID": str(game_id)})
        return "Item" in response
    except Exception as e:
        logging.error(f"Error checking DynamoDB for Game ID {game_id}: {e}")
        return False  # Return False to allow sending the notification


# Record that a notification has been sent for the given game in DynamoDB.
def record_notification_in_dynamodb(game_id):
    try:
        table.put_item(
            Item={
                "gameID": str(game_id),
                "timestamp": datetime.now(central).isoformat(),
            }
        )
        logging.info(f"Recorded notification in DynamoDB for Game ID {game_id}.")
    except Exception as e:
        logging.error(
            f"Error recording notification in DynamoDB for Game ID {game_id}: {e}"
        )


# Send a notification using AWS SNS.
def send_goal_notification(game_id):
    message = f"Goal scored by the Chicago Blackhawks in the first period of game {game_id}! Check your rewards!"
    try:
        sns_client.publish(TopicArn=SNS_TOPIC_ARN, Message=message)
        logging.info(f"Notification sent for Game ID {game_id}.")
    except Exception as e:
        logging.error(f"Error sending notification for Game ID {game_id}: {e}")


if __name__ == "__main__":
    main()
