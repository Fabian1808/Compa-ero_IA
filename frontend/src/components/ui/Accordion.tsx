import React from 'react';
export function Accordion({ children, ...props }: any) { return <div {...props}>{children}</div>; }
export function AccordionItem({ children, value, ...props }: any) { return <div className="border-b" {...props}>{children}</div>; }
export function AccordionTrigger({ children, ...props }: any) { return <button className="w-full text-left py-4" {...props}>{children}</button>; }
export function AccordionContent({ children, ...props }: any) { return <div className="py-2" {...props}>{children}</div>; }
