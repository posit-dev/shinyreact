import "./shinyreact.css"; // side-effect import is how Vite bundles CSS — no alternative

import { installDepDiscovery } from "./dep-discovery";
import { installGlobal } from "./global";
import { installModalFallback } from "./modal-fallback";

installGlobal();
installDepDiscovery();
installModalFallback();
