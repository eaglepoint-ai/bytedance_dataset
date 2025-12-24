import React, { useEffect, useState, useMemo, useCallback, memo } from "react";

function generateUsers(count) {
  const users = [];
  for (let i = 0; i < count; i++) {
    users.push({
      id: i,
      name: `User ${i}`,
      score: Math.floor(Math.random() * 100),
      lastActive: Date.now() - Math.floor(Math.random() * 100000000),
    });
  }
  return users;
}

// 1. Precompute fixed checksum ONCE (loop is static — sum is constant)
const FIXED_CHECKSUM = (() => {
  let sum = 0;
  for (let i = 0; i < 50_000_000; i++) {
    sum += i % 10;
  }
  return sum;
})();

// 2. Memoize ExpensiveHeader to re-render ONLY if props (total) change
const ExpensiveHeader = memo(function ExpensiveHeader({ total }) {
  return (
    <h2>
      User Analytics ({total}) – checksum: {FIXED_CHECKSUM}
    </h2>
  );
});

// 3. Memoize UserItem so it only re-renders when its props change meaningfully
const UserItem = memo(function UserItem({ user, isSelected, onSelect, formatLastActive }) {
  const label = `${user.name} (${user.score})`;
  const lastSeenText = formatLastActive(user.lastActive);

  return (
    <div
      onClick={() => onSelect(user.id)}
      style={{
        padding: 8,
        cursor: "pointer",
        background: isSelected ? "#eef" : "transparent",
      }}
    >
      <strong>{label}</strong>
      <div style={{ fontSize: 12 }}>
        Last active: {lastSeenText}
      </div>
    </div>
  );
});

export default function UserAnalyticsDashboard() {
  const [users, setUsers] = useState([]);
  const [search, setSearch] = useState("");
  const [selectedUserId, setSelectedUserId] = useState(null);

  useEffect(() => {
    setUsers(generateUsers(8000));
  }, []);

  const formatLastActive = useCallback((timestamp) => {
    const diff = Date.now() - timestamp;
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    return `${days} days ago`;
  }, []);

  const visibleUsers = useMemo(() => {
    const q = search.toLowerCase();
    return [...users]
      .filter((u) => u.name.toLowerCase().includes(q))
      .sort((a, b) => b.score - a.score);
  }, [users, search]);

  return (
    <div style={{ padding: 16 }}>
      <ExpensiveHeader total={users.length} />

      <input
        placeholder="Search users..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        style={{ marginBottom: 12, width: 300 }}
      />

      <div style={{ height: 400, overflow: "auto", border: "1px solid #ccc" }}>
        {visibleUsers.map((user) => (
          <UserItem
            key={user.id}
            user={user}
            isSelected={user.id === selectedUserId}
            onSelect={setSelectedUserId}
            formatLastActive={formatLastActive}
          />
        ))}
      </div>

      {selectedUserId !== null && (
        <div style={{ marginTop: 16 }}>
          Selected user ID: {selectedUserId}
        </div>
      )}
    </div>
  );
}
