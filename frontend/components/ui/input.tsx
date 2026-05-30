import * as React from "react";

import { cn } from "@/lib/utils";

const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, type, ...props }, ref) => (
    <input
      ref={ref}
      type={type}
      className={cn(
        "flex h-11 w-full rounded-md border border-steel-200 bg-white px-3 text-sm text-ink-900 placeholder:text-steel-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-trust-500",
        className
      )}
      {...props}
    />
  )
);
Input.displayName = "Input";

export { Input };
