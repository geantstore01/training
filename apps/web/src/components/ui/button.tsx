import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
const buttonVariants=cva("inline-flex min-h-11 items-center justify-center gap-2 rounded-xl px-5 py-3 text-base font-bold transition-colors focus-visible:outline-3 focus-visible:outline-offset-4 focus-visible:outline-teal-700 disabled:pointer-events-none disabled:opacity-50",{variants:{variant:{default:"bg-primary text-primary-foreground hover:bg-primary/90",secondary:"bg-secondary text-secondary-foreground hover:bg-secondary/80",outline:"border-2 border-border bg-white hover:bg-muted",ghost:"hover:bg-muted",destructive:"bg-red-800 text-white hover:bg-red-900"}},defaultVariants:{variant:"default"}});
export function Button({className,variant,asChild=false,...props}:React.ComponentProps<"button">&VariantProps<typeof buttonVariants>&{asChild?:boolean}){const Comp=asChild?Slot:"button";return <Comp className={cn(buttonVariants({variant,className}))} {...props}/>;}
