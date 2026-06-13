import Step from "@mui/material/Step";
import StepLabel from "@mui/material/StepLabel";
import Stepper from "@mui/material/Stepper";

// --- shinyreact bridge ---
// Display: renders a static stepper from an array of step labels.
function ShinyStepper({ element }) {
  const { steps = [], active = 0, className } = element.props;
  return (
    <Stepper activeStep={active} className={className}>
      {steps.map((s, i) => (
        <Step key={i}>
          <StepLabel>{s}</StepLabel>
        </Step>
      ))}
    </Stepper>
  );
}

export { ShinyStepper as Stepper };
