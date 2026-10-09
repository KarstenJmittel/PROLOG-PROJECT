# Prolog Project

## Overview
This project combines Python and Prolog to build a web-based application that uses logical rules and a knowledge base to process information and generate results.

## Technologies Used
- **Python** – Application logic and backend
- **Prolog** – Knowledge representation and logical reasoning
- **Flask** – Web application framework
- **HTML** – Web page structure
- **CSS** – User interface styling
- **Database** – Data storage and management

## Project Structure
```text
PROLOG-PROJECT/
├── .vscode/
│   └── settings.json
├── prolog/
│   ├── knowledge_base.pl
│   └── temp_facts.pl
├── static/
│   └── style.css
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   └── incident.html
├── app.py
├── database.py
├── prolog_engine.py
├── .gitignore
└── README.md
```

## Features
- Web-based user interface
- Python backend integration
- Prolog knowledge base and logical reasoning
- Database integration
- Dashboard and incident-related pages

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/KarstenJmittel/PROLOG-PROJECT.git
cd PROLOG-PROJECT
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
```

Activate it on Windows:
```bash
venv\Scripts\activate
```

### 3. Install Dependencies
Install the Python packages required by the project. If a `requirements.txt` file is available, run:

```bash
pip install -r requirements.txt
```

Ensure that SWI-Prolog is installed and available in your system PATH if the application uses it to execute Prolog queries.

### 4. Run the Application
```bash
python app.py
```

Open the local URL displayed in the terminal in your browser.

## Usage
1. Start the application.
2. Open the dashboard in your browser.
3. Use the available pages and features.
4. The backend processes application data and interacts with the Prolog knowledge base.

## Future Improvements
- Improve error handling and validation.
- Add more Prolog rules and facts.
- Enhance the dashboard and user experience.
- Add automated tests and documentation.

## Author
**KarstenJmittel**

## License
This project is available for educational and learning purposes.
