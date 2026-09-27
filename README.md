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
    └── secrets.toml.example       # Safe template; contains no real API key
```

You only need to edit `app.py` to change the app. `requirements.txt` tells Python which packages to install. `secrets.toml.example` demonstrates the AI settings format. To use AI locally, copy it and name the copy `secrets.toml`, then put your real key in that private copy.

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

## 7. Optional: connect the AI study buddy

The AI feature uses the OpenAI API. API usage may cost money depending on your account and usage. Create an API key in the [OpenAI API platform](https://platform.openai.com/api-keys). Do not paste the key into `app.py`, a GitHub file, or a message.

For local use:

1. In the app folder, open `.streamlit`.
2. Copy `secrets.toml.example` and rename the copy to `secrets.toml` (keep the example file too).
3. Open `secrets.toml` and replace the placeholder with your own key:

```toml
OPENAI_API_KEY = "paste-your-key-here"
OPENAI_MODEL = "gpt-5"
```

4. Save the file and restart Streamlit. The `.gitignore` file prevents this secrets file from being added to Git by accident.

For a deployed app, paste these same two lines into **Advanced settings → Secrets** while deploying, or your app's **Settings → Secrets** later. Never put the real key in the public GitHub repository. The AI code runs on the Streamlit server, so the key is not sent to visitors' browsers.

## 8. Put the app on GitHub

1. Sign in to GitHub and create a new repository. Choose a name such as `campus-connect`.
2. If you already downloaded this project, open the repository and choose **Add file → Upload files**.
3. Drag in `app.py`, `requirements.txt`, `README.md`, and `.gitignore`. Do not upload `.streamlit/secrets.toml`.
4. Choose **Commit changes** at the bottom.

## 9. Publish it with Streamlit Community Cloud

1. Sign in at [share.streamlit.io](https://share.streamlit.io/) using GitHub.
2. Choose **Create app**, then select your `campus-connect` repository and the `app.py` file.
3. Choose **Deploy**. Streamlit reads `requirements.txt` and installs the listed packages.
4. If you want the AI feature online, open the deployed app's settings, add `OPENAI_API_KEY` and `OPENAI_MODEL` under **Secrets**, and restart/redeploy the app.

The exact labels in GitHub or Streamlit Cloud can change, but the key choices are the repository, `app.py`, and the app secrets.

## What this prototype does not include yet

- Accounts, college email verification, or permanent database storage
- Private messaging, file uploads, moderation, or admin tools
- Production protections for a large public student community

Those can be added after the first version is running and students have tried it.
