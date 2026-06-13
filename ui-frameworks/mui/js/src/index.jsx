import { Alert } from "@/components/alert";
import { Button } from "@/components/button";
import { Card } from "@/components/card";
import { Checkbox } from "@/components/checkbox";
import { Dialog } from "@/components/dialog";
import { Select } from "@/components/select";
import { Slider } from "@/components/slider";
import { Switch } from "@/components/switch";
import { TextField } from "@/components/text-field";

window.shinyreact.registerComponents(null, {
  "mui:Alert": Alert,
  "mui:Button": Button,
  "mui:Card": Card,
  "mui:Checkbox": Checkbox,
  "mui:Dialog": Dialog,
  "mui:Select": Select,
  "mui:Slider": Slider,
  "mui:Switch": Switch,
  "mui:TextField": TextField,
});
