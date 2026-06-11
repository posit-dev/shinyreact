import * as React from "react";
import { OTPInput, OTPInputContext } from "input-otp";
import { useShinyInput } from "@/hooks";
import { MinusIcon } from "lucide-react";
import { cn } from "@/lib/utils";
function InputOTP({
  className,
  containerClassName,
  ...props
}) {
  return <OTPInput
    data-slot="input-otp"
    containerClassName={cn(
      "flex items-center gap-2 has-disabled:opacity-50",
      containerClassName
    )}
    className={cn("disabled:cursor-not-allowed", className)}
    {...props}
  />;
}
function InputOTPGroup({ className, ...props }) {
  return <div
    data-slot="input-otp-group"
    className={cn("flex items-center", className)}
    {...props}
  />;
}
function InputOTPSlot({
  index,
  className,
  ...props
}) {
  const inputOTPContext = React.useContext(OTPInputContext);
  const { char, hasFakeCaret, isActive } = inputOTPContext?.slots[index] ?? {};
  return <div
    data-slot="input-otp-slot"
    data-active={isActive}
    className={cn(
      "relative flex h-9 w-9 items-center justify-center border-y border-r border-input text-sm shadow-xs transition-all outline-none first:rounded-l-md first:border-l last:rounded-r-md aria-invalid:border-destructive data-[active=true]:z-10 data-[active=true]:border-ring data-[active=true]:ring-[3px] data-[active=true]:ring-ring/50 data-[active=true]:aria-invalid:border-destructive data-[active=true]:aria-invalid:ring-destructive/20 dark:bg-input/30 dark:data-[active=true]:aria-invalid:ring-destructive/40",
      className
    )}
    {...props}
  >{char}{hasFakeCaret && <div className="pointer-events-none absolute inset-0 flex items-center justify-center"><div className="h-4 w-px animate-caret-blink bg-foreground duration-1000" /></div>}</div>;
}
function InputOTPSeparator({ ...props }) {
  return <div data-slot="input-otp-separator" role="separator" {...props}><MinusIcon /></div>;
}

// --- shinyreact bridge ---
// Input: server reads input.<input_id>() as the OTP string (complete or partial).
// Props: input_id, length (default 6), separator (show dash between groups, default false), className.
function ShinyInputOtp({ element }) {
  const { input_id, length = 6, separator = false, className } = element.props;
  const [value, setValue] = useShinyInput(input_id, "");
  const mid = Math.floor(length / 2);
  return (
    <InputOTP
      maxLength={length}
      value={value ?? ""}
      onChange={setValue}
      className={className}
    >
      <InputOTPGroup>
        {Array.from({ length: separator ? mid : length }, (_, i) => (
          <InputOTPSlot key={i} index={i} />
        ))}
      </InputOTPGroup>
      {separator && (
        <>
          <InputOTPSeparator />
          <InputOTPGroup>
            {Array.from({ length: length - mid }, (_, i) => (
              <InputOTPSlot key={i + mid} index={i + mid} />
            ))}
          </InputOTPGroup>
        </>
      )}
    </InputOTP>
  );
}

export { ShinyInputOtp as InputOtp };
