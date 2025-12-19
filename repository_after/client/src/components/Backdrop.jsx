import React from "react";

const Backdrop = ({ content, remoteUsers }) => {
  const renderBackdrop = () => {
    let elements = [];
    let lastIndex = 0;

    const markers = [];
    Object.entries(remoteUsers).forEach(([, user]) => {
      markers.push({
        index: user.selectionEnd,
        type: "cursor",
        color: user.color,
        name: user.username,
      });
      if (user.selectionStart !== user.selectionEnd) {
        const min = Math.min(user.selectionStart, user.selectionEnd);
        const max = Math.max(user.selectionStart, user.selectionEnd);
        markers.push({ index: min, type: "start-select", color: user.color });
        markers.push({ index: max, type: "end-select", color: user.color });
      }
    });

    markers.sort((a, b) => a.index - b.index);

    let activeSelections = [];

    markers.forEach((marker, i) => {
      const textChunk = content.slice(lastIndex, marker.index);

      if (activeSelections.length > 0) {
        const bgColor = activeSelections[activeSelections.length - 1] + "44";
        elements.push(
          <span key={`t-${i}`} style={{ backgroundColor: bgColor }}>
            {textChunk}
          </span>
        );
      } else {
        elements.push(<span key={`t-${i}`}>{textChunk}</span>);
      }

      if (marker.type === "cursor") {
        elements.push(
          <span
            key={`c-${i}`}
            style={{ position: "relative", display: "inline", fontSize: 0 }}
          >
            <span
              style={{
                position: "absolute",
                top: "-1.2rem",
                left: "-1px",
                width: "2px",
                height: "1.2rem",
                backgroundColor: marker.color,
                zIndex: 10,
              }}
            >
              <span
                style={{
                  position: "absolute",
                  top: "-1.4em",
                  left: 0,
                  backgroundColor: marker.color,
                  color: "#fff",
                  fontSize: "10px",
                  padding: "1px 3px",
                  borderRadius: "3px",
                  whiteSpace: "nowrap",
                }}
              >
                {marker.name}
              </span>
            </span>
          </span>
        );
      } else if (marker.type === "start-select") {
        activeSelections.push(marker.color);
      } else if (marker.type === "end-select") {
        activeSelections.pop();
      }

      lastIndex = marker.index;
    });

    const remainder = content.slice(lastIndex);
    if (activeSelections.length > 0) {
      elements.push(
        <span key="rem" style={{ backgroundColor: activeSelections[0] + "44" }}>
          {remainder}
        </span>
      );
    } else {
      elements.push(<span key="rem">{remainder}</span>);
    }

    elements.push(<br key="br" />);

    return elements;
  };

  return <div className="editor-backdrop">{renderBackdrop()}</div>;
};

export default Backdrop;
