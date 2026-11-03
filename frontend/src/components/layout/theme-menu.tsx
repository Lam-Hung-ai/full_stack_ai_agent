"use client";

import { MonitorIcon, MoonIcon, SunIcon } from "lucide-react";
import { useTheme } from "next-themes";
import {
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
} from "@/components/ui/dropdown-menu";

const THEMES = [
  { value: "light", label: "Sáng", icon: SunIcon },
  { value: "dark", label: "Tối", icon: MoonIcon },
  { value: "system", label: "Theo hệ thống", icon: MonitorIcon },
] as const;

/** Submenu of a dropdown: light, dark or the system's choice. */
export function ThemeMenu() {
  const { theme = "system", setTheme } = useTheme();
  const current = THEMES.find((option) => option.value === theme) ?? THEMES[2];

  return (
    <DropdownMenuSub>
      <DropdownMenuSubTrigger>
        <current.icon />
        <span>Giao diện</span>
        <span className="ml-auto text-muted-foreground text-xs">{current.label}</span>
      </DropdownMenuSubTrigger>
      <DropdownMenuSubContent className="w-44">
        <DropdownMenuRadioGroup onValueChange={setTheme} value={theme}>
          {THEMES.map(({ value, label, icon: Icon }) => (
            <DropdownMenuRadioItem key={value} value={value}>
              <Icon />
              {label}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuSubContent>
    </DropdownMenuSub>
  );
}
