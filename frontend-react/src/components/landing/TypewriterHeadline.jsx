import React, { useState, useEffect } from 'react';

export default function TypewriterHeadline() {
  const prefixText = "Ready For a Smarter ";
  const highlightText = "Check In?";

  const [displayedPrefix, setDisplayedPrefix] = useState("");
  const [displayedHighlight, setDisplayedHighlight] = useState("");
  const [isTypingHighlight, setIsTypingHighlight] = useState(false);

  useEffect(() => {
    let prefixIdx = 0;
    let highlightIdx = 0;
    let timer;

    function typePrefix() {
      if (prefixIdx < prefixText.length) {
        setDisplayedPrefix(prefixText.slice(0, prefixIdx + 1));
        prefixIdx++;
        timer = setTimeout(typePrefix, 40 + Math.random() * 20);
      } else {
        setIsTypingHighlight(true);
        timer = setTimeout(typeHighlight, 120);
      }
    }

    function typeHighlight() {
      if (highlightIdx < highlightText.length) {
        setDisplayedHighlight(highlightText.slice(0, highlightIdx + 1));
        highlightIdx++;
        timer = setTimeout(typeHighlight, 45 + Math.random() * 25);
      }
    }

    // Initial delay before typing starts
    timer = setTimeout(typePrefix, 300);

    return () => clearTimeout(timer);
  }, []);

  return (
    <h1 className="font-serif font-bold text-4xl sm:text-5xl md:text-6xl lg:text-[3.75rem] xl:text-[4.25rem] leading-[1.1] sm:leading-[1.08] tracking-tight">
      <span className="text-[#0d382d]">
        {displayedPrefix}
      </span>
      {isTypingHighlight && (
        <span className="text-[#1d7da4] transition-colors">
          {displayedHighlight}
        </span>
      )}
      <span className="inline-block text-[#1d7da4] font-light animate-cursor ml-1">
        |
      </span>
    </h1>
  );
}
