# 🏡 HomeChore

**HomeChore** is a web application designed to streamline the management of household chores. Built with 🐍 Flask, 🗄️ SQLAlchemy, and 🎨 Bootstrap 5 (featuring dark mode via Bootstrap 5.3), it offers a user-friendly interface to view, add, update, and complete chores. The app utilizes 🐘 PostgreSQL as its database and is containerized using 🐳 Docker and Docker Compose.

## ✨ Features

- **Chore Management:**  
  View chores organized into four categories:
  - 📅 **Due Today**
  - 📆 **Next 3 Days**
  - 📅 **Next Week**
  - 📋 **Other Tasks**  
  Each chore card displays details such as the last completed time and the user who completed it.

- **Dark Mode Interface:**  
  The app employs Bootstrap 5.3’s dark theme for a modern, sleek look. 🌑

- **Responsive Layout:**  
  Features an off-canvas sidebar for navigation and a responsive dashboard that evenly displays chore cards. 📱💻

- **Timezone Configuration:**  
  Users can select their preferred timezone for accurate date/time display. 🌍🕒

- **Containerization:**  
  The application is containerized with Docker, and a Docker Compose setup orchestrates both the Flask app and PostgreSQL database. 🐳

## 🛠️ Prerequisites

- [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/)
- Alternatively, Python 3.10+ with the required packages if running locally without Docker 🐍

## 🚀 Setup

### 1. Clone the Repository

```bash
git clone https://github.com/islandjon/HomeChore.git
cd HomeChore
```

### 2. Install Dependencies

If you prefer running the app locally (without Docker), install the dependencies using:

```bash
pip install -r requirements.txt
```

### 3. Configure the Database

Initialize your PostgreSQL database schema. You can use either:

- **Flask-Migrate:**  
  ```bash
  flask db init
  flask db migrate
  flask db upgrade
  ```
- **SQLAlchemy `create_all()`:**  
  Add the following code to run once:
  ```python
  with app.app_context():
      db.create_all()
  ```

### 4. Running with Docker Compose

A `Dockerfile` and `docker-compose.yml` are included in the repo. To build and run the app with PostgreSQL:

```bash
docker-compose up --build
```

This command will:

- Build the Docker image for the Flask app.
- Spin up a PostgreSQL container.
- Start the Flask application on port 5000.

Access the application at [http://localhost:5000](http://localhost:5000). 🌐

## 📂 Project Structure

- **`src/app.py`**: Main Flask application and route definitions.
- **`src/templates/`**: HTML templates (dashboard, settings, etc.) using Bootstrap 5.
- **`Dockerfile`**: Builds the Flask app container.
- **`docker-compose.yml`**: Orchestrates the Flask app and PostgreSQL containers.
- **`README.md`**: This documentation file.

## 🎨 Customization

- **UI & Dark Mode:**  
  The app leverages Bootstrap 5.3’s dark mode. Modify templates or add custom CSS as needed.

- **Timezone Settings:**  
  A settings section lets users choose their timezone, ensuring accurate date/time display.

- **Extending Functionality:**  
  The app is designed to be modular and easily extendable. Contributions are welcome! 🤝

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome. Please open an issue or submit a pull request for improvements, bug fixes, or new features.

## 🙏 Acknowledgements

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Bootstrap 5.3 Documentation](https://getbootstrap.com/docs/5.3/)
- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

Happy chore managing! 🧹✨