import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import "./App.css";

function App() {
  const [count, setCount] = useState(0);

  return (
    <>
      <div>
        <a href="https://tokenminds.co" target="_blank">
          <img
            src={`https://framerusercontent.com/images/7Fjd4JhBn4XdPoBAztnI31U.webp`}
            className="logo"
            alt="Tokenminds logo"
          />
        </a>
      </div>
      <h1>My First Telegram Mini App</h1>
      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          count is {count}
        </button>
      </div>
      <div>
        <p>
          Click{" "}
          <a href="https://docs.ton.org/develop/dapps/telegram-apps/app-examples"
            target="_blank"
          >
            here
          </a>{" "}
          to learn more.
        </p>
      </div>
    </>
  );
}

export default App;