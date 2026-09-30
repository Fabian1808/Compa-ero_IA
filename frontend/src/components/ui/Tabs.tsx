import React from 'react';
export function Tabs({ children, ...props }: any) { return <div {...props}>{children}</div>; }
export function TabsList({ children, ...props }: any) { return <div className="flex space-x-2 border-b" {...props}>{children}</div>; }
export function TabsTrigger({ children, value, ...props }: any) { return <button className="px-4 py-2" {...props}>{children}</button>; }
export function TabsContent({ children, value, ...props }: any) { return <div {...props}>{children}</div>; }
