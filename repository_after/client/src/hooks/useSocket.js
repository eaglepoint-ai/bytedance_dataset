import { useEffect, useRef } from "react";
import { socket } from "./socket";

export const useSocket = (
  roomId,
  username,
  textareaRef,
  setContent,
  setRemoteUsers,
  cursorRef
) => {
  useEffect(() => {
    socket.emit("join-room", { roomId, username });

    socket.on("request-state", ({ requesterId }) => {
      socket.emit("sync-state", {
        targetId: requesterId,
        content: textareaRef.current.value,
      });
    });

    socket.on("receive-state", ({ content }) => {
      setContent(content);
    });

    socket.on("user-joined", ({ id, color, username }) => {
      setRemoteUsers((prev) => ({
        ...prev,
        [id]: { color, username, selectionStart: 0, selectionEnd: 0 },
      }));
    });

    socket.on("user-left", ({ id }) => {
      setRemoteUsers((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
    });

    socket.on(
      "remote-cursor",
      ({ id, selectionStart, selectionEnd, color, username }) => {
        setRemoteUsers((prev) => ({
          ...prev,
          [id]: { color, username, selectionStart, selectionEnd },
        }));
      }
    );

    socket.on("remote-change", ({ delta }) => {
      const { start, end, text } = delta;

      setContent((prev) => {
        const before = prev.slice(0, start);
        const after = prev.slice(end);
        return before + text + after;
      });

      const currentStart = textareaRef.current.selectionStart;
      const currentEnd = textareaRef.current.selectionEnd;

      const charsAdded = text.length;
      const charsRemoved = end - start;
      const shift = charsAdded - charsRemoved;

      let newStart = currentStart;
      let newEnd = currentEnd;

      if (currentStart > end) {
        newStart += shift;
      } else if (currentStart > start) {
        newStart = start + charsAdded;
      }

      if (currentEnd > end) {
        newEnd += shift;
      } else if (currentEnd > start) {
        newEnd = start + charsAdded;
      }

      cursorRef.current = { start: newStart, end: newEnd };
    });

    return () => {
      socket.off("request-state");
      socket.off("receive-state");
      socket.off("remote-change");
      socket.off("remote-cursor");
      socket.off("user-joined");
      socket.off("user-left");
    };
  }, [roomId, username, textareaRef, setContent, setRemoteUsers, cursorRef]);
};
