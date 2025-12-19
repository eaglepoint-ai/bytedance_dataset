import { useState } from "react";
import LiveEditor from "./LiveEditor.jsx";
import "./App.css";

function App() {
  const [joined, setJoined] = useState(false);
  const [roomId, setRoomId] = useState("");
  const [username, setUsername] = useState("");

  const handleJoin = () => {
    if (roomId && username) setJoined(true);
  };

  return (
    <div className="app-container">
      {!joined ? (
        <div className="join-screen">
          <h1>Live Ephemeral Note</h1>
          <input
            placeholder="Room ID"
            value={roomId}
            onChange={(e) => setRoomId(e.target.value)}
          />
          <input
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <button onClick={handleJoin}>Join / Create Room</button>
        </div>
      ) : (
        <LiveEditor roomId={roomId} username={username} />
      )}
    </div>
  );
}

export default App;
