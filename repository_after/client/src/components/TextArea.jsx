import React from "react";

const TextArea = React.forwardRef(
  ({ content, onChange, onSelect }, ref) => {
    return (
      <textarea
        ref={ref}
        value={content}
        onChange={onChange}
        onSelect={onSelect}
        onKeyUp={onSelect}
        onClick={onSelect}
        spellCheck="false"
      />
    );
  }
);

export default TextArea;
