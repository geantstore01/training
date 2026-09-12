import * as React from "react";
import {cn} from "@/lib/utils";
export function Input({className,...props}:React.ComponentProps<"input">){return <input className={cn("w-full min-h-12 rounded-xl border-2 border-border bg-white px-4 py-3 text-base focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-teal-700 disabled:opacity-60",className)} {...props}/>;}
