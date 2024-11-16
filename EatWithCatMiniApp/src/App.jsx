// React component for the Telegram Mini App UI
import React from 'react';
import './App.css';

// Sample data for dishes
const cats = ['taco.png', 'pasta.png', 'pizza.png', 'melon.png'];

function App() {
    return (
        <div id="app">
            {cats.map((cat, index) => (
                <div key={index} className="dish-card">
                    <img src={cat} alt="kitty with food" />
                </div>
            ))}
        </div>
    );
} 

export default App;
