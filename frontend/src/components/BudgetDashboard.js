import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Bar, Pie } from 'react-chartjs-2';
import 'chart.js/auto';
import { Card, Button } from 'react-bootstrap';

function BudgetDashboard() {
  const [transactions, setTransactions] = useState([]);
  const [error, setError] = useState(null);

  const fetchTransactions = async () => {
    try {
      const response = await axios.get('http://localhost:5000/transactions');
      setTransactions(response.data.transactions);
      setError(null);
    } catch (error) {
      setError('Error fetching transactions. Please try again.');
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, []);

  const categorizeTransactions = () => {
    const categories = {};
    transactions.forEach((transaction) => {
      if (!categories[transaction.Category]) {
        categories[transaction.Category] = 0;
      }
      categories[transaction.Category] += transaction.Amount;
    });
    return categories;
  };

  const categories = categorizeTransactions();
  const categoryLabels = Object.keys(categories);
  const categoryData = Object.values(categories);

  const budgetData = {
    labels: categoryLabels,
    datasets: [
      {
        label: 'Spending by Category',
        data: categoryData,
        backgroundColor: [
          'rgba(255, 99, 132, 0.2)',
          'rgba(54, 162, 235, 0.2)',
          'rgba(255, 206, 86, 0.2)',
          'rgba(75, 192, 192, 0.2)',
          'rgba(153, 102, 255, 0.2)',
          'rgba(255, 159, 64, 0.2)',
        ],
        borderColor: [
          'rgba(255, 99, 132, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(255, 206, 86, 1)',
          'rgba(75, 192, 192, 1)',
          'rgba(153, 102, 255, 1)',
          'rgba(255, 159, 64, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };

  return (
    <div>
      <h2>Budget Visualization Dashboard</h2>
      {error && <p className="error">{error}</p>}
      <Card className="chart-container">
        <Card.Body>
          <Pie data={budgetData} />
        </Card.Body>
      </Card>
      <Card className="chart-container">
        <Card.Body>
          <Bar data={budgetData} />
        </Card.Body>
      </Card>
      <Button onClick={fetchTransactions}>Refresh Data</Button>
    </div>
  );
}

export default BudgetDashboard;
