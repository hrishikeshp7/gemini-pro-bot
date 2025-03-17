<div align="center">
  **GEmini 1.5 API is live and this is teh updated model. **
(Originally buily by @rabilrbl for gemini 1.0 , this repo is only for 1.5 version )
  # GEMINI-1.5-PRO-BOT
  
  **A Python Telegram bot powered by Google's `gemini-pro` LLM API**

  *This is a Python Telegram bot that uses Google's gemini-pro LLM API to generate creative text formats based on user input. It is designed to be a fun and interactive way to explore the possibilities of large language models.*
  
[Gemini Bot Preview](https://github.com/rabilrbl/gemini-pro-bot/assets/63334479/ffddcdfa-09c2-4f02-b14d-4407e888b605)

</div>

### Features
* Currently Updated to gemini 1.5 pro model (It is in private access so you will need to get access to it )
* Generate creative text formats like poems, code, scripts, musical pieces, etc.
* Stream the generation process, so you can see the text unfold in real-time.
* Reply to your messages with Bard's creative output.
* Easy to use with simple commands:
    * `/start`: Greet the bot and get started.
    * `/help`: Get information about the bot's capabilities.
* Send any text message to trigger the generation process.
* Send any image with captions to generate responses based on the image. (Multi-modal support)
* User authentication to prevent unauthorized access by setting `AUTHORIZED_USERS` in the `.env` file (optional).

### Remaining to do 

* Add Video context functionality .
* PDF and document suppport .


### Requirements

* Python 3.10+
* Telegram Bot API token
* Google `gemini-pro-1.5` API key
* dotenv (for environment variables)


### Docker

#### GitHub Container Registry
Simply run the following command to run the pre-built image from GitHub Container Registry:

```shell
docker run --env-file .env ghcr.io/rabilrbl/gemini-pro-bot:latest
```

Update the image with:
```shell
docker pull ghcr.io/rabilrbl/gemini-pro-bot:latest
```

#### Build
Build the image with:
```shell
docker build -t gemini-pro-bot .
```
Once the image is built, you can run it with:
```shell
docker run --env-file .env gemini-pro-bot
```

#### CircleCI Pipeline
To set up the CircleCI pipeline for building and pushing Docker images, follow these steps:

1. Create a CircleCI account and link it to your GitHub repository.
2. Add the following environment variables to your CircleCI project settings:
    * `CR_PAT`: Your GitHub Container Registry Personal Access Token.
    * `GITHUB_USERNAME`: Your GitHub username.
3. Create a `.circleci/config.yml` file in your repository with the following content:
    ```yaml
    version: 2.1

    executors:
      docker-executor:
        docker:
          - image: circleci/python:3.12

    jobs:
      build:
        executor: docker-executor
        steps:
          - checkout
          - setup_remote_docker:
              version: 20.10.7
          - setup_qemu
          - setup_buildx
          - run:
              name: Build Docker image
              command: docker build -t gemini-pro-bot .
          - run:
              name: Save Docker image to workspace
              command: docker save gemini-pro-bot | gzip > gemini-pro-bot.tar.gz
          - persist_to_workspace:
              root: .
              paths:
                - gemini-pro-bot.tar.gz

      push:
        executor: docker-executor
        steps:
          - attach_workspace:
              at: /workspace
          - run:
              name: Load Docker image from workspace
              command: gunzip -c /workspace/gemini-pro-bot.tar.gz | docker load
          - run:
              name: Login to GitHub Container Registry
              command: |
                echo $CR_PAT | docker login ghcr.io -u $GITHUB_USERNAME --password-stdin
          - run:
              name: Push Docker image to GitHub Container Registry
              command: docker push ghcr.io/${GITHUB_USERNAME}/gemini-pro-bot:latest

    workflows:
      version: 2
      build_and_push:
        jobs:
          - build
          - push:
              requires:
                - build
              filters:
                branches:
                  only:
                    - main
                pull_requests:
                  branches:
                    only:
                      - main
    ```

### Installation

1. Clone this repository.
2. Install the required dependencies:
    * `pipenv install` (if using pipenv)
    * `pip install -r requirements.txt` (if not using pipenv)
3. Create a `.env` file and add the following environment variables:
    * `BOT_TOKEN`: Your Telegram Bot API token. You can get one by talking to [@BotFather](https://t.me/BotFather).
    * `GOOGLE_API_KEY`: Your Google Bard API key. You can get one from [Google AI Studio](https://makersuite.google.com/).
    * `AUTHORIZED_USERS`: A comma-separated list of Telegram usernames or user IDs that are authorized to access the bot. (optional) Example value: `shonan23,1234567890`
4. Run the bot:
    * `python main.py` (if not using pipenv)
    * `pipenv run python main.py` (if using pipenv)

### Usage

1. Start the bot by running the script.
   ```shell
   python main.py
   ```
2. Open the bot in your Telegram chat.
3. Send any text message to the bot.
4. The bot will generate creative text formats based on your input and stream the results back to you.
5. If you want to restrict public access to the bot, you can set `AUTHORIZED_USERS` in the `.env` file to a comma-separated list of Telegram user IDs. Only these users will be able to access the bot.
    Example:
    ```shell
    AUTHORIZED_USERS=shonan23,1234567890
    ```

### Bot Commands

| Command | Description |
| ------- | ----------- |
| `/start` | Greet the bot and get started. |
| `/help` | Get information about the bot's capabilities. |
| `/new` | Start a new chat session. |

### Star History

<a href="https://star-history.com/#rabilrbl/gemini-pro-bot&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=rabilrbl/gemini-pro-bot&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=rabilrbl/gemini-pro-bot&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=rabilrbl/gemini-pro-bot&type=Date" />
  </picture>
</a>

### Contributing

We welcome contributions to this project. Please feel free to fork the repository and submit pull requests.

### Disclaimer

This bot is still under development and may sometimes provide nonsensical or inappropriate responses. Use it responsibly and have fun!

### License

This is a free and open-source project released under the GNU Affero General Public License v3.0 license. See the LICENSE file for details.
