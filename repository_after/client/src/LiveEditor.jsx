import { useState, useRef, useLayoutEffect } from "react";
import { useSocket } from "./hooks/useSocket";
import Backdrop from "./components/Backdrop";
import TextArea from "./components/TextArea";
import { socket } from "./services/socket";

const LiveEditor = ({ roomId, username }) => {
  const [content, setContent] = useState("");
  const [remoteUsers, setRemoteUsers] = useState({});
  const textareaRef = useRef(null);
  const cursorRef = useRef({ start: 0, end: 0 });

  useSocket(
    roomId,
    username,
    textareaRef,
    setContent,
    setRemoteUsers,
    cursorRef
  );

  useLayoutEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.setSelectionRange(
        cursorRef.current.start,
        cursorRef.current.end
      );
    }
  }, [content]);

  const handleChange = (e) => {
    const newVal = e.target.value;
    const oldVal = content;

    let start = 0;
    while (
      start < oldVal.length &&
      start < newVal.length &&
      oldVal[start] === newVal[start]
    ) {
      start++;
    }

    let endOld = oldVal.length;
    let endNew = newVal.length;

    while (
      endOld > start &&
      endNew > start &&
      oldVal[endOld - 1] === newVal[endNew - 1]
    ) {
      endOld--;
      endNew--;
    }

    const insertedText = newVal.slice(start, endNew);

    if (start !== endOld || insertedText.length > 0) {
      socket.emit("text-change", {
        roomId,
        delta: {
          start,
          end: endOld,
          text: insertedText,
        },
      });
    }

    setContent(newVal);

    cursorRef.current = {
      start: e.target.selectionStart,
      end: e.target.selectionEnd,
    };
  };

  const handleSelect = (e) => {
    cursorRef.current = {
      start: e.target.selectionStart,
      end: e.target.selectionEnd,
    };
    socket.emit("cursor-move", {
      roomId,
      selectionStart: e.target.selectionStart,
      selectionEnd: e.target.selectionEnd,
    });
  };

  return (
    <div className="editor-wrapper">
      <Backdrop content={content} remoteUsers={remoteUsers} />
      <TextArea
        ref={textareaRef}
        content={content}
        onChange={handleChange}
        onSelect={handleSelect}
      />
    </div>
  );
};

export default LiveEditor;
