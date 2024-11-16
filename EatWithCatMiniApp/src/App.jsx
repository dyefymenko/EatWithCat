// React component for the Telegram Mini App UI
import React from 'react';
import './App.css';

// Sample data for dishes
const menuData = [
    { restaurant: 'The Happy Spoon', dishName: 'Pancake Delight', price: '$8.99', photo: 'img/avocado.jpeg' },
    { restaurant: 'Sunny Cafe', dishName: 'Avocado Toast', price: '$7.50', photo: 'img/avocado.jpeg' },
    { restaurant: 'Blue Moon Diner', dishName: 'French Toast Magic', price: '$9.25', photo: 'img/avocado.jpeg' },
    { restaurant: 'Sparkle Eatery', dishName: 'Berry Bliss Bowl', price: '$10.99', photo: 'img/avocado.jpeg' },
    { restaurant: 'Golden Fork', dishName: 'Lemon Tart', price: '$6.50', photo: 'img/avocado.jpeg' },
    { restaurant: 'Crispy Crust', dishName: 'Cheese Pizza', price: '$12.00', photo: 'img/avocado.jpeg' },
    { restaurant: 'Sweet Dreams', dishName: 'Chocolate Mousse', price: '$5.99', photo: 'img/avocado.jpeg' },
    { restaurant: 'Healthy Bites', dishName: 'Quinoa Salad', price: '$9.75', photo: 'img/avocado.jpeg' },
    { restaurant: 'Cozy Corner', dishName: 'Apple Pie', price: '$4.50', photo: 'img/avocado.jpeg' }
];

function App() {
    return (
        <div id="app">
            {menuData.map((dish, index) => (
                <div key={index} className="dish-card">
                    <div className='dish-photo'>
                      <img src={dish.photo} alt={dish.dishName} className="dish-photo" height={100} width={100}/>
                    </div>
                    <div className="dish-details">
                        <h3 className="restaurant-name">{dish.restaurant}</h3>
                        <p className="dish-name">{dish.dishName}</p>
                        <p className="dish-price">{dish.price}</p>
                    </div>
                </div>
            ))}
        </div>
    );
}

export default App;
