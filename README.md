# Chick-fil-A Reward Notifier - Blackhawks

Sends a text message whenever the Blackhawks score a goal in the first period of any 2024-2025 regular season home game. Usually indicative of a [free Chick-fil-A breakfast reward in the Chicagoland area](https://web.archive.org/web/20241205100351if_/https://i0.wp.com/www.cfachicagoland.com/wp-content/uploads/2024/09/2024-free-reward-blackhawks-banner.jpg?w=800&ssl=1).

This project is completely automated with GitHub Actions, and can be manually triggered for a live update. It also uses AWS DynamoDB to store if a notification has already been sent out for a game, preventing duplicate messages. AWS SNS is used to send the text messages.

---

<br/><br/>

# Self-Hosting Instructions

## Prerequisites

1. Set up an AWS account
2. Create a DynamoDB table
3. Set up SNS with a topic and susbcribe with preferred method (SMS, email, etc.)
4. Set up an IAM user with the following permissions:
   - `AmazonDynamoDBFullAccess`
   - `AmazonSNSFullAccess`
5. Obtain and note the following information:
   - AWS Access Key ID
   - AWS Secret Access Key
   - AWS Region
   - SNS Topic ARN
   - DynamoDB Table Name

## Option 1: Local Setup

1. Clone the repository
2. Set the following environment variables:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_REGION`
   - `SNS_TOPIC_ARN`
   - `DYNAMODB_TABLE_NAME`
3. Run `pip install -r requirements.txt` to install the required Python packages
4. Run `python run.py`
5. (Optional) Set up a cron job to run the script at specific intervals

## Option 2: Cloud Setup

1. Fork this repository
2. Go to the repository's settings
3. Go to the "Secrets" tab
4. Add the following secrets:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_REGION`
   - `SNS_TOPIC_ARN`
   - `DYNAMODB_TABLE_NAME`
5. Customize the cron schedule in the `.github/workflows/blackhawks-goal-monitor.yml` file
