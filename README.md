# Personal Finance Tracker

## About the Application

The Personal Finance Tracker is a lightweight personal finance tracker that demonstrates the speed and utility of GitHub Copilot in building high-quality, functional code with minimal effort. The application allows users to upload a CSV file containing their transaction data, automatically categorizes each transaction into predefined spending categories, and provides an interactive dashboard that visualizes spending by category and comparison of actual spending vs. budgeted amounts.

### Core Features

#### Expense Tracking & Categorization

- **What it does:**
  - Allows users to upload a CSV file containing their transaction data.
  - Automatically categorizes each transaction into predefined spending categories like Food, Rent, Utilities, etc.

- **Why it’s useful:**
  - Simplifies understanding of spending habits by automating categorization.
  - Helps users save time by avoiding manual data entry or tagging.

- **Technical Overview:**
  - **Input:** CSV file containing transaction details (Date, Description, Amount).
  - **Processing:** Backend parses the CSV and applies categorization rules.
  - **Output:** A categorized summary of transactions, stored in a database.

#### Budget Visualization Dashboard

- **What it does:**
  - Provides an interactive dashboard that visualizes:
    - Spending by category (pie chart or bar graph).
    - Comparison of actual spending vs. budgeted amounts.

- **Why it’s useful:**
  - Gives users a quick overview of their financial health.
  - Encourages better budgeting and spending habits.

- **Technical Overview:**
  - **Input:** Categorized transaction data from the backend.
  - **Processing:** Summarizes spending by category and compares it with user-defined budgets.
  - **Output:** Interactive charts displayed on the frontend.

## How to Deploy the Application

### Prerequisites

- Docker installed on your machine.
- Node.js and npm installed on your machine.

### Steps to Deploy

1. **Clone the repository:**
   ```sh
   git clone https://github.com/sdamache/mint-clone.git
   cd mint-clone
   ```

2. **Build and run the Docker containers:**
   ```sh
   docker-compose up --build
   ```

3. **Access the application:**
   - The backend will be running on `http://localhost:5000`.
   - The frontend will be running on `http://localhost:3000`.

4. **Upload a CSV file:**
   - Use the frontend interface to upload a CSV file containing your transaction data.

5. **View the Budget Visualization Dashboard:**
   - After uploading the CSV file, navigate to the Budget Visualization Dashboard to view your categorized transactions and spending visualizations.

## Additional Information

- The backend is built using Flask and handles CSV file uploads, transaction categorization, and storage in a SQLite database.
- The frontend is built using React and provides the user interface for uploading CSV files and displaying the budget visualization dashboard.
- The application uses Axios for HTTP requests between the frontend and backend.
- The application uses Chart.js for visualizing spending data in the budget dashboard.

