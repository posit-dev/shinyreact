{
  "name": "@{{pkg}}/js",
  "private": true,
  "version": "0.0.0-prototype",
  "type": "module",
  "scripts": {
    "build": "vite build",
    "watch": "vite build --watch",
    "lint": "tsc --noEmit"
  },
  "peerDependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "dependencies": {
    "{{upstream_pkg}}": "latest"
  },
  "devDependencies": {
    "@types/react": "^19.2.0",
    "@types/react-dom": "^19.2.0",
    "@vitejs/plugin-react": "^4.0.0",
    "react": "^19.2.3",
    "react-dom": "^19.2.3",
    "typescript": "^5.0.0",
    "vite": "^5.0.0"
  }
}
