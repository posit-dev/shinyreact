import "./shinyreact.css"; // side-effect import is how Vite bundles CSS — no alternative

import { installGlobal } from "./global";
import { registerShinyreactOutputBinding } from "./output-binding";
import { installInlineSpecSeeding } from "./inline-spec";

installGlobal();
registerShinyreactOutputBinding();
installInlineSpecSeeding();
