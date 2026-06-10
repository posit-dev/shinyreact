import "@/styles.css";

import { Alert } from "@/components/alert";
import { Badge } from "@/components/badge";
import { Button } from "@/components/button";
import { Card } from "@/components/card";
import { Checkbox } from "@/components/checkbox";
import { Dialog } from "@/components/dialog";
import { DropdownMenu } from "@/components/dropdown-menu";
import { Input } from "@/components/input";
import { Popover } from "@/components/popover";
import { Select } from "@/components/select";
import { Separator } from "@/components/separator";
import { Slider } from "@/components/slider";
import { Switch } from "@/components/switch";

window.shinyreact.registerComponents(null, {
  "shadcn:Alert": Alert,
  "shadcn:Badge": Badge,
  "shadcn:Button": Button,
  "shadcn:Card": Card,
  "shadcn:Checkbox": Checkbox,
  "shadcn:Dialog": Dialog,
  "shadcn:DropdownMenu": DropdownMenu,
  "shadcn:Input": Input,
  "shadcn:Popover": Popover,
  "shadcn:Select": Select,
  "shadcn:Separator": Separator,
  "shadcn:Slider": Slider,
  "shadcn:Switch": Switch,
});
