// Re-export React from the shinyjson IIFE bundle so esbuild's JSX
// transform can resolve React.createElement at runtime.
export const React = window.shinyjson.React;
