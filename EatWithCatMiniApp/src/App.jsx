// React component for the Telegram Mini App UI
import React from 'react';
import './App.css';

// Sample data for dishes
const cats = [
  { name: 'taco', path: '/img/taco.png' },
  { name: 'pasta', path: '/img/pasta.png' },
  { name: 'pizza', path: '/img/pizza.png' },
  { name: 'melon', path: '/img/melon.png' }
];
function App() {
    return (
        <div id="app">
            {cats.map((cat, index) => (
                <div key={index} className="dish-card">
                    <img src={cat.path} alt="kitty with food" />
                </div>
            ))}
        </div>
    );
} 

export default App;
