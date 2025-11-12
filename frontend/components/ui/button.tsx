/**
 * Button Component (shadcn/ui)
 *
 * A customizable button component built on Radix UI primitives.
 * Supports multiple variants, sizes, and can render as any element via asChild prop.
 */

import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

/**
 * Button variant styles using class-variance-authority.
 *
 * Defines visual variants (default, destructive, outline, secondary, ghost, link)
 * and sizes (default, sm, lg, icon).
 */
const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "bg-primary text-primary-foreground shadow hover:bg-primary/90",
        destructive:
          "bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90",
        outline:
          "border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground",
        secondary:
          "bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-md px-8",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

/**
 * Button component props.
 *
 * Extends standard HTML button attributes with variant and size options.
 */
export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  /** If true, renders as Radix Slot component allowing custom elements */
  asChild?: boolean
}

/**
 * Button Component
 *
 * Flexible button component with multiple visual variants and sizes.
 * Can render as any element using the asChild prop with Radix Slot.
 *
 * @param props - Button props
 * @param props.variant - Visual style (default, destructive, outline, secondary, ghost, link)
 * @param props.size - Button size (default, sm, lg, icon)
 * @param props.asChild - If true, merges props to child element instead of rendering button
 * @param props.className - Additional CSS classes
 * @param ref - React ref for button element
 *
 * @example
 * ```tsx
 * // Standard button
 * <Button variant="default" size="default">Click me</Button>
 *
 * // Destructive button (for delete/remove actions)
 * <Button variant="destructive">Delete</Button>
 *
 * // Icon button
 * <Button variant="ghost" size="icon">
 *   <TrashIcon />
 * </Button>
 *
 * // Render as link (using asChild with Radix Slot)
 * <Button asChild>
 *   <a href="/home">Home</a>
 * </Button>
 * ```
 */
const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
