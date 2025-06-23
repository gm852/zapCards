
# Welcome to **ZapCards**

<div align="center">
  <table>
    <tr>
      <td align="center"><img src="webCore/assets/images/settingsOverview.gif" width="440" height="200" alt="Feature 1"></td>
      <td align="center"><img src="webCore/assets/images/ollamaAndUserTools.gif" width="440" height="200" alt="Feature 2"></td>
    </tr>
    <tr>
      <td align="center"><img src="webCore/assets/images/aiCardgen.gif" width="440" height="200" alt="Feature 3"></td>
      <td align="center"><img src="webCore/assets/images/practiceCards.gif" width="440" height="200" alt="Feature 4"></td>
    </tr>
  </table>
</div

> The **only free and open-source self-hosted AI Flashcard App** designed for rapid learning, smart recall, and total customization.

---

## Features

### Flashcard Generator

* Uses **Ollama/~~OpenAI~~** to generate intelligent Q&A pairs.
* Customize prompts per topic e.g., *"Generate 15 flashcards on cell biology."*
* Choose between **basic** or **detailed** answers.
* Use **Ollama** for any model you want.

---

### Deck Manager

* Create, rename, and delete custom decks.
* Data stored locally via **PostgreSQL / MySQL / MariaDB / SQLite & Others**.
* Autosave to save your work for you.
---

### Study Mode

* Flip flashcards (front ↔ back).
* Full screen study mode
* No distractions, clean and simple flashcards.

---

### Settings

* Edit all AI configuration.
* Enable/Disable authentication.
* Settings Export
* Ollama models pull/delete & test.
* Manage users.

---

### (Coming soon Feeatures)

* Quickly add Q\&A pairs via copy/paste.
* Edit Promts for the ai through Web UI
* Organize by deck, tags, or creation date.
* Settings and decks export/import (json,xml,csv)
---

## 🛠 Installation / Setup
### Install As a Service
```bash
git clone https://github.com/gm852/zapcards.git
cd zapcards
bash install.sh
```
And to restart it
```bash
sudo systemctl restart zapcards.service
```

### Setup Using Docker
```bash
git clone https://github.com/gm852/zapcards.git
cd zapcards
sudo docker build -t zapcards .
sudo docker run -d \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -p 8089:8089 \
  --name zapcards \
  --restart unless-stopped \
  zapcards

```

---

## Usage

To start the app manually:

```bash
python -m venv venv && source venv/bin/activate
sudo venv/bin/python run.py
```

---

### Login

Once its up and running, you can use the app at http://hostip:8089

Once you navagate to /login page you can enter the default username and password below and login. We reccommend you delete the default user and make a new one with a secure password.

```
admin : ZapCardsAdmin!
```

---


## License



