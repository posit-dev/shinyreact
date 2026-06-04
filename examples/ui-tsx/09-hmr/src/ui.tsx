import * as ReactDOM from "react-dom/client";

import App from "./App";

// Mount only. Component definitions live in App.tsx so the refresh boundary is
// clean. Editing THIS file triggers a full reload (rare); editing App.tsx does
// not. Calling createRoot in a file that also defines components would defeat
// Fast Refresh.
ReactDOM.createRoot(document.getElementById("root")!).render(<App />);
