# FreelanceConnect

FreelanceConnect is a web application designed to connect clients with freelancers. It allows clients to post job requirements and freelancers to showcase their skills and apply for jobs. The application also includes features like resume analysis, job matching, user profiles, and real-time chat functionality.

## Features

- **User Authentication**: Sign up and log in as either a client or a freelancer.
- **Job Posting**: Clients can post jobs with details like title, description, location, budget, and required skills.
- **Job Search**: Freelancers can search for jobs based on keywords.
- **Resume Analysis**: Freelancers can upload their resumes to get recommendations on how to better match job requirements.
- **Job Matching**: Clients can find freelancers whose skills match their job requirements.
- **User Profiles**: Both clients and freelancers can create and update their profiles, including profile pictures and resumes.
- **Real-Time Chat**: Clients and freelancers can communicate in real-time through chat rooms.

## Technologies Used

- **Backend**: Flask (Python)
- **Database**: MongoDB
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: bcrypt for password hashing
- **File Uploads**: Werkzeug for secure file handling
- **Resume Analysis**: Groq API for AI-powered resume analysis
- **Real-Time Communication**: Flask-SocketIO for real-time chat functionality

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/PrashantBarai/FreelanceConnect.git
   cd FreelanceConnect
2. **Run main.py**:
   ```bash
   python main.py
