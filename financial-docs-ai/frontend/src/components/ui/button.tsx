import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "ghost" | "danger";
};

export function Button({ className, variant = "primary", ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "rounded-lg px-4 py-2 text-sm font-medium transition disabled:opacity-50",
        variant === "primary" && "bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white",
        variant === "ghost" && "bg-transparent hover:bg-[var(--card)] text-[var(--foreground)]",
        variant === "danger" && "bg-[var(--danger)] text-white",
        className,
      )}
      {...props}
    />
  );
}
