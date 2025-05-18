import React from "react";
import Header from "./Header";

interface MainLayoutProps {
  children: React.ReactNode;
}

export default function MainLayout({ children }: MainLayoutProps) {
  return (
    <div className="flex flex-col h-screen">
      <Header />
      <div className="flex-1 overflow-hidden">
        <main className="h-full overflow-y-auto bg-[hsl(var(--background))] p-4 md:p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
