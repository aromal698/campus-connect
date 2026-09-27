# CampusConnect — a B.Tech student community app

A beginner-friendly Streamlit starter app for students across all departments. It includes a campus feed, student-created study groups, a cross-department project teammate form, and an optional AI study buddy.

## Files in this project

```text
campus-connect/
├── app.py                         # The Python code that builds the app
├── requirements.txt               # Python packages Streamlit installs
├── README.md                      # These instructions
├── .gitignore                     # Keeps secrets and temporary files out of GitHub
└── .streamlit/
    ├── config.toml                # App colors and theme
    └── secrets.toml.example       # Safe Gemini settings template; no real API key
```

You only need to edit `app.py` to change the app's features. `config.toml` sets the app's color theme. `requirements.txt` tells Python which packages to install. `secrets.toml.example` demonstrates the Gemini settings format. To use AI locally, copy it and name the copy `secrets.toml`, then put your real key in that private copy.

## App color theme

The app uses a calm green and off-white palette with dark text for readability. The palette is set in `.streamlit/config.toml`; `app.py` also styles the cards, sidebar, and buttons to match. To change the theme later, edit `config.toml` and commit the change to GitHub.

## 1. Get the project onto your computer

If you are looking at these files in a GitHub repository, open the green **Code** button and choose **Download ZIP**. Extract the ZIP somewhere easy to find, such as your Desktop. You can also use GitHub's **Add file → Create new file** to create each file from this project, but downloading the ZIP is simpler.

You should see `app.py`, `requirements.txt`, and `README.md` in the same folder.

## 2. Install Python

Install Python 3.10 or newer from [python.org](https://www.python.org/downloads/). On Windows, tick **Add Python to PATH** in the installer. After installation, open PowerShell or Command Prompt and check:

```text
python --version
```

If Windows does not recognize `python`, close and reopen the terminal. You can also try `py --version`.

## 3. Open a terminal in the project folder

In File Explorer, open the folder containing `app.py`. Click the address bar, type `powershell`, and press Enter. This opens a terminal in that folder.

## 4. Install the app's packages

Run:

```text
python -m pip install -r requirements.txt
```

If your computer uses the `py` command, run `py -m pip install -r requirements.txt` instead.

## 5. Start the app

Run:

```text
python -m streamlit run app.py
```

If needed, use `py -m streamlit run app.py`. Your browser should open the app. Keep the terminal window open while using it. To stop the app, click the terminal and press **Ctrl+C**.

## 6. Try it out

Use the left menu to visit the campus feed, create a study group, post a project teammate request, and open the AI study buddy. The AI section works in demo mode until you set up an API key. Posts and groups are kept in temporary session memory; they reset when the server restarts and are not shared between students. Before inviting a whole campus, connect a database and add sign-in and moderation.

## 7. Optional: connect the free-tier Gemini study buddy

The study buddy uses Google's Gemini API. Google currently offers a free tier for some models, subject to per-project usage limits; availability and limits can change. See Google's [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing) and [rate limits](https://ai.google.dev/gemini-api/docs/rate-limits).

The Gemini free tier may use prompts and responses to improve Google's products. Avoid entering personal, sensitive, or confidential information, and tell students that their messages are sent to Google. Review Google's current terms before opening this app to a wider audience.

Create a Gemini API key in [Google AI Studio](https://aistudio.google.com/app/apikey). Do not paste the key into `app.py`, a GitHub file, or a message.

For local use:

1. In the app folder, open `.streamlit`.
2. Copy `secrets.toml.example` and rename the copy to `secrets.toml` (keep the example file too).
3. Open `secrets.toml` and replace the entire placeholder `paste-your-gemini-api-key-here` with your Gemini API key:

```toml
GEMINI_API_KEY = "paste-your-gemini-api-key-here"
GEMINI_MODEL = "gemini-3.5-flash-lite"
```

4. Save the file and restart Streamlit. The `.gitignore` file prevents this secrets file from being added to Git by accident.

For a deployed app on Streamlit Community Cloud:

1. Open your app's page in your [Streamlit Community Cloud workspace](https://share.streamlit.io/).
2. Open the app menu and choose **Settings**. You can also enter the secrets during deployment under **Advanced settings → Secrets**.
3. In the **Secrets** box, remove the old `OPENAI_API_KEY` and `OPENAI_MODEL` entries if they are present. Paste the two Gemini lines shown above and replace the placeholder with your Gemini API key.
4. Save. Streamlit will restart the app, and the AI study buddy can use the key.

Never put the real key in the public GitHub repository. The AI code runs on the Streamlit server, so the key is not sent to visitors' browsers. If you accidentally publish a real key, revoke it in Google AI Studio and create a new one.

## 8. Put the app on GitHub

1. Sign in to GitHub and create a new repository. Choose a name such as `campus-connect`.
2. If you already downloaded this project, open the repository and choose **Add file → Upload files**.
3. Drag in `app.py`, `requirements.txt`, `README.md`, and `.gitignore`. Do not upload `.streamlit/secrets.toml`.
4. Choose **Commit changes** at the bottom.

## 9. Publish it with Streamlit Community Cloud

1. Sign in at [share.streamlit.io](https://share.streamlit.io/) using GitHub.
2. Choose **Create app**, then select your `campus-connect` repository and the `app.py` file.
3. Choose **Deploy**. Streamlit reads `requirements.txt` and installs the listed packages.
4. If you want the AI feature online, add `GEMINI_API_KEY` and `GEMINI_MODEL` under **Advanced settings → Secrets** during deployment, or add them later under the app's **Settings → Secrets**. Save the settings to restart the app.

If your repository already exists and you change files on your computer, upload the changed files to GitHub and commit them. Streamlit Community Cloud uses the committed GitHub files and then updates the deployed app.

The exact labels in GitHub or Streamlit Cloud can change, but the key choices are the repository, `app.py`, and the app secrets.

## What this prototype does not include yet

- Accounts, college email verification, or permanent database storage
- Private messaging, file uploads, moderation, or admin tools
- Production protections for a large public student community

Those can be added after the first version is running and students have tried it.
